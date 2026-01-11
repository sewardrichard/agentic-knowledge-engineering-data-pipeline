"""
Pipeline Runner Script

Usage:
  python scripts/run_pipeline.py --layer bronze
  python scripts/run_pipeline.py --layer all
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pipeline import run_bronze_layer, run_silver_layer, run_gold_layer, run_full_pipeline
import argparse


def main():
    parser = argparse.ArgumentParser(description="Run Aura Knowledge Pipeline")
    parser.add_argument(
        "--layer",
        choices=["bronze", "silver", "gold", "all"],
        default="all",
        help="Which layer to run"
    )
    
    args = parser.parse_args()
    
    if args.layer == "bronze":
        run_bronze_layer()
    elif args.layer == "silver":
        bronze_pipeline = run_bronze_layer()
        run_silver_layer(bronze_pipeline)
    elif args.layer == "gold":
        bronze_pipeline = run_bronze_layer()
        silver_pipeline = run_silver_layer(bronze_pipeline)
        run_gold_layer(silver_pipeline)
    else:  # all
        run_full_pipeline()


if __name__ == "__main__":
    main()
