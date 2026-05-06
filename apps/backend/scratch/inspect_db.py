
import sqlite3
import os

db_path = "/Users/maopengjie/Documents/m-application/apps/backend/data/app.db"
if not os.path.exists(db_path):
    print(f"Database not found at {db_path}")
else:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("--- SkuProduct (ID 7) ---")
    cursor.execute("SELECT id, platform, sku_id, product_name FROM sku_product WHERE id = 7")
    row = cursor.fetchone()
    print(row)
    
    print("\n--- SkuPriceSnapshot for Product ID 7 ---")
    cursor.execute("SELECT COUNT(*) FROM sku_price_snapshot WHERE sku_product_id = 7")
    count = cursor.fetchone()[0]
    print(f"Count: {count}")
    
    print("\n--- All SkuProducts ---")
    cursor.execute("SELECT id, platform, sku_id FROM sku_product")
    rows = cursor.fetchall()
    for r in rows:
        print(r)
        
    conn.close()
