"""Debug script to check timestamps in the database"""
import duckdb

conn = duckdb.connect('./data/processed/aura.duckdb')

print("=" * 70)
print("BRONZE LAYER - Warehouse Records")
print("=" * 70)
result = conn.execute("""
    SELECT part_id, quantity, last_updated, _ingested_at 
    FROM bronze.warehouse_stock 
    WHERE part_id = 'P003'
""").fetchall()
for row in result:
    print(f"Part: {row[0]}, Qty: {row[1]}, LastUpdated: {row[2]}, Ingested: {row[3]}")

print("\n" + "=" * 70)
print("SILVER LAYER - Events")
print("=" * 70)
result = conn.execute("""
    SELECT part_id, quantity, event_timestamp, ingestion_timestamp, source_system
    FROM silver.inventory_events 
    WHERE part_id = 'P003'
""").fetchall()
for row in result:
    print(f"Part: {row[0]}, Qty: {row[1]}, EventTime: {row[2]}, IngestionTime: {row[3]}, Source: {row[4]}")

print("\n" + "=" * 70)
print("GOLD LAYER - Facts")
print("=" * 70)
result = conn.execute("""
    SELECT part_id, qty_on_shelf, shadow_stock_qty, shelf_last_updated, has_inconsistency
    FROM gold.inventory_facts 
    WHERE part_id = 'P003'
""").fetchall()
for row in result:
    print(f"Part: {row[0]}, OnShelf: {row[1]}, Shadow: {row[2]}, LastUpdated: {row[3]}, HasIssue: {row[4]}")

conn.close()
