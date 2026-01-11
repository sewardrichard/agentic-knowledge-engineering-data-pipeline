"""
Simplified query interface for Aura.

This is what a client application would use to interact with Aura.
"""

from .safety_layer import AuraAgentSafetyLayer


class AuraQueryInterface:
    """
    High-level interface for querying Aura's knowledge base.
    """
    
    def __init__(self, db_path: str):
        self.safety_layer = AuraAgentSafetyLayer(db_path)
    
    def ask(self, part_id: str, question: str) -> Dict[str, Any]:
        """
        Ask Aura a question about inventory.
        
        Examples:
        - "Should I reorder hydraulic pumps?"
        - "What's the current stock level for part P001?"
        - "Is it safe to order from Supplier A?"
        """
        return self.safety_layer.query_with_safety(part_id, question)
    
    def get_all_low_stock_parts(self) -> List[Dict[str, Any]]:
        """
        TODO: Query for all parts that need reordering
        """
        pass
    
    def get_parts_with_warnings(self) -> List[Dict[str, Any]]:
        """
        TODO: Get all parts with data quality warnings
        """
        pass
    
    def close(self):
        self.safety_layer.close()
