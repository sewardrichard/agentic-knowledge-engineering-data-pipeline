"""
Generate Mock Warehouse Data - ONE-TIME SETUP SCRIPT

⚠️ IMPORTANT: Run this ONCE during initial setup, NOT before each demo run!

Creates a realistic CSV with intentional scenarios for demo:
- High stock (SAFE query)
- Shadow stock scenario (delivered but not counted)
- Low stock (URGENT reorder)
- Out of stock (CRITICAL)
- Varied update patterns simulating shift changes

The timestamps are intentionally OLD (10+ hours ago) to create the shadow stock
scenario when compared with the mock API's delivery timestamps.

DO NOT regenerate this file before each demo run, or the timestamps will be fresh
and shadow stock detection won't work!
"""

import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import random


def generate_warehouse_csv(output_path: str = "./data/raw/warehouse_stock.csv"):
    """
    Generate mock warehouse inventory CSV with realistic mining operation data.
    
    Scenarios covered:
    - P001: High stock, recent update → SAFE query
    - P002: Medium stock with in-transit → SAFE with in-transit
    - P003: Shadow stock scenario (warehouse count is OLD, delivery happened after)
    - P004: Low stock → URGENT reorder
    - P005: Out of stock → CRITICAL
    """
    
    now = datetime.now()
    
    # Define parts with specific scenarios
    parts_data = [
        {
            "part_id": "P001",
            "part_name": "Hydraulic Pump HP-2000",
            "qty_on_shelf": 45,
            "unit_cost_zar": 12500.00,
            "warehouse_location": "Rustenburg-Main",
            # Recent update - high confidence
            "last_updated": (now - timedelta(hours=3)).strftime("%Y-%m-%d %H:%M:%S")
        },
        {
            "part_id": "P002",
            "part_name": "Conveyor Belt 1200mm",
            "qty_on_shelf": 35,
            "unit_cost_zar": 8900.50,
            "warehouse_location": "Rustenburg-Main",
            # Recent update
            "last_updated": (now - timedelta(hours=5)).strftime("%Y-%m-%d %H:%M:%S")
        },
        {
            "part_id": "P003",
            "part_name": "Safety Valve SV-100",
            "qty_on_shelf": 78,
            "unit_cost_zar": 3200.00,
            "warehouse_location": "Rustenburg-Backup",
            # OLD update - 10 hours ago, BEFORE delivery at 8 hours ago
            # This creates SHADOW STOCK scenario
            "last_updated": (now - timedelta(hours=10)).strftime("%Y-%m-%d %H:%M:%S")
        },
        {
            "part_id": "P004",
            "part_name": "Drill Bit 45mm Carbide",
            "qty_on_shelf": 5,  # LOW STOCK - triggers urgent reorder
            "unit_cost_zar": 1850.00,
            "warehouse_location": "Rustenburg-Main",
            "last_updated": (now - timedelta(hours=4)).strftime("%Y-%m-%d %H:%M:%S")
        },
        {
            "part_id": "P005",
            "part_name": "Bearing Assembly BA-500",
            "qty_on_shelf": 0,  # OUT OF STOCK - critical
            "unit_cost_zar": 6750.00,
            "warehouse_location": "Rustenburg-Main",
            "last_updated": (now - timedelta(hours=6)).strftime("%Y-%m-%d %H:%M:%S")
        }
    ]
    
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
    print("\n📋 Scenario breakdown:")
    for _, row in df.iterrows():
        stock_status = "✅ OK" if row['qty_on_shelf'] >= 50 else "⚠️ LOW" if row['qty_on_shelf'] > 0 else "🔴 OUT"
        print(f"   {row['part_id']}: {row['qty_on_shelf']:3d} units [{stock_status}] - {row['part_name']}")
    
    return df


if __name__ == "__main__":
    generate_warehouse_csv()
