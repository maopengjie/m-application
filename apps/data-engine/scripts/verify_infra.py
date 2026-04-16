import sys
import os
from sqlalchemy import text
from redis import Redis

# Add the project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal, engine
from app.core.config import get_settings
from app.core.redis import get_redis_client

def verify_mysql():
    print("Verifying MySQL connection...")
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            print(f"  MySQL OK: {result.scalar()}")
            
            # Check tables
            result = connection.execute(text("SHOW TABLES"))
            tables = [row[0] for row in result]
            print(f"  Tables found: {tables}")
            
            required_tables = ['products', 'product_skus', 'price_history', 'alembic_version']
            missing = [t for t in required_tables if t not in tables]
            if not missing:
                print("  All core tables exist.")
            else:
                print(f"  Missing tables: {missing}")
                return False
        return True
    except Exception as e:
        print(f"  MySQL Failed: {e}")
        return False

def verify_redis():
    print("Verifying Redis connection...")
    try:
        redis_client = get_redis_client()
        pong = redis_client.ping()
        print(f"  Redis PING: {pong}")
        
        # Test write/read
        redis_client.set("smoke_test", "ok")
        val = redis_client.get("smoke_test")
        print(f"  Redis Read/Write: {val}")
        return val == "ok"
    except Exception as e:
        print(f"  Redis Failed: {e}")
        return False

if __name__ == "__main__":
    mysql_ok = verify_mysql()
    print("-" * 20)
    redis_ok = verify_redis()
    
    print("-" * 20)
    if mysql_ok and redis_ok:
        print("INFRASTRUCTURE VERIFICATION PASSED")
        sys.exit(0)
    else:
        print("INFRASTRUCTURE VERIFICATION FAILED")
        sys.exit(1)
