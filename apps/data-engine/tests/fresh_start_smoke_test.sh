#!/bin/bash
set -e

# fresh_start_smoke_test.sh: Verifies migration, seed and start from scratch.

echo "[1/4] Cleaning existing DB tables..."
# Using a python one-liner to drop all tables based on Base.metadata
.venv/bin/python -c "
from app.core.database import engine, Base
from app.models.user import User
from app.models.product import Product, ProductSKU, PriceHistory, Coupon, Review, RiskScore, PriceAlert
from app.models.task import CrawlTask
import sqlalchemy as sa

with engine.connect() as conn:
    # Disable foreign key checks for clean drop in MySQL
    if engine.url.drivername.startswith('mysql'):
        conn.execute(sa.text('SET FOREIGN_KEY_CHECKS = 0'))
        
    Base.metadata.drop_all(bind=engine)
    conn.execute(sa.text('DROP TABLE IF EXISTS alembic_version'))
    
    if engine.url.drivername.startswith('mysql'):
        conn.execute(sa.text('SET FOREIGN_KEY_CHECKS = 1'))
    conn.commit()
print('Tables dropped successfully.')"

echo "[2/4] Running Alembic Migrations..."
.venv/bin/alembic upgrade head

echo "[3/4] Seeding Initial Data..."
.venv/bin/python scripts/seed_data.py

echo "[4/4] Verifying Core Data counts..."
.venv/bin/python -c "
from app.core.database import SessionLocal
from app.models.user import User
from app.models.product import Product
db = SessionLocal()
user_count = db.query(User).count()
product_count = db.query(Product).count()
print(f'Verification: {user_count} users, {product_count} products found.')
db.close()
if user_count > 0 and product_count > 0:
    print('FRESH START VERIFICATION PASSED.')
else:
    print('FRESH START VERIFICATION FAILED: Missing seed data.')
    exit(1)
"
