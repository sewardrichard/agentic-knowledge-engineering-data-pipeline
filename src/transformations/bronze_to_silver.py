"""
Bronze → Silver Transformation

Takes raw ingested data and normalizes it into a clean event stream.

Goals:
1. Standardize schemas across sources
2. Normalize timestamps (all UTC)
3. Convert currencies (all ZAR)
4. Create unified event log
5. Detect late-arriving data
"""

import dlt
from typing import List, Dict, Any
from datetime import datetime, timezone


def normalize_to_events(bronze_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Transforms Bronze layer into normalized Silver event stream.
    
    TODO: Implement normalization logic
    
    For each bronze record:
    1. Standardize timestamp format (ISO 8601 UTC)
    2. Ensure all costs in ZAR
    3. Create event_type classification
    4. Add temporal metadata (event_time vs ingestion_time)
    5. Detect late arrivals
    
    Returns:
        List of normalized event dictionaries
    """
    normalized_events = []
    
    for record in bronze_data:
        # Determine event type based on source and status
        event_type = _classify_event(record)
        
        # Parse timestamp - handle both string and datetime objects from DuckDB
        last_updated = record.get('last_updated')
        if isinstance(last_updated, datetime):
            event_timestamp = last_updated
        elif isinstance(last_updated, str):
            event_timestamp = _parse_timestamp(last_updated)
        else:
            event_timestamp = datetime.now(timezone.utc)
        
        # Handle ingestion timestamp (might already be datetime object from DuckDB)
        ingestion_ts = record['_ingested_at']
        if isinstance(ingestion_ts, str):
            ingestion_timestamp = datetime.fromisoformat(ingestion_ts)
        else:
            ingestion_timestamp = ingestion_ts
        
        # Check if late-arriving
        lateness = (ingestion_timestamp - event_timestamp).total_seconds() / 3600
        is_late = lateness > 12  # More than 12 hours late
        
        normalized = {
            # Identity
            "event_id": _generate_event_id(record),
            "event_type": event_type,
            
            # Business data
            "part_id": record["part_id"],
            "quantity": record["quantity"],
            "quantity_semantic": record.get("quantity_semantic", "unknown"),
            "unit_cost_zar": record["unit_cost_zar"],
            
            # Temporal
            "event_timestamp": event_timestamp.isoformat(),
            "ingestion_timestamp": ingestion_timestamp.isoformat(),
            "is_late_arrival": is_late,
            "lateness_hours": round(lateness, 2) if is_late else 0,
            
            # Source metadata
            "source_system": record["_source_system"],
            "source_type": record["_source_type"],
            "reliability_score": record["_reliability_score"],
            
            # Additional context
            **_extract_additional_context(record)
        }
        
        normalized_events.append(normalized)
    
    return normalized_events


def _classify_event(record: Dict[str, Any]) -> str:
    """
    Classifies the type of inventory event.
    
    Event Types:
    - stock_count: Warehouse physical count
    - shipment_dispatch: Supplier sends items
    - shipment_in_transit: Items on the road
    - goods_receipt: Items arrive at warehouse
    """
    source = record.get("_source_system", "")
    status = record.get("status", "")
    
    if source == "warehouse_stock":
        return "stock_count"
    elif source == "logistics_shipments":
        if status == "in_transit":
            return "shipment_in_transit"
        elif status == "delivered":
            return "goods_receipt"
        else:
            return "shipment_dispatch"
    
    return "unknown"


def _parse_timestamp(timestamp_str: str) -> datetime:
    """Safely parse various timestamp formats to UTC datetime"""
    if not timestamp_str:
        return datetime.now(timezone.utc)
    
    try:
        # Handle ISO format with Z or +00:00
        dt = datetime.fromisoformat(str(timestamp_str).replace('Z', '+00:00'))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception as e:
        # If parsing fails, return current time as fallback
        print(f"Warning: Failed to parse timestamp '{timestamp_str}': {e}. Using current time.")
        return datetime.now(timezone.utc)


def _generate_event_id(record: Dict[str, Any]) -> str:
    """Generate unique event ID"""
    # TODO: Improve this to use actual unique identifiers
    source = record.get("_source_system", "unknown")
    part = record.get("part_id", "unknown")
    timestamp = record.get("_ingested_at", "")
    return f"{source}_{part}_{timestamp}"[:50]


def _extract_additional_context(record: Dict[str, Any]) -> Dict[str, Any]:
    """Extract source-specific additional fields"""
    context = {}
    
    # Part name (from warehouse records)
    if "part_name" in record:
        context["part_name"] = record["part_name"]
    
    # Warehouse-specific
    if "warehouse_location" in record:
        context["warehouse_location"] = record["warehouse_location"]
    
    # Logistics-specific
    if "supplier" in record:
        context["supplier"] = record["supplier"]
    if "estimated_arrival" in record:
        context["estimated_arrival"] = record["estimated_arrival"]
    if "status" in record:
        context["status"] = record["status"]
    
    return context
