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
        
        TODO: Implement this critical function
        
        Steps:
        1. Extract qty_on_shelf from warehouse records
        2. Sum in_transit quantities from logistics (where status='in_transit')
        3. Calculate effective_inventory = on_shelf + in_transit
        4. Detect shadow stock (delivered shipments not yet in warehouse count)
        5. Compute weighted reliability score
        6. Generate semantic context for Aura
        
        Args:
            warehouse_records: All warehouse records for this part
            logistics_records: All logistics records for this part
        
        Returns:
            Unified inventory fact with metadata
        """
        # TODO: Implement logic
        # This is where your knowledge engineering skills shine!
        
        # Extract latest warehouse data
        if not warehouse_records:
            warehouse_qty = 0
            warehouse_timestamp = None
            warehouse_reliability = 0.0
        else:
            latest_warehouse = max(warehouse_records, key=lambda x: x['last_updated'])
            warehouse_qty = latest_warehouse['quantity']
            warehouse_timestamp = datetime.fromisoformat(latest_warehouse['last_updated'])
            warehouse_reliability = latest_warehouse['_reliability_score']
        
        # Calculate in-transit quantity
        in_transit_qty = sum([
            r['quantity'] 
            for r in logistics_records 
            if r.get('status') == 'in_transit'
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
            reliability_score = (
                (warehouse_qty * warehouse_reliability) + 
                (in_transit_qty * 0.9)  # Logistics has 0.9 reliability
            ) / total_qty
        else:
            reliability_score = min(warehouse_reliability, 0.9)
        
        return {
            "qty_on_shelf": warehouse_qty,
            "in_transit_qty": in_transit_qty,
            "effective_inventory": warehouse_qty + in_transit_qty,
            "has_inconsistency": has_shadow,
            "data_reliability_index": round(reliability_score, 3),
            "semantic_context": self._generate_context(
                warehouse_qty, 
                in_transit_qty, 
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
        
        TODO: Implement shadow stock detection logic
        
        Logic:
        1. Find all logistics records with status='delivered'
        2. Check if delivery timestamp is recent (within threshold)
        3. If delivered >N hours ago but warehouse hasn't updated, flag as shadow
        
        This is critical for preventing Aura from over-ordering!
        """
        if not warehouse_timestamp:
            return False
        
        # Find delivered shipments
        delivered = [r for r in logistics_records if r.get('status') == 'delivered']
        
        if not delivered:
            return False
        
        # Check if any delivered shipment hasn't been reflected in warehouse count
        for shipment in delivered:
            delivery_time = datetime.fromisoformat(shipment['last_updated'])
            time_gap = warehouse_timestamp - delivery_time
            
            # If delivered but warehouse update is old, might be shadow stock
            if time_gap > self.shadow_stock_threshold:
                return True
        
        return False
    
    def _generate_context(
        self, 
        on_shelf: int, 
        in_transit: int, 
        has_shadow: bool
    ) -> str:
        """
        Generates human-readable context for Aura to understand the data.
        
        This helps Aura explain its reasoning to humans.
        """
        if has_shadow:
            return (
                f"Inventory includes {on_shelf} confirmed on-shelf units and "
                f"{in_transit} in-transit units. WARNING: Possible shadow stock detected - "
                f"recent deliveries may not be reflected in warehouse count."
            )
        elif in_transit > 0:
            return (
                f"Inventory includes {on_shelf} confirmed on-shelf units and "
                f"{in_transit} units currently in-transit (expected within 48 hours)."
            )
        else:
            return f"Inventory reflects {on_shelf} confirmed on-shelf units only."
