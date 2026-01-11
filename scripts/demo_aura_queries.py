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


def print_header():
    """Print demo header"""
    print("\n" + "=" * 70)
    print("🤖 AURA AGENT QUERY DEMONSTRATION")
    print("=" * 70)
    print("Demonstrating how Aura handles different data quality scenarios")
    print("This shows the Agent Safety Layer in action.\n")


def print_response(response: dict, scenario_name: str, emoji: str = "📋"):
    """Pretty print Aura's response"""
    print("\n" + "-" * 70)
    print(f"{emoji} SCENARIO: {scenario_name}")
    print("-" * 70)
    
    status = response.get('status', 'UNKNOWN')
    status_emoji = {"SAFE": "🟢", "WARNING": "🟡", "BLOCKED": "🔴"}.get(status, "⚪")
    print(f"Status: {status_emoji} {status}")
    
    if response.get('confidence'):
        print(f"Confidence: {response['confidence'].upper()}")
    
    if response.get('data'):
        data = response['data']
        print(f"\n📦 Inventory Data:")
        print(f"  • Effective Inventory: {data.get('effective_inventory', 'N/A')} units")
        print(f"  • On Shelf: {data.get('qty_on_shelf', 'N/A')} units")
        print(f"  • In Transit: {data.get('in_transit_qty', 'N/A')} units")
        
        reliability = data.get('data_reliability_index')
        if reliability:
            print(f"  • Data Reliability: {reliability:.1%}")
        
        if data.get('semantic_context'):
            print(f"\n📝 Context: {data['semantic_context']}")
        
        # Show reorder recommendation
        reorder = data.get('reorder_recommendation')
        if reorder:
            if isinstance(reorder, str):
                try:
                    reorder = json.loads(reorder)
                except:
                    pass
            if isinstance(reorder, dict):
                urgency = reorder.get('urgency', 'unknown')
                urgency_emoji = {
                    "urgent": "🚨",
                    "recommended": "📋",
                    "none": "✅",
                    "manual_review": "👁️"
                }.get(urgency, "❓")
                print(f"\n💡 Recommendation ({urgency_emoji} {urgency.upper()}):")
                print(f"   {reorder.get('reasoning', 'N/A')}")
    
    if response.get('reasoning'):
        print(f"\n💭 Aura's Reasoning:\n{response['reasoning']}")
    
    if response.get('warnings'):
        print(f"\n⚠️  Warnings:")
        for warning in response['warnings']:
            print(f"  • {warning}")
    
    if response.get('reason'):
        print(f"\n❌ Reason: {response['reason']}")
    
    if response.get('action'):
        print(f"🎯 Recommended Action: {response['action']}")


def run_demo_scenarios():
    """
    Demonstrate 4 key scenarios that show safety layer in action.
    
    Scenarios:
    1. SAFE - High quality data, adequate stock
    2. WARNING - Shadow stock detected (delivered but not scanned)
    3. WARNING - Low stock requiring urgent reorder
    4. SAFE/WARNING - Out of stock with incoming shipment
    """
    
    print_header()
    
    # Initialize Aura interface
    db_path = "./data/processed/aura.duckdb"
    
    try:
        aura = AuraQueryInterface(db_path)
    except Exception as e:
        print(f"❌ Could not connect to database: {e}")
        print("\n📋 Make sure you've run the pipeline first:")
        print("   1. Start the mock API: uvicorn mock_apis.main:app --port 8000")
        print("   2. Run the pipeline: python scripts/run_pipeline.py")
        return
    
    print(f"📊 Connected to knowledge base: {db_path}")
    
    # Get inventory summary first
    print("\n" + "=" * 70)
    print("📈 INVENTORY SUMMARY")
    print("=" * 70)
    summary = aura.get_inventory_summary()
    if summary:
        print(f"  • Total Parts Tracked: {summary.get('total_parts', 0)}")
        print(f"  • Total Units: {summary.get('total_units', 0)}")
        print(f"  • Average Reliability: {summary.get('avg_reliability', 0):.1%}")
        print(f"  • Parts with Warnings: {summary.get('parts_with_warnings', 0)}")
        print(f"  • Urgent Reorders Needed: {summary.get('urgent_reorders', 0)}")
    
    # =========================================================================
    # Scenario 1: Normal Query - High Quality Data (SAFE)
    # =========================================================================
    print("\n" + "=" * 70)
    print("🟢 SCENARIO 1: Normal Query - High Quality Data")
    print("=" * 70)
    print("Aura asks: 'Should I reorder Hydraulic Pumps (P001)?'")
    print("Expected: SAFE response with high confidence")
    
    response1 = aura.ask("P001", "Should I reorder Hydraulic Pumps?")
    print_response(response1, "High Confidence Query - P001 Hydraulic Pumps", "🟢")
    
    # =========================================================================
    # Scenario 2: Shadow Stock Warning
    # =========================================================================
    print("\n" + "=" * 70)
    print("🟡 SCENARIO 2: Shadow Stock Detected")
    print("=" * 70)
    print("Aura asks: 'What's the stock level for Safety Valves (P003)?'")
    print("Expected: WARNING - Delivery marked complete but not in warehouse count")
    
    response2 = aura.ask("P003", "What's the stock level for Safety Valves?")
    print_response(response2, "Shadow Stock Detection - P003 Safety Valves", "🟡")
    
    # =========================================================================
    # Scenario 3: Low Stock - Urgent Reorder
    # =========================================================================
    print("\n" + "=" * 70)
    print("🟠 SCENARIO 3: Low Stock - Urgent Reorder Needed")
    print("=" * 70)
    print("Aura asks: 'Do we have enough Drill Bits (P004)?'")
    print("Expected: Data showing low stock with urgent reorder recommendation")
    
    response3 = aura.ask("P004", "Do we have enough Drill Bits?")
    print_response(response3, "Low Stock Alert - P004 Drill Bits", "🟠")
    
    # =========================================================================
    # Scenario 4: Out of Stock with Incoming Shipment
    # =========================================================================
    print("\n" + "=" * 70)
    print("🔴 SCENARIO 4: Out of Stock - Emergency Situation")
    print("=" * 70)
    print("Aura asks: 'What's the situation with Bearing Assemblies (P005)?'")
    print("Expected: Critical stock level (0 on shelf) with in-transit units")
    
    response4 = aura.ask("P005", "What's the situation with Bearing Assemblies?")
    print_response(response4, "Out of Stock - P005 Bearing Assemblies", "🔴")
    
    # =========================================================================
    # Show parts that need attention
    # =========================================================================
    print("\n" + "=" * 70)
    print("📋 PARTS REQUIRING ATTENTION")
    print("=" * 70)
    
    # Parts with warnings
    warnings = aura.get_parts_with_warnings()
    if warnings:
        print("\n⚠️  Parts with Data Quality Warnings:")
        for part in warnings:
            print(f"  • {part.get('part_id')}: {part.get('part_name', 'Unknown')}")
            print(f"    Reliability: {part.get('data_reliability_index', 0):.1%}, "
                  f"Inconsistency: {'Yes' if part.get('has_inconsistency') else 'No'}")
    else:
        print("\n✅ No data quality warnings")
    
    # Parts needing reorder
    low_stock = aura.get_all_low_stock_parts()
    if low_stock:
        print("\n🛒 Parts Needing Reorder:")
        for part in low_stock:
            print(f"  • {part.get('part_id')}: {part.get('part_name', 'Unknown')}")
            print(f"    Stock: {part.get('effective_inventory', 0)} units, "
                  f"Confidence: {part.get('confidence_level', 'unknown')}")
    else:
        print("\n✅ No parts need reordering")
    
    # Cleanup
    aura.close()
    
    # Final summary
    print("\n" + "=" * 70)
    print("✅ DEMO COMPLETE")
    print("=" * 70)
    print("""
Key Takeaways:
  • SAFE queries proceed with full data access
  • WARNING queries provide data but flag concerns  
  • BLOCKED queries prevent autonomous decisions on bad data
  • Aura always explains its reasoning and recommends actions

This demonstrates how the Agent Safety Layer prevents costly mistakes
by ensuring Aura only acts on trustworthy knowledge.
""")


if __name__ == "__main__":
    try:
        run_demo_scenarios()
    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\n📋 Troubleshooting steps:")
        print("   1. Start the mock API:")
        print("      uvicorn mock_apis.main:app --port 8000")
        print("   2. Run the pipeline:")
        print("      python scripts/run_pipeline.py")
        print("   3. Then run this demo:")
        print("      python scripts/demo_aura_queries.py")
