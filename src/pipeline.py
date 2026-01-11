"""
Main DLT Pipeline

Orchestrates the full Bronze → Silver → Gold flow.
"""

import dlt
from pathlib import Path
import yaml
from sources import WarehouseSource, LogisticsSource
from transformations import normalize_to_events, aggregate_events_to_facts


def load_config() -> dict:
    """Load source configuration from YAML"""
    config_path = Path(__file__).parent / "config" / "sources.yaml"
    with open(config_path) as f:
        return yaml.safe_load(f)


def run_bronze_layer():
    """
    Bronze Layer: Ingest raw data from all sources
    
    TODO: Complete this function
    
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
    
    # Create DLT pipeline
    pipeline = dlt.pipeline(
        pipeline_name="aura_bronze",
        destination="duckdb",
        dataset_name="bronze",
        dev_mode=False  # Set to False for production
    )
    
    # Run ingestion
    info = pipeline.run(
        [
            warehouse_source.to_dlt_resource().with_name("warehouse_stock"),
            logistics_source.to_dlt_resource().with_name("logistics_shipments")
        ],
        write_disposition="append"
    )
    
    print(f"✅ Bronze layer complete. Loaded {info.metrics['rows']} rows")
    return pipeline


def run_silver_layer(bronze_pipeline):
    """
    Silver Layer: Normalize into event stream
    
    TODO: Implement Silver transformation
    
    Steps:
    1. Read from Bronze tables
    2. Apply normalize_to_events transformation
    3. Write to Silver schema
    """
    print("⚪ Running Silver Layer: Event Normalization...")
    
    # TODO: Implement this
    # Hint: You'll need to:
    # 1. Query bronze tables
    # 2. Pass data through normalize_to_events()
    # 3. Write to silver.inventory_events table
    
    pass


def run_gold_layer(silver_pipeline):
    """
    Gold Layer: Aggregate events into facts
    
    TODO: Implement Gold transformation
    
    Steps:
    1. Read from Silver event stream
    2. Apply aggregate_events_to_facts transformation
    3. Write to Gold schema
    """
    print("🟡 Running Gold Layer: Fact Aggregation...")
    
    # TODO: Implement this
    # Hint: You'll need to:
    # 1. Query silver.inventory_events
    # 2. Pass data through aggregate_events_to_facts()
    # 3. Write to gold.inventory_facts table
    
    pass


def run_full_pipeline():
    """Execute complete Bronze → Silver → Gold pipeline"""
    print("=" * 60)
    print("🚀 AURA KNOWLEDGE PIPELINE - Full Execution")
    print("=" * 60)
    
    # Run layers sequentially
    bronze_pipeline = run_bronze_layer()
    # silver_pipeline = run_silver_layer(bronze_pipeline)
    # gold_pipeline = run_gold_layer(silver_pipeline)
    
    print("=" * 60)
    print("✅ Pipeline execution complete!")
    print("=" * 60)


if __name__ == "__main__":
    run_full_pipeline()
