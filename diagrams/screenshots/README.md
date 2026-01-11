# Aura Knowledge Pipeline - Diagrams

This folder contains all architecture and flow diagrams for the project.

## Required Diagrams (Create in Draw.io)

### 1. System Architecture Overview
**File:** `01_system_architecture.drawio`
**Purpose:** Show the complete system from data sources to Aura agent
**Components to include:**
- Data Sources (Warehouse CSV, Logistics API)
- Mock APIs
- DLT Pipeline (Bronze/Silver/Gold layers)
- DuckDB
- Agent Safety Layer
- Aura Agent interface

### 2. Data Flow Diagram (Medallion Architecture)
**File:** `02_data_flow_medallion.drawio`
**Purpose:** Visualize the Bronze → Silver → Gold transformations
**Show:**
- What data looks like at each layer
- Transformations applied
- Schema changes
- Data quality improvements

### 3. Event-to-Fact Timeline
**File:** `03_event_to_fact_timeline.drawio`
**Purpose:** Explain temporal modeling and event sourcing
**Include:**
- Timeline with 3-4 events
- How events aggregate into facts
- Fact versioning (valid_from, valid_to)
- Example: Monday shipment → Wednesday receipt

### 4. Semantic Conflict Resolution
**File:** `04_semantic_conflict_resolution.drawio`
**Purpose:** Show how "quantity" ambiguity is resolved
**Elements:**
- Source A: qty_on_shelf (physical)
- Source B: quantity_shipped (in-transit)
- Decision tree/logic
- Output: effective_inventory

### 5. Shadow Stock Detection Scenario
**File:** `05_shadow_stock_scenario.drawio`
**Purpose:** Visualize the failure mode and your solution
**Show:**
- Monday: Shipment dispatched
- Tuesday: Delivered but not scanned
- The gap where inventory appears to be zero
- How your pipeline detects and flags this

### 6. Agent Consumption Pattern (Bonus)
**File:** `06_agent_query_sequence.drawio`
**Purpose:** Sequence diagram of Aura making a query
**Flow:**
1. Aura asks: "Should I reorder drill bits?"
2. Safety layer checks
3. Query gold layer
4. Return with confidence + metadata

## Draw.io Tips
- Use consistent colors (e.g., Bronze=orange, Silver=gray, Gold=yellow)
- Add legends/keys
- Keep it clean and professional
- Export as PNG for README
- Save .drawio source files for editing

## Screenshot Requirements
Also capture screenshots showing:
- DuckDB tables with sample data
- Pipeline run logs
- Agent query outputs
- Safety layer warnings

Place screenshots in `diagrams/screenshots/` folder.