"""
Main DLT Pipeline

Orchestrates the full Bronze → Silver → Gold flow.
"""

import dlt
import duckdb
import json
from pathlib import Path
from datetime import datetime
import yaml
from sources import WarehouseSource, LogisticsSource
from transformations import normalize_to_events, aggregate_events_to_facts
from transformations.semantic_resolver import SemanticConflictResolver


# Database path - centralized for consistency
DB_PATH = "./data/processed/aura.duckdb"


def load_config() -> dict:
    """Load source configuration from YAML"""
    config_path = Path(__file__).parent / "config" / "sources.yaml"
    with open(config_path) as f:
        return yaml.safe_load(f)


def run_bronze_layer():
    """
    Bronze Layer: Ingest raw data from all sources
    
    Steps:
    1. Load config
    2. Initialize sources (WarehouseSource, LogisticsSource)
    3. Create DLT pipeline
    4. Run ingestion
    """
    print("🔶 Running Bronze Layer: Raw Ingestion...")
    
    config = load_config()
    
    # Initialize sources
    warehouse_config = config["sources"]["warehouse_stock"]
    logistics_config = config["sources"]["logistics_shipments"]
    
    warehouse_source = WarehouseSource(
        csv_path=warehouse_config["path"],
        reliability_score=warehouse_config["reliability_score"]
    )
    
    logistics_source = LogisticsSource(
        api_endpoint=logistics_config["endpoint"],
        fx_rate_endpoint="http://localhost:8000/api/fx/usd-zar",
        reliability_score=logistics_config["reliability_score"]
    )
    
    # Create DLT resources as standalone functions (works better with DLT)
    @dlt.resource(name="warehouse_stock", write_disposition="replace")
    def warehouse_data():
        for record in warehouse_source.load_raw_data():
            yield {
                **record,
                "_source_system": warehouse_source.name,
                "_source_type": warehouse_source.source_type,
                "_reliability_score": warehouse_source.reliability_score,
                "_ingested_at": datetime.now().isoformat(),
            }
    
    @dlt.resource(name="logistics_shipments", write_disposition="replace")
    def logistics_data():
        for record in logistics_source.load_raw_data():
            yield {
                **record,
                "_source_system": logistics_source.name,
                "_source_type": logistics_source.source_type,
                "_reliability_score": logistics_source.reliability_score,
                "_ingested_at": datetime.now().isoformat(),
            }
    
    # Create DLT pipeline with explicit database path
    pipeline = dlt.pipeline(
        pipeline_name="aura_bronze",
        destination=dlt.destinations.duckdb(DB_PATH),
        dataset_name="bronze",
        dev_mode=False
    )
    
    # Run ingestion with replace mode to avoid duplicates
    info = pipeline.run([warehouse_data(), logistics_data()])
    
    print(f"✅ Bronze layer complete. Loaded data to {DB_PATH}")
    return pipeline


def run_silver_layer(bronze_pipeline):
    """
    Silver Layer: Normalize into event stream
    
    Steps:
    1. Read from Bronze tables
    2. Apply normalize_to_events transformation
    3. Write to Silver schema
    """
    print("⚪ Running Silver Layer: Event Normalization...")
    
    # Connect to DuckDB and read Bronze data
    conn = duckdb.connect(DB_PATH)
    
    try:
        # Create silver schema if not exists
        conn.execute("CREATE SCHEMA IF NOT EXISTS silver")
        
        # Clear existing silver data to avoid duplicates
        try:
            conn.execute("DROP TABLE IF EXISTS silver.inventory_events")
        except:
            pass
        
        # Read warehouse data from bronze
        warehouse_data = []
        try:
            warehouse_df = conn.execute("""
                SELECT * FROM bronze.warehouse_stock 
                ORDER BY _ingested_at DESC
            """).fetchdf()
            warehouse_data = warehouse_df.to_dict('records')
            print(f"   📦 Read {len(warehouse_data)} warehouse records from Bronze")
        except Exception as e:
            print(f"   ⚠️  No warehouse data in Bronze: {e}")
        
        # Read logistics data from bronze
        logistics_data = []
        try:
            logistics_df = conn.execute("""
                SELECT * FROM bronze.logistics_shipments
                ORDER BY _ingested_at DESC
            """).fetchdf()
            logistics_data = logistics_df.to_dict('records')
            print(f"   🚚 Read {len(logistics_data)} logistics records from Bronze")
        except Exception as e:
            print(f"   ⚠️  No logistics data in Bronze: {e}")
        
        # Combine all bronze data
        all_bronze_data = warehouse_data + logistics_data
        
        if not all_bronze_data:
            print("   ❌ No data to process in Silver layer")
            return None
        
        # Apply normalization transformation
        silver_events = normalize_to_events(all_bronze_data)
        
        # Create silver table and insert data
        conn.execute("""
            CREATE TABLE IF NOT EXISTS silver.inventory_events (
                event_id VARCHAR PRIMARY KEY,
                event_type VARCHAR,
                part_id VARCHAR,
                part_name VARCHAR,
                quantity INTEGER,
                quantity_semantic VARCHAR,
                unit_cost_zar DOUBLE,
                event_timestamp TIMESTAMP,
                ingestion_timestamp TIMESTAMP,
                is_late_arrival BOOLEAN,
                lateness_hours DOUBLE,
                source_system VARCHAR,
                source_type VARCHAR,
                reliability_score DOUBLE,
                warehouse_location VARCHAR,
                supplier VARCHAR,
                estimated_arrival VARCHAR,
                status VARCHAR,
                _inserted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Insert silver events
        for event in silver_events:
            conn.execute("""
                INSERT OR REPLACE INTO silver.inventory_events (
                    event_id, event_type, part_id, part_name, quantity, quantity_semantic,
                    unit_cost_zar, event_timestamp, ingestion_timestamp,
                    is_late_arrival, lateness_hours, source_system, source_type,
                    reliability_score, warehouse_location, supplier, estimated_arrival, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                event.get('event_id'),
                event.get('event_type'),
                event.get('part_id'),
                event.get('part_name'),
                event.get('quantity'),
                event.get('quantity_semantic'),
                event.get('unit_cost_zar'),
                event.get('event_timestamp'),
                event.get('ingestion_timestamp'),
                event.get('is_late_arrival', False),
                event.get('lateness_hours', 0),
                event.get('source_system'),
                event.get('source_type'),
                event.get('reliability_score'),
                event.get('warehouse_location'),
                event.get('supplier'),
                event.get('estimated_arrival'),
                event.get('status')
            ])
        
        conn.commit()
        print(f"✅ Silver layer complete. Processed {len(silver_events)} events")
        
        return silver_events
        
    finally:
        conn.close()


def run_gold_layer(silver_events=None):
    """
    Gold Layer: Aggregate events into facts
    
    Steps:
    1. Read from Silver event stream
    2. Apply aggregate_events_to_facts transformation
    3. Write to Gold schema
    """
    print("🟡 Running Gold Layer: Fact Aggregation...")
    
    conn = duckdb.connect(DB_PATH)
    
    try:
        # Create gold schema if not exists
        conn.execute("CREATE SCHEMA IF NOT EXISTS gold")
        
        # Clear existing gold data to avoid duplicates
        try:
            conn.execute("DROP TABLE IF EXISTS gold.inventory_facts")
        except:
            pass
        
        # Read silver events if not passed
        if silver_events is None:
            try:
                silver_df = conn.execute("""
                    SELECT * FROM silver.inventory_events
                    ORDER BY event_timestamp DESC
                """).fetchdf()
                silver_events = silver_df.to_dict('records')
                print(f"   📊 Read {len(silver_events)} events from Silver")
            except Exception as e:
                print(f"   ❌ Error reading Silver layer: {e}")
                return None
        
        if not silver_events:
            print("   ❌ No events to aggregate")
            return None
        
        # Group events by part_id and resolve conflicts
        resolver = SemanticConflictResolver()
        events_by_part = {}
        part_names = {}
        
        for event in silver_events:
            part_id = event.get('part_id')
            if not part_id:
                continue
                
            if part_id not in events_by_part:
                events_by_part[part_id] = {"warehouse": [], "logistics": []}
            
            source = event.get('source_system', '')
            if source == 'warehouse_stock':
                events_by_part[part_id]["warehouse"].append(event)
                # Extract part_name from warehouse records
                if event.get('part_name'):
                    part_names[part_id] = event['part_name']
            elif source == 'logistics_shipments':
                events_by_part[part_id]["logistics"].append(event)
        
        # Create gold table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS gold.inventory_facts (
                part_id VARCHAR PRIMARY KEY,
                part_name VARCHAR,
                qty_on_shelf INTEGER,
                in_transit_qty INTEGER,
                shadow_stock_qty INTEGER,
                effective_inventory INTEGER,
                data_reliability_index DOUBLE,
                semantic_context VARCHAR,
                has_inconsistency BOOLEAN,
                confidence_level VARCHAR,
                reorder_recommendation JSON,
                fact_valid_from TIMESTAMP,
                fact_valid_to TIMESTAMP,
                shelf_last_updated VARCHAR,
                _updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Generate facts for each part
        facts_created = 0
        for part_id, events in events_by_part.items():
            # Use semantic resolver to create unified view
            unified = resolver.resolve_inventory(
                events["warehouse"],
                events["logistics"]
            )
            
            # Get part name
            part_name = part_names.get(part_id, f"Part {part_id}")
            
            # Calculate reorder recommendation
            reorder_rec = _calculate_reorder_recommendation(
                unified["effective_inventory"],
                unified["has_inconsistency"]
            )
            
            # Assess confidence level
            confidence = _assess_confidence(unified)
            
            # Insert/update fact
            conn.execute("""
                INSERT OR REPLACE INTO gold.inventory_facts (
                    part_id, part_name, qty_on_shelf, in_transit_qty, shadow_stock_qty,
                    effective_inventory, data_reliability_index, semantic_context,
                    has_inconsistency, confidence_level, reorder_recommendation,
                    fact_valid_from, fact_valid_to, shelf_last_updated
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                part_id,
                part_name,
                unified["qty_on_shelf"],
                unified["in_transit_qty"],
                unified.get("shadow_stock_qty", 0),
                unified["effective_inventory"],
                unified["data_reliability_index"],
                unified["semantic_context"],
                unified["has_inconsistency"],
                confidence,
                json.dumps(reorder_rec),
                datetime.now().isoformat(),
                None,  # fact_valid_to = NULL means currently valid
                unified["shelf_last_updated"]
            ])
            facts_created += 1
        
        conn.commit()
        print(f"✅ Gold layer complete. Created {facts_created} facts")
        
        return facts_created
        
    finally:
        conn.close()


def _calculate_reorder_recommendation(effective_inventory: int, has_inconsistency: bool) -> dict:
    """
    Simple rule-based reorder logic.
    
    Rules:
    - If inventory < 30: URGENT reorder
    - If inventory < 50: RECOMMEND reorder
    - If inventory >= 50: NO ACTION
    - If inconsistency detected: MANUAL REVIEW
    """
    if has_inconsistency:
        return {
            "should_reorder": None,
            "urgency": "manual_review",
            "reasoning": "Data inconsistency detected - requires human verification"
        }
    
    if effective_inventory < 30:
        return {
            "should_reorder": True,
            "urgency": "urgent",
            "reasoning": f"Critical stock level ({effective_inventory} units) - immediate reorder recommended"
        }
    elif effective_inventory < 50:
        return {
            "should_reorder": True,
            "urgency": "recommended",
            "reasoning": f"Below optimal level ({effective_inventory} units) - consider reordering"
        }
    else:
        return {
            "should_reorder": False,
            "urgency": "none",
            "reasoning": f"Adequate stock ({effective_inventory} units) - no action needed"
        }


def _assess_confidence(unified_inventory: dict) -> str:
    """
    Assigns confidence level based on reliability and consistency.
    
    Levels:
    - high: reliability > 0.85, no inconsistencies
    - medium: reliability 0.6-0.85, no inconsistencies
    - low: reliability < 0.6 OR inconsistencies detected
    """
    reliability = unified_inventory.get("data_reliability_index", 0)
    has_issue = unified_inventory.get("has_inconsistency", False)
    
    if has_issue or reliability < 0.6:
        return "low"
    elif reliability >= 0.85:
        return "high"
    else:
        return "medium"


def run_full_pipeline():
    """Execute complete Bronze → Silver → Gold pipeline"""
    print("=" * 60)
    print("🚀 AURA KNOWLEDGE PIPELINE - Full Execution")
    print("=" * 60)
    
    # Run layers sequentially
    bronze_pipeline = run_bronze_layer()
    silver_events = run_silver_layer(bronze_pipeline)
    gold_facts = run_gold_layer(silver_events)
    
    print("=" * 60)
    print("✅ Pipeline execution complete!")
    print(f"   Database: {DB_PATH}")
    print("=" * 60)
    
    return {
        "bronze": bronze_pipeline,
        "silver_events": len(silver_events) if silver_events else 0,
        "gold_facts": gold_facts
    }


if __name__ == "__main__":
    run_full_pipeline()
