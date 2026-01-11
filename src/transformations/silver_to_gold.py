"""
Silver → Gold Transformation

Creates agent-ready "facts" from event stream.

This is where Events become Facts:
- Events: Individual occurrences (append-only log)
- Facts: Current state of truth (updated/versioned)
"""

import dlt
from typing import List, Dict, Any
from collections import defaultdict
from datetime import datetime
from .semantic_resolver import SemanticConflictResolver


@dlt.transformer(name="gold_inventory_facts", write_disposition="merge", primary_key="part_id")
def aggregate_events_to_facts(
    silver_events: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Aggregates event stream into current facts.
    
    TODO: Implement event-to-fact aggregation
    
    Process:
    1. Group events by part_id
    2. Separate warehouse events from logistics events
    3. Use SemanticConflictResolver to create unified view
    4. Calculate reorder recommendations
    5. Add temporal validity (fact_valid_from, fact_valid_to)
    
    Returns:
        List of fact records (one per part)
    """
    resolver = SemanticConflictResolver()
    
    # Group events by part_id
    events_by_part = defaultdict(lambda: {"warehouse": [], "logistics": []})
    
    for event in silver_events:
        part_id = event["part_id"]
        source = event["source_system"]
        
        if source == "warehouse_stock":
            events_by_part[part_id]["warehouse"].append(event)
        elif source == "logistics_shipments":
            events_by_part[part_id]["logistics"].append(event)
    
    # Create facts for each part
    facts = []
    for part_id, events in events_by_part.items():
        # Resolve semantic conflicts
        unified = resolver.resolve_inventory(
            events["warehouse"],
            events["logistics"]
        )
        
        # Get part name (from any record)
        part_name = "Unknown"
        if events["warehouse"]:
            # TODO: Extract part_name from warehouse records
            pass
        
        # Calculate reorder recommendation
        reorder_rec = _calculate_reorder_recommendation(
            unified["effective_inventory"],
            unified["has_inconsistency"]
        )
        
        # Create fact record
        fact = {
            "part_id": part_id,
            "part_name": part_name,
            
            # Inventory
            "qty_on_shelf": unified["qty_on_shelf"],
            "in_transit_qty": unified["in_transit_qty"],
            "effective_inventory": unified["effective_inventory"],
            
            # Metadata for Aura
            "data_reliability_index": unified["data_reliability_index"],
            "semantic_context": unified["semantic_context"],
            "has_inconsistency": unified["has_inconsistency"],
            "confidence_level": _assess_confidence(unified),
            
            # Reorder logic
            "reorder_recommendation": reorder_rec,
            
            # Temporal
            "fact_valid_from": datetime.now().isoformat(),
            "fact_valid_to": None,  # Currently valid
            "shelf_last_updated": unified["shelf_last_updated"],
        }
        
        facts.append(fact)
    
    return facts


def _calculate_reorder_recommendation(
    effective_inventory: int,
    has_inconsistency: bool
) -> Dict[str, Any]:
    """
    Simple rule-based reorder logic.
    
    TODO: Implement reorder rules
    
    Rules (simplified for demo):
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
            "reasoning": f"Critical stock level ({effective_inventory} units)"
        }
    elif effective_inventory < 50:
        return {
            "should_reorder": True,
            "urgency": "recommended",
            "reasoning": f"Below optimal level ({effective_inventory} units)"
        }
    else:
        return {
            "should_reorder": False,
            "urgency": "none",
            "reasoning": f"Adequate stock ({effective_inventory} units)"
        }


def _assess_confidence(unified_inventory: Dict[str, Any]) -> str:
    """
    Assigns confidence level based on reliability and consistency.
    
    Levels:
    - high: reliability > 0.85, no inconsistencies
    - medium: reliability 0.6-0.85, no inconsistencies
    - low: reliability < 0.6 OR inconsistencies detected
    """
    reliability = unified_inventory["data_reliability_index"]
    has_issue = unified_inventory["has_inconsistency"]
    
    if has_issue or reliability < 0.6:
        return "low"
    elif reliability >= 0.85:
        return "high"
    else:
        return "medium"