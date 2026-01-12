# Aura Knowledge Pipeline - Architecture Diagrams

This document contains comprehensive architecture and data flow diagrams for the Aura Knowledge Pipeline project. All diagrams are written in Mermaid.js for easy visualization and maintenance.

## 📊 Viewing the Diagrams

You can view these diagrams in several ways:

1. **GitHub** - Diagrams render automatically in GitHub's markdown viewer
2. **Mermaid Live Editor** - Copy any diagram to [mermaid.live](https://mermaid.live/) for interactive editing
3. **VS Code** - Use the Mermaid Preview extension
4. **Documentation Sites** - Most static site generators support Mermaid (GitBook, Docusaurus, MkDocs)

## 🏗️ Architecture Overview

The Aura Knowledge Pipeline implements a medallion architecture (Bronze → Silver → Gold) for inventory data processing, with built-in support for:

- **Bitemporal data tracking** (business time vs. system time)
- **Semantic conflict resolution** between data sources
- **Shadow stock detection** for delivered goods not yet reflected in warehouse counts
- **Agent safety layer** for AI query validation and consistency checks

---

## Diagram 01: System Architecture Overview

High-level view of the entire system, showing data sources, pipeline orchestration, storage layers, and agent consumption.

```mermaid
graph TD
  subgraph Sources[Data Sources]
    CSV["Warehouse CSV file
    data/raw/warehouse_stock.csv"]
  end

  subgraph Mock[Mock API Server]
    FastAPI["FastAPI app
    mock_apis/main.py"]
    Shipments["GET /api/shipments/active"]
    FxRate["GET /api/fx/usd-zar"]
  end

  subgraph Orchestration[Pipeline Orchestration]
    Runner["CLI runner
    scripts/run_pipeline.py"]
    Pipeline["src/pipeline.py
    run_full_pipeline()"]
    WS["src/sources/warehouse_source.py
    WarehouseSource"]
    LS["src/sources/logistics_source.py
    LogisticsSource"]
  end

  subgraph Storage[DuckDB]
    DB[("data/processed/aura.duckdb")]
    Bronze[("bronze.*")]
    Silver[("silver.inventory_events")]
    Gold[("gold.inventory_facts")]
  end

  subgraph Agent[Agent Consumption]
    Aura["Aura client"]
    Query["agent/query_interface.py
    AuraQueryInterface"]
    Safety["agent/safety_layer.py
    AuraAgentSafetyLayer"]
  end

  Runner --> Pipeline

  Pipeline --> WS
  WS --> CSV

  Pipeline --> LS
  LS --> Shipments
  LS --> FxRate
  FastAPI --> Shipments
  FastAPI --> FxRate

  Pipeline -->|DLT ingestion| Bronze
  Bronze --> DB
  Pipeline -->|normalize_to_events| Silver
  Silver --> DB
  Pipeline -->|SemanticConflictResolver| Gold
  Gold --> DB

  Aura --> Query
  Query --> Safety
  Safety -->|SELECT from gold.inventory_facts| Gold
```

**Key Components:**
- **Data Sources**: CSV files and REST APIs
- **Orchestration**: Python-based pipeline using DLT for ingestion
- **Storage**: DuckDB with medallion architecture
- **Agent Layer**: Safety-checked query interface for AI consumption

---

## Diagram 02: Data Flow (Medallion Architecture)

Detailed view of the Bronze → Silver → Gold transformation pipeline and the fields at each layer.

```mermaid
graph LR
  subgraph Bronze[Bronze: Raw ingestion DLT to DuckDB]
    B1["bronze.warehouse_stock
    fields: part_id, part_name, quantity,
    unit_cost_zar, last_updated, warehouse_location
    metadata: _source_system, _source_type,
    _reliability_score, _ingested_at"]
    B2["bronze.logistics_shipments
    fields: shipment_id, part_id, quantity,
    unit_cost_zar, status, estimated_arrival, last_updated
    metadata: _source_system, _source_type,
    _reliability_score, _ingested_at"]
  end

  subgraph Silver[Silver: Normalized event stream]
    S1["silver.inventory_events
    event_id, event_type, part_id, part_name,
    quantity, quantity_semantic, unit_cost_zar
    event_timestamp, ingestion_timestamp,
    is_late_arrival, lateness_hours, status"]
  end

  subgraph Gold[Gold: Agent-ready facts]
    G1["gold.inventory_facts
    qty_on_shelf, in_transit_qty,
    shadow_stock_qty, effective_inventory
    data_reliability_index, semantic_context,
    has_inconsistency, confidence_level
    reorder_recommendation, shelf_last_updated"]
  end

  N["transformations/bronze_to_silver.py
  normalize_to_events()"]
  R["transformations/semantic_resolver.py
  SemanticConflictResolver.resolve_inventory()"]
  RR["src/pipeline.py
  _calculate_reorder_recommendation()"]
  CF["src/pipeline.py
  _assess_confidence()"]

  B1 --> N
  B2 --> N
  N --> S1
  S1 --> R
  R --> G1
  RR --> G1
  CF --> G1
```

**Layer Responsibilities:**
- **Bronze**: Raw data ingestion with metadata tracking
- **Silver**: Event normalization with temporal tracking
- **Gold**: Unified facts with conflict resolution and business logic

---

## Diagram 03: Event-to-Fact Timeline (Bitemporal Tracking)

Illustrates how events are tracked with both business time (event_timestamp) and system time (ingestion_timestamp), including late arrival detection.

```mermaid
sequenceDiagram
  autonumber
  participant W as Warehouse CSV
  participant L as Logistics API
  participant P as Pipeline (Silver)
  participant S as silver.inventory_events
  participant G as gold.inventory_facts

  Note over W: event_timestamp = last_updated (business time)
  Note over P: ingestion_timestamp = _ingested_at (system time)

  W->>P: Stock count record
  P->>S: INSERT event_type=stock_count<br/>(event_timestamp, ingestion_timestamp)

  L->>P: Shipment status=in_transit
  P->>S: INSERT event_type=shipment_in_transit<br/>(event_timestamp, ingestion_timestamp)

  Note over P,S: Late arrival detection<br/>if (ingestion - event) > 12h then is_late_arrival=true

  P->>G: Recompute fact for part_id<br/>from all events in S
  Note over G: fact_valid_to is NULL for current snapshot
```

**Temporal Design:**
- **Business Time**: When the event actually occurred in the real world
- **System Time**: When the pipeline ingested the event
- **Late Arrival**: Flagged when ingestion lags business time by >12 hours

---

## Diagram 04: Semantic Conflict Resolution

Shows the implemented rules for resolving conflicts between warehouse and logistics data sources.

```mermaid
flowchart TD
  WH["Warehouse events
  (source_system=warehouse_stock)
  quantity_semantic=on_shelf"]
  
  LWH["Pick latest by timestamp
  qty_on_shelf = quantity
  warehouse_reliability = reliability_score"]
  
  LG["Logistics events
  (source_system=logistics_shipments)
  quantity_semantic=in_transit"]
  
  INTR["Sum quantity where status='in_transit'
  in_transit_qty"]
  
  DEL["Sum quantity where status='delivered'
  shadow_stock_qty candidate"]
  
  SH["Detect shadow stock
  (delivery timestamp after warehouse update)
  has_inconsistency"]
  
  EI["effective_inventory = 
  qty_on_shelf + in_transit_qty
  (excludes delivered/shadow stock)"]
  
  REL["Weighted reliability
  (warehouse_qty*warehouse_rel + 
  in_transit_qty*0.9)/(total_qty)"]
  
  OUT["Output unified fact fields
  shadow_stock_qty (only if has_inconsistency)
  semantic_context
  data_reliability_index"]

  WH --> LWH
  LG --> INTR
  LG --> DEL
  LWH --> SH
  DEL --> SH
  LWH --> EI
  INTR --> EI
  EI --> REL
  SH --> OUT
  REL --> OUT
```

**Resolution Logic:**
- **Warehouse**: Latest timestamp wins for on-shelf quantities
- **Logistics**: Sum in-transit shipments, detect delivered items
- **Shadow Stock**: Delivered goods arriving after last warehouse update
- **Effective Inventory**: Excludes shadow stock to prevent double-counting

---

## Diagram 05: Shadow Stock Detection Scenario

End-to-end flow showing how shadow stock is detected and handled by the safety layer.

```mermaid
sequenceDiagram
  autonumber
  participant L as Logistics API
  participant W as Warehouse CSV
  participant P as Pipeline (Gold)
  participant R as SemanticConflictResolver
  participant G as gold.inventory_facts
  participant A as AuraAgentSafetyLayer

  L->>P: Shipment status='delivered'<br/>(quantity=50, last_updated=T_delivery)
  W->>P: Stock count last_updated=T_warehouse<br/>(T_warehouse < T_delivery)
  P->>R: resolve_inventory(warehouse_events, logistics_events)
  R-->>P: has_inconsistency=true<br/>shadow_stock_qty=50<br/>effective_inventory excludes 50
  P->>G: INSERT OR REPLACE fact<br/>(has_inconsistency=true)
  A->>G: SELECT current fact
  A-->>A: Consistency check fails (shadow stock)
  A-->>A: Return WARNING with manual verification action
```

**Shadow Stock Problem:**
When logistics shows delivered goods but warehouse counts haven't been updated yet, creating a data inconsistency that could mislead inventory calculations.

**Solution:**
The system detects this scenario, flags it, and excludes shadow stock from effective inventory until warehouse updates confirm receipt.

---

## Diagram 06: Agent Query Sequence (Safety Checks)

Complete flow of an agent query through the safety layer with all validation checks.

```mermaid
sequenceDiagram
  autonumber
  participant Client as Aura client
  participant Q as AuraQueryInterface.ask()
  participant S as AuraAgentSafetyLayer.query_with_safety()
  participant DB as DuckDB (read-only)
  participant G as gold.inventory_facts

  Client->>Q: ask(part_id, question)
  Q->>S: query_with_safety(part_id, question)
  S->>DB: Connect read_only=True
  S->>G: SELECT ... WHERE part_id=? AND fact_valid_to IS NULL

  alt No fact found
    S-->>Client: BLOCKED (no data)
  else Fact found
    S-->>S: Check reliability >= 0.6
    alt Reliability below threshold
      S-->>Client: BLOCKED (refresh/verify)
    else Reliability ok
      S-->>S: Check has_inconsistency
      alt Inconsistency detected
        S-->>Client: WARNING (shadow stock)
      else No inconsistency
        S-->>S: Check freshness (shelf_last_updated within 24h)
        alt Stale
          S-->>Client: WARNING (stale)
        else Fresh
          S-->>Client: SAFE (data + reasoning)
        end
      end
    end
  end
```

**Safety Checks (in order):**
1. **Data Availability**: Is there a current fact for this part?
2. **Reliability**: Does the data meet minimum quality threshold (≥0.6)?
3. **Consistency**: Are there any detected inconsistencies (shadow stock)?
4. **Freshness**: Is the warehouse data recent (<24 hours old)?

---

## 🔧 Implementation Notes

### Current Architecture

The diagrams reflect the **implemented** system as of the latest commit:

- **Pipeline Orchestration**: `src/pipeline.py` with `run_full_pipeline()`
- **Bronze Layer**: DLT ingestion into `bronze.*` tables in DuckDB
- **Silver Layer**: `transformations.normalize_to_events()` creates `silver.inventory_events`
- **Gold Layer**: `SemanticConflictResolver` produces `gold.inventory_facts`
- **Agent Interface**: `AuraQueryInterface` + `AuraAgentSafetyLayer` for safe queries

### Database

All data stored in: `./data/processed/aura.duckdb`

### Key Files

```
src/
├── pipeline.py                    # Main orchestration
├── sources/
│   ├── warehouse_source.py       # CSV ingestion
│   └── logistics_source.py       # API ingestion
└── transformations/
    ├── bronze_to_silver.py       # Event normalization
    └── semantic_resolver.py      # Conflict resolution

agent/
├── query_interface.py            # AuraQueryInterface
└── safety_layer.py               # AuraAgentSafetyLayer

mock_apis/
└── main.py                       # FastAPI mock server
```

---

## 📸 Screenshots

For visual reference, screenshots of the system in action are available in `diagrams/screenshots/`:

- DuckDB table samples
- Pipeline execution logs  
- Agent query outputs
- Safety layer warnings

---

## 📚 Additional Resources

- [Mermaid Documentation](https://mermaid.js.org/)
- [DLT Documentation](https://dlthub.com/docs)
- [DuckDB Documentation](https://duckdb.org/docs/)

---
