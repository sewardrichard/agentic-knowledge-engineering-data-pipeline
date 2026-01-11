"""
Simplified query interface for Aura.

This is what a client application would use to interact with Aura.
"""

from typing import Dict, List, Any
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
        Query for all parts that need reordering.
        Returns parts where reorder_recommendation suggests action.
        """
        try:
            query = """
                SELECT 
                    part_id,
                    part_name,
                    effective_inventory,
                    reorder_recommendation,
                    confidence_level
                FROM gold.inventory_facts
                WHERE fact_valid_to IS NULL
                AND (
                    json_extract_string(reorder_recommendation, '$.urgency') = 'urgent'
                    OR json_extract_string(reorder_recommendation, '$.urgency') = 'recommended'
                )
                ORDER BY effective_inventory ASC
            """
            results = self.safety_layer.conn.execute(query).fetchall()
            columns = ['part_id', 'part_name', 'effective_inventory', 'reorder_recommendation', 'confidence_level']
            return [dict(zip(columns, row)) for row in results]
        except Exception as e:
            print(f"Error querying low stock parts: {e}")
            return []
    
    def get_parts_with_warnings(self) -> List[Dict[str, Any]]:
        """
        Get all parts with data quality warnings (inconsistencies or low reliability).
        """
        try:
            query = """
                SELECT 
                    part_id,
                    part_name,
                    effective_inventory,
                    data_reliability_index,
                    has_inconsistency,
                    semantic_context,
                    confidence_level
                FROM gold.inventory_facts
                WHERE fact_valid_to IS NULL
                AND (has_inconsistency = TRUE OR data_reliability_index < 0.6)
                ORDER BY data_reliability_index ASC
            """
            results = self.safety_layer.conn.execute(query).fetchall()
            columns = ['part_id', 'part_name', 'effective_inventory', 'data_reliability_index', 
                      'has_inconsistency', 'semantic_context', 'confidence_level']
            return [dict(zip(columns, row)) for row in results]
        except Exception as e:
            print(f"Error querying parts with warnings: {e}")
            return []
    
    def get_inventory_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the entire inventory state.
        """
        try:
            query = """
                SELECT 
                    COUNT(*) as total_parts,
                    SUM(effective_inventory) as total_units,
                    AVG(data_reliability_index) as avg_reliability,
                    SUM(CASE WHEN has_inconsistency THEN 1 ELSE 0 END) as parts_with_warnings,
                    SUM(CASE WHEN json_extract_string(reorder_recommendation, '$.urgency') = 'urgent' THEN 1 ELSE 0 END) as urgent_reorders
                FROM gold.inventory_facts
                WHERE fact_valid_to IS NULL
            """
            result = self.safety_layer.conn.execute(query).fetchone()
            return {
                "total_parts": result[0],
                "total_units": result[1],
                "avg_reliability": round(result[2], 3) if result[2] else 0,
                "parts_with_warnings": result[3],
                "urgent_reorders": result[4]
            }
        except Exception as e:
            print(f"Error getting inventory summary: {e}")
            return {}
    
    def close(self):
        self.safety_layer.close()
