"""
Generate Mock Warehouse Data

Creates a realistic CSV with intentional messiness:
- Delayed timestamps
- Occasional typos
- Varied update patterns
"""

import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import random


def generate_warehouse_csv(output_path: str = "./data/raw/warehouse_stock.csv"):
    """
    Generate mock warehouse inventory CSV.
    
    TODO: Enhance with more realistic scenarios
    - Add parts that are out of stock
    - Include different warehouse locations
    - Vary update timestamps to simulate shift patterns
    """
    
    # Define parts
    parts_data = [
        {
            "part_id": "P001",
            "part_name": "Hydraulic Pump HP-2000",
            "qty_on_shelf": 45,
            "unit_cost_zar": 12500.00,
            "warehouse_location": "JHB-North"
        },
        {
            "part_id": "P002",
            "part_name": "Conveyor Belt 1200mm",
            "qty_on_shelf": 12,
            "unit_cost_zar": 8900.50,
            "warehouse_location": "JHB-South"
        },
        {
            "part_id": "P003",
            "part_name": "Safety Valve SV-100",
            "qty_on_shelf": 78,
            "unit_cost_zar": 3200.00,
            "warehouse_location": "CPT-Main"
        },
        {
            "part_id": "P004",
            "part_name": "Drill Bit 45mm Carbide",
            "qty_on_shelf": 5,  # Low stock to trigger reorder
            "unit_cost_zar": 1850.00,
            "warehouse_location": "JHB-North"
        },
        {
            "part_id": "P005",
            "part_name": "Bearing Assembly BA-500",
            "qty_on_shelf": 0,  # Out of stock!
            "unit_cost_zar": 6750.00,
            "warehouse_location": "JHB-South"
        }
    ]
    
    # Add timestamps (simulate shift change updates)
    now = datetime.now()
    for i, part in enumerate(parts_data):
        # Vary update times to simulate different shifts
        hours_ago = random.randint(2, 12)
        part["last_updated"] = (now - timedelta(hours=hours_ago)).strftime("%Y-%m-%d %H:%M:%S")
    
    # Create DataFrame
    df = pd.DataFrame(parts_data)
    
    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save to CSV
    df.to_csv(output_path, index=False)
    
    print(f"✅ Generated warehouse CSV: {output_path}")
    print(f"   Parts: {len(df)}")
    print(f"   Total inventory value: R{df['qty_on_shelf'].mul(df['unit_cost_zar']).sum():,.2f}")
