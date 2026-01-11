"""
Warehouse CSV Source

Characteristics:
- Manual data entry (prone to delays, typos)
- Updated at shift changes (every 8 hours)
- Lower reliability score (0.7)
- Represents physical "on-shelf" inventory
"""

import pandas as pd
from pathlib import Path
from typing import Iterator, Dict, Any
from .base_source import BaseSource


class WarehouseSource(BaseSource):
    """
    Ingests warehouse physical inventory from CSV file.
    
    Expected CSV columns:
    - part_id: Unique part identifier
    - part_name: Human-readable name
    - qty_on_shelf: Physical count
    - unit_cost_zar: Cost in South African Rand
    - last_updated: When count was performed
    - warehouse_location: Which warehouse
    """
    
    def __init__(self, csv_path: str, reliability_score: float = 0.7):
        super().__init__(
            name="warehouse_stock",
            reliability_score=reliability_score,
            source_type="csv",
            update_frequency="shift_change"
        )
        self.csv_path = Path(csv_path)
        
        if not self.csv_path.exists():
            raise FileNotFoundError(f"Warehouse CSV not found: {csv_path}")
    
    def load_raw_data(self) -> Iterator[Dict[str, Any]]:
        """
        Load warehouse data from CSV.
        
        TODO: Add data quality checks here:
        - Check for negative quantities
        - Validate part_id format
        - Handle missing values
        """
        # Read CSV
        df = pd.read_csv(self.csv_path)
        
        # TODO: Add data cleaning logic
        # Example:
        # - df['part_id'] = df['part_id'].str.strip().str.upper()
        # - df = df[df['qty_on_shelf'] >= 0]  # Remove negative quantities
        
        # Convert to dictionaries and yield
        for _, row in df.iterrows():
            yield {
                "part_id": row["part_id"],
                "part_name": row["part_name"],
                "quantity": row["qty_on_shelf"],  # Semantic: on-shelf quantity
                "unit_cost_zar": float(row["unit_cost_zar"]),
                "last_updated": row["last_updated"],
                "warehouse_location": row["warehouse_location"],
                # Add semantic context
                "quantity_semantic": "on_shelf",  # Important for conflict resolution
            }