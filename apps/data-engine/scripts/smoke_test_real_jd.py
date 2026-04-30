import sys
import os

# Add the app directory to sys.path
sys.path.append(os.path.join(os.getcwd()))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.product import ProductSKU
from app.services.scraper import ScraperFactory
import json

def smoke_test_real_jd():
    """
    Smoke test to verify real JD scraping capabilities.
    Hits up to 3 JD SKUs already in the database and prints their true live status.
    """
    print("=== JD Real-World Smoke Test Started ===")
    db = SessionLocal()
    try:
        # Find JD SKUs
        jd_skus = db.query(ProductSKU).filter(ProductSKU.platform == "JD").limit(3).all()
        
        if not jd_skus:
            print("[ERROR] No JD SKUs found in database. Please run 'seed_real_data.py' first.")
            return

        print(f"Found {len(jd_skus)} JD SKUs to test.\n")

        for sku in jd_skus:
            print(f"--- Testing SKU: {sku.platform_sku_id} ---")
            print(f"Existing Title: {sku.title}")
            print(f"Existing Price: ¥{sku.price}")
            print("Action: Fetching LIVE data from JD...")
            
            result = ScraperFactory.scrape(sku)
            
            if result.success:
                print(f"[SUCCESS]")
                print(f" Live Title: {result.title}")
                print(f" Live Price: ¥{result.price}")
                print(f" Live Shop : {result.shop_name}")
                print(f" Live Stock: {result.stock_status}")
                print(f" Live Orig : ¥{result.original_price}")
            else:
                print(f"[FAILED] Error Code: {result.error_code}")
                print(f" Error Message: {result.error_message}")
            print("-" * 40 + "\n")

    except Exception as e:
        print(f"Critical error during smoke test: {e}")
    finally:
        db.close()
        print("=== Smoke Test Finished ===")

if __name__ == "__main__":
    smoke_test_real_jd()
