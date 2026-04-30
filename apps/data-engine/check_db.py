import os
import sys
from sqlalchemy import text

# Add current dir to sys.path to find 'app'
sys.path.append(os.getcwd())
try:
    from app.core.database import SessionLocal
except ImportError:
    # If app is not in path, try adding src?
    # Actually BASE_DIR should be the project root
    pass

def check():
    try:
        db = SessionLocal()
        result = db.execute(text("SELECT count(*) FROM products")).scalar()
        print(f"Total Products: {result}")
        
        sku_count = db.execute(text("SELECT count(*) FROM product_skus")).scalar()
        print(f"Total SKUs: {sku_count}")
        
        # Check table names just in case
        table_names = db.execute(text("SELECT name FROM sqlite_master WHERE type='table';")).fetchall()
        if not table_names:
            # Maybe it's MySQL
            pass
        
        db.close()
    except Exception as e:
        print(f"Error checking DB: {e}")

if __name__ == "__main__":
    check()
