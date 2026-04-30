import os
import sys
import subprocess
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

# Add the project root to sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from app.core.config import get_settings

def init_db():
    settings = get_settings()
    dsn = settings.mysql_dsn
    
    # Extract DB name and base DSN for creation
    if "mysql" in dsn:
        base_dsn, db_name = dsn.rsplit("/", 1)
        if "?" in db_name:
            db_name = db_name.split("?")[0]
            
        print(f"Checking for database: {db_name}...")
        temp_engine = create_engine(base_dsn)
        try:
            with temp_engine.connect() as conn:
                conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
                print(f"Database {db_name} created or already exists.")
        except Exception as e:
            print(f"Warning: Could not automatically create database. Reason: {e}")
        finally:
            temp_engine.dispose()

    # Run Alembic migrations
    print("Running Alembic migrations...")
    try:
        # Use current python interpreter to run alembic module
        subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], check=True)
        print("Migrations applied successfully.")
    except Exception as e:
        print(f"Error: Alembic migration failed. Reason: {e}")
        return

    # Run Seed Data
    print("Checking for seed data...")
    from scripts.seed_data import seed_data
    seed_data()
    
    print("\nDatabase initialization complete! ✅")

if __name__ == "__main__":
    init_db()
