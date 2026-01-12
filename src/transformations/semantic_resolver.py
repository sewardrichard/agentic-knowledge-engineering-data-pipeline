"""
Semantic Conflict Resolution

The core knowledge engineering challenge: "quantity" means different things
in different sources. This module resolves those conflicts.
"""

from typing import Dict, List, Any
from datetime import datetime, timedelta


class SemanticConflictResolver:
    """
    Resolves semantic conflicts between data sources.
    
    Primary Conflict: "What does 'quantity' mean?"
    - Warehouse CSV: quantity = physical units on shelf
    - Logistics API: quantity = units in-transit
    
    Goal: Create unified "effective_inventory" that Aura can trust
    """
    
    def __init__(self, shadow_stock_threshold_hours: int = 6):
        """
        Args:
            shadow_stock_threshold_hours: If shipment marked "delivered"
                but warehouse hasn't updated within this many hours,
                flag as potential shadow stock
        """
        self.shadow_stock_threshold = timedelta(hours=shadow_stock_threshold_hours)
    
    def resolve_inventory(
        self,
        warehouse_records: List[Dict[str, Any]],
        logistics_records: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Creates unified inventory view for a single part.
        
        Steps:
        1. Extract qty_on_shelf from warehouse records
        2. Sum in_transit quantities from logistics (where status='in_transit')
        3. Calculate effective_inventory = on_shelf + in_transit
        4. Detect shadow stock (delivered shipments not yet in warehouse count)
        5. Compute weighted reliability score
        6. Generate semantic context for Aura
        
        Args:
            warehouse_records: All warehouse/silver events for this part (source_system='warehouse_stock')
            logistics_records: All logistics/silver events for this part (source_system='logistics_shipments')
        
        Returns:
            Unified inventory fact with metadata
        """
        # Extract latest warehouse data
        # Handle both raw records and silver events (different field names)
        if not warehouse_records:
            warehouse_qty = 0
            warehouse_timestamp = None
            warehouse_reliability = 0.0
        else:
            # Find latest warehouse record by timestamp
            def get_timestamp(r):
                ts = r.get('event_timestamp') or r.get('last_updated') or ''
                if isinstance(ts, str):
                    return ts
                return str(ts)
            
            latest_warehouse = max(warehouse_records, key=get_timestamp)
            warehouse_qty = latest_warehouse.get('quantity', 0)
            
            # Parse timestamp
            ts_str = get_timestamp(latest_warehouse)
            try:
                if ts_str:
                    warehouse_timestamp = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                else:
                    warehouse_timestamp = None
            except:
                warehouse_timestamp = None
            
            # Get reliability score (handle both field names)
            warehouse_reliability = latest_warehouse.get('reliability_score') or latest_warehouse.get('_reliability_score', 0.7)
        
        # Calculate in-transit quantity (ONLY items with status='in_transit')
        # EXCLUDE delivered items even if shadow stock is detected
        in_transit_qty = sum([
            r.get('quantity', 0) 
            for r in logistics_records 
            if r.get('status') == 'in_transit' and r.get('status') != 'delivered'
        ])
        
        # Calculate delivered but not shelved (shadow stock quantity)
        # These are items marked as delivered in logistics but not yet in warehouse count
        shadow_qty = sum([
            r.get('quantity', 0)
            for r in logistics_records
            if r.get('status') == 'delivered'
        ])
        
        # Detect shadow stock
        has_shadow = self._detect_shadow_stock(
            warehouse_records, 
            logistics_records,
            warehouse_timestamp
        )
        
        # Compute weighted reliability
        total_qty = warehouse_qty + in_transit_qty
        if total_qty > 0:
            logistics_reliability = 0.9  # Logistics has 0.9 reliability
            reliability_score = (
                (warehouse_qty * warehouse_reliability) + 
                (in_transit_qty * logistics_reliability)
            ) / total_qty
        else:
            reliability_score = warehouse_reliability if warehouse_reliability > 0 else 0.5
        
        # Note: Shadow stock detection is a FEATURE, not a failure
        # We don't penalize reliability for detecting it correctly
        # Instead, we flag it as an inconsistency for manual review
        
        return {
            "qty_on_shelf": warehouse_qty,
            "in_transit_qty": in_transit_qty,
            "shadow_stock_qty": shadow_qty if has_shadow else 0,
            "effective_inventory": warehouse_qty + in_transit_qty,  # Don't count shadow stock in effective inventory
            "has_inconsistency": has_shadow,
            "data_reliability_index": round(reliability_score, 3),
            "semantic_context": self._generate_context(
                warehouse_qty, 
                in_transit_qty,
                shadow_qty if has_shadow else 0,
                has_shadow
            ),
            "shelf_last_updated": warehouse_timestamp.isoformat() if warehouse_timestamp else None,
        }
    
    def _detect_shadow_stock(
        self,
        warehouse_records: List[Dict[str, Any]],
        logistics_records: List[Dict[str, Any]],
        warehouse_timestamp: datetime
    ) -> bool:
        """
        Detects "shadow stock" - inventory that's been delivered but not scanned in.
        
        Logic:
        1. Find all logistics records with status='delivered'
        2. Check if delivery timestamp is recent (within threshold)
        3. If delivered >N hours ago but warehouse hasn't updated, flag as shadow
        
        This is critical for preventing Aura from over-ordering!
        """
        if not warehouse_timestamp:
            # No warehouse data means we can't detect shadow stock
            return False
        
        # Find delivered shipments (check both event_type and status fields)
        delivered = [
            r for r in logistics_records 
            if r.get('status') == 'delivered' or r.get('event_type') == 'goods_receipt'
        ]
        
        if not delivered:
            return False
        
        # Check if any delivered shipment hasn't been reflected in warehouse count
        for shipment in delivered:
            # Get delivery timestamp (handle both field names)
            ts_str = shipment.get('event_timestamp') or shipment.get('last_updated')
            if not ts_str:
                continue
                
            try:
                if isinstance(ts_str, str):
                    delivery_time = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                else:
                    delivery_time = ts_str
                
                # Make both timestamps timezone-naive for comparison
                if delivery_time.tzinfo is not None:
                    delivery_time = delivery_time.replace(tzinfo=None)
                if warehouse_timestamp.tzinfo is not None:
                    warehouse_timestamp_naive = warehouse_timestamp.replace(tzinfo=None)
                else:
                    warehouse_timestamp_naive = warehouse_timestamp
                
                # If warehouse update is BEFORE delivery, that's shadow stock
                # (delivered items not yet counted in warehouse)
                if warehouse_timestamp_naive < delivery_time:
                    return True
                
                # Also check if delivery was recent but warehouse is stale
                time_since_delivery = datetime.now() - delivery_time
                if time_since_delivery < self.shadow_stock_threshold:
                    # Recent delivery - check if warehouse updated after
                    time_gap = warehouse_timestamp_naive - delivery_time
                    if time_gap < timedelta(0):  # Warehouse update is before delivery
                        return True
                        
            except Exception as e:
                # If we can't parse timestamps, be conservative
                continue
        
        return False
    
    def _generate_context(
        self, 
        on_shelf: int, 
        in_transit: int,
        shadow_qty: int,
        has_shadow: bool
    ) -> str:
        """
        Generates human-readable context for Aura to understand the data.
        
        This helps Aura explain its reasoning to humans.
        """
        if has_shadow and shadow_qty > 0:
            base = f"Inventory includes {on_shelf} confirmed on-shelf units"
            if in_transit > 0:
                base += f" and {in_transit} units in-transit"
            base += f". WARNING: {shadow_qty} units marked as DELIVERED but NOT yet counted in warehouse stock (shadow stock)"
            return base
        elif in_transit > 0:
            return (
                f"Inventory includes {on_shelf} confirmed on-shelf units and "
                f"{in_transit} units currently in-transit (expected within 48 hours)."
            )
        else:
            return f"Inventory reflects {on_shelf} confirmed on-shelf units only."
