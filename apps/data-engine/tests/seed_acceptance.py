import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import Base
from app.models.user import User
from app.models.product import Product, ProductSKU, Coupon
from app.core.security import get_password_hash
from app.core.config import get_settings

settings = get_settings()
DB_URL = settings.mysql_dsn
print(f"Connecting to: {DB_URL}")
engine = create_engine(DB_URL)
SessionLocal = sessionmaker(bind=engine)

def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    # Check if admin exists
    admin = db.query(User).filter_by(username="admin").first()
    if not admin:
        print("Creating admin user...")
        admin = User(
            username="admin",
            hashed_password=get_password_hash("password123"),
            real_name="System Admin",
            roles=["admin", "super"],
            is_active=True,
            is_locked=False,
            failed_login_attempts=0
        )
        db.add(admin)
    else:
        print("Resetting admin user status...")
        admin.is_locked = False
        admin.failed_login_attempts = 0
        admin.hashed_password = get_password_hash("password123") # Ensure password is known
    
    # Seed a product if none exists
    if db.query(Product).count() == 0:
        print("Seeding sample product...")
        p = Product(name="iPhone 15 Pro", brand="Apple", category="Phone", main_image="https://example.com/iphone.jpg", rating=4.9)
        db.add(p)
        db.flush()
        
        sku = ProductSKU(
            product_id=p.id, 
            platform="JD", 
            platform_sku_id="JD_IPHONE_15_PRO", 
            title="Apple iPhone 15 Pro 256G",
            price=7999.00,
            original_price=8999.00,
            shop_name="Apple Official Store",
            buy_url="https://item.jd.com/123.html"
        )
        db.add(sku)
        db.flush()
        
        coupon = Coupon(
            sku_id=sku.id,
            title="New Year Global Sale",
            desc="500 off for iPhone",
            type="coupon",
            amount=500.00
        )
        db.add(coupon)
    
    db.commit()
    db.close()
    print("Seeding complete.")

if __name__ == "__main__":
    seed()
