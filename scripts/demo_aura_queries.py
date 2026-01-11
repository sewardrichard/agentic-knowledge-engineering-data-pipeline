"""
Aura Query Demonstration

Shows how Aura would interact with the knowledge base in different scenarios.

Run after pipeline has completed: python scripts/demo_aura_queries.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agent import AuraQueryInterface
import json


def print_response(response: dict, scenario_name: str):
    """Pretty print Aura's response"""
    print("\n" + "=" * 70)
    print(f"📋 SCENARIO: {scenario_name}")
    print("=" * 70)
    print(f"Status: {response['status']}")
    
    if response.get('data'):
        print(f"\nInventory Data:")
        print(f"  • Effective Inventory: {response['data']['effective_inventory']} units")
        print(f"  • On Shelf: {response['data']['qty_on_shelf']} units")
        print(f"  • In Transit: {response['data']['in_transit_qty']} units")
        print(f"  • Reliability: {response['data']['data_reliability_index']:.1%}")
    
    if response.get('reasoning'):
        print(f"\n💡 Reasoning:\n{response['reasoning']}")
    
    if response.get('warnings'):
        print(f"\n⚠️  Warnings:")
        for warning in response['warnings']:
            print(f"  • {warning}")
    
    if response.get('reason'):
        print(f"\n❌ Blocked: {response['reason']}")
        print(f"   Recommended Action: {response.get('action', 'N/A')}")
    
    print()


def run_demo_scenarios():
    """
    Demonstrate 4 key scenarios that show safety layer in action.
    
    TODO: Implement these scenarios after pipeline is complete
    """
    
    print("🤖 AURA AGENT QUERY DEMONSTRATION")
    print("=" * 70)
    print("Demonstrating how Aura handles different data quality scenarios\n")
    
    # Initialize Aura interface
    db_path = "./data/processed/aura.duckdb"
    aura = AuraQueryInterface(db_path)
    
    # Scenario 1: Normal query (high confidence)
    print("\n🟢 Scenario 1: Normal Query - High Quality Data")
    response1 = aura.ask("P001", "Should I reorder Hydraulic Pumps?")
    print_response(response1, "High Confidence Query")
    
    # Scenario 2: Shadow stock detected
    print("\n🟡 Scenario 2: Shadow Stock Warning")
    response2 = aura.ask("P003", "What's the stock level for Safety Valves?")
    print_response(response2, "Shadow Stock Detection")
    
    # Scenario 3: Stale data
    print("\n🟠 Scenario 3: Stale Data Warning")
    # TODO: Query a part with old timestamp
    
    # Scenario 4: Low reliability - blocked
    print("\n🔴 Scenario 4: Low Reliability - Blocked")
    # TODO: Query a part with low reliability score
    
    # Cleanup
    aura.close()
    
    print("\n" + "=" * 70)
    print("✅ Demo complete!")
    print("=" * 70)


if __name__ == "__main__":
    try:
        run_demo_scenarios()
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nMake sure you've run the pipeline first:")
        print("  python scripts/run_pipeline.py")
