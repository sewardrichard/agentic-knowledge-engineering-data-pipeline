"""
Aura Agent Safety Layer

Prevents Aura from making procurement decisions based on unreliable data.

Safety Principles:
1. Never trust stale data (>24 hours old)
2. Block queries on low-reliability data (<0.6)
3. Warn on detected inconsistencies
4. Provide confidence levels with all responses
5. Always explain reasoning

This is what separates a "chatbot" from an "agentic system."
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta, timezone
import duckdb


class AuraAgentSafetyLayer:
    """
    Enforces safety checks before Aura queries knowledge base.
    
    Think of this as the "guardrails" that prevent autonomous decisions
    from going wrong.
    """
    
    # Configurable thresholds
    MIN_RELIABILITY = 0.6
    MAX_DATA_AGE_HOURS = 24
    
    def __init__(self, db_path: str):
        """
        Args:
            db_path: Path to DuckDB database with Gold layer
        """
        self.db_path = db_path
        self.conn = duckdb.connect(db_path, read_only=True)
    
    def query_with_safety(
        self, 
        part_id: str, 
        question: str
    ) -> Dict[str, Any]:
        """
        Main entry point for Aura to query inventory data.
        
        TODO: Implement complete safety check logic
        
        Process:
        1. Query gold.inventory_facts for part_id
        2. Run all safety checks
        3. Determine if query should be:
           - SAFE (proceed normally)
           - WARNING (proceed with caution)
           - BLOCKED (require human intervention)
        4. Return structured response with reasoning
        
        Args:
            part_id: Which part Aura is asking about
            question: Natural language question (for context)
        
        Returns:
            {
                "status": "SAFE" | "WARNING" | "BLOCKED",
                "data": {...} or None,
                "confidence": "high" | "medium" | "low",
                "reasoning": "...",
                "warnings": [...],
                "recommended_action": "..."
            }
        """
        # Query gold layer
        fact = self._query_gold_layer(part_id)
        
        if fact is None:
            return {
                "status": "BLOCKED",
                "reason": f"No data found for part {part_id}",
                "action": "Verify part_id is correct or add part to system",
                "data": None
            }
        
        # Run safety checks
        safety_checks = {
            "is_fresh": self._check_freshness(fact),
            "is_reliable": self._check_reliability(fact),
            "has_conflicts": fact.get("has_inconsistency", False),
            "confidence_level": fact.get("confidence_level", "unknown")
        }
        
        # Decision logic
        if not safety_checks["is_reliable"]:
            return {
                "status": "BLOCKED",
                "reason": f"Data reliability ({fact['data_reliability_index']:.1%}) below threshold ({self.MIN_RELIABILITY:.0%})",
                "action": "Request fresh warehouse count or verify logistics data",
                "data": fact,  # Include data so timestamp analysis can still display
                "checks": safety_checks
            }
        
        if safety_checks["has_conflicts"]:
            return {
                "status": "WARNING",
                "reason": "Shadow stock detected - possible unprocessed delivery",
                "action": "Verify with warehouse supervisor before ordering",
                "data": fact,
                "confidence": "low",
                "warnings": [
                    "Recent delivery may not be reflected in physical count",
                    "Effective inventory calculation may be understated"
                ],
                "checks": safety_checks
            }
        
        if not safety_checks["is_fresh"]:
            return {
                "status": "WARNING",
                "reason": f"Data is stale (last updated: {fact['shelf_last_updated']})",
                "action": "Consider requesting fresh warehouse count",
                "data": fact,
                "confidence": safety_checks["confidence_level"],
                "warnings": ["Data may not reflect recent changes"],
                "checks": safety_checks
            }
        
        # All checks passed - safe to proceed
        return {
            "status": "SAFE",
            "data": fact,
            "confidence": safety_checks["confidence_level"],
            "reasoning": self._generate_reasoning(fact, question),
            "checks": safety_checks
        }
    
    def _query_gold_layer(self, part_id: str) -> Optional[Dict[str, Any]]:
        """
        Query the gold.inventory_facts table.
        """
        try:
            query = """
                SELECT 
                    part_id,
                    part_name,
                    qty_on_shelf,
                    in_transit_qty,
                    shadow_stock_qty,
                    effective_inventory,
                    data_reliability_index,
                    semantic_context,
                    has_inconsistency,
                    confidence_level,
                    reorder_recommendation,
                    shelf_last_updated
                FROM gold.inventory_facts
                WHERE part_id = ?
                AND fact_valid_to IS NULL  -- Get current fact only
            """
            
            result = self.conn.execute(query, [part_id]).fetchone()
            
            if result is None:
                return None
            
            # Convert to dictionary
            columns = [desc[0] for desc in self.conn.description]
            fact = dict(zip(columns, result))
            
            # Parse JSON fields
            if fact.get('reorder_recommendation'):
                import json
                reorder = fact['reorder_recommendation']
                if isinstance(reorder, str):
                    fact['reorder_recommendation'] = json.loads(reorder)
            
            return fact
        
        except Exception as e:
            print(f"Error querying gold layer: {e}")
            return None
    
    def _check_freshness(self, fact: Dict[str, Any]) -> bool:
        """
        Check if data is fresh enough for autonomous decisions.
        Returns True if data is within MAX_DATA_AGE_HOURS threshold.
        """
        if not fact.get("shelf_last_updated"):
            return False
        
        try:
            last_update_str = fact["shelf_last_updated"]
            # Handle both timezone-aware and naive timestamps
            if isinstance(last_update_str, str):
                last_update = datetime.fromisoformat(last_update_str.replace('Z', '+00:00'))
            else:
                last_update = last_update_str
            
            # Make timezone-aware if naive
            if last_update.tzinfo is None:
                last_update = last_update.replace(tzinfo=timezone.utc)
            
            now = datetime.now(timezone.utc)
            age = now - last_update
            
            return age < timedelta(hours=self.MAX_DATA_AGE_HOURS)
        except Exception as e:
            print(f"Error checking freshness: {e}")
            return False
    
    def _check_reliability(self, fact: Dict[str, Any]) -> bool:
        """Check if reliability score meets minimum threshold"""
        reliability = fact.get("data_reliability_index", 0)
        return reliability >= self.MIN_RELIABILITY
    
    def _generate_reasoning(self, fact: Dict[str, Any], question: str) -> str:
        """
        Generate human-readable reasoning for Aura's response.
        
        This helps humans understand why Aura made a particular decision.
        """
        effective_inv = fact["effective_inventory"]
        reorder = fact["reorder_recommendation"]
        
        reasoning = f"Based on current data:\n"
        reasoning += f"- Effective inventory: {effective_inv} units\n"
        reasoning += f"- Data reliability: {fact['data_reliability_index']:.2%}\n"
        reasoning += f"- {fact['semantic_context']}\n"
        reasoning += f"\nRecommendation: {reorder['reasoning']}"
        
        return reasoning
    
    def close(self):
        """Close database connection"""
        self.conn.close()
