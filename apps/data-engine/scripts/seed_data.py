import os
import sys
from datetime import datetime, timedelta

# Add the project root to sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from app.core.database import SessionLocal
from app.models.product import (
    Product,
    ProductSKU,
    PriceHistory,
    Coupon,
    Review,
    RiskScore,
)
from app.models.user import User
from app.core.security import get_password_hash


def seed_data():
    db = SessionLocal()
    try:
        # Check if already seeded
        existing_iphone = db.query(Product).filter(Product.name == "iPhone 15 Pro").first()
        if existing_iphone:
            # Check if users are seeded, if not, seed them
            if not db.query(User).first():
                seed_users(db)
            else:
                print("Database already contains seed data. Skipping...")
            return

        print("Seeding database with mock data...")
        seed_users(db)
        
        # 1. Create a Product
        iphone = Product(
            name="iPhone 15 Pro",
            brand="Apple",
            category="Mobile Phone",
            main_image="https://example.com/iphone15.jpg",
        )
        db.add(iphone)
        db.flush()  # Get ID

        # 2. Create SKUs for JD and Tmall
        jd_sku = ProductSKU(
            product_id=iphone.id,
            platform="JD",
            platform_sku_id="100067931600",
            title="Apple iPhone 15 Pro 256GB 原色钛金属",
            price=7999.00,
            original_price=8999.00,
            shop_name="京东自营",
            is_official=True,
        )
        tmall_sku = ProductSKU(
            product_id=iphone.id,
            platform="Tmall",
            platform_sku_id="735467382910",
            title="Apple/苹果 iPhone 15 Pro 5G智能手机",
            price=7899.00,
            original_price=8999.00,
            shop_name="Apple Store 官方旗舰店",
            is_official=True,
        )
        db.add(jd_sku)
        db.add(tmall_sku)
        db.flush()

        # 3. Add Price History (90 days)
        for i in range(90):
            date = datetime.now() - timedelta(days=i)
            # JD prices with some fluctuation
            jd_price = 7999.00 - (i * 10) if i < 45 else 7549.00 + (i - 45) * 4
            db.add(PriceHistory(sku_id=jd_sku.id, price=jd_price, recorded_at=date))
            # Tmall prices with some fluctuation
            tmall_price = 7899.00 - (i * 8) if i < 60 else 7419.00 + (i - 60) * 6
            db.add(PriceHistory(sku_id=tmall_sku.id, price=tmall_price, recorded_at=date))

        # 4. Add Coupons
        db.add(
            Coupon(
                sku_id=jd_sku.id,
                title="满5000减200",
                desc="Apple产品专享满减券",
                type="满减",
                amount=200.00,
                condition_amount=5000.00,
            )
        )
        db.add(
            Coupon(
                sku_id=tmall_sku.id,
                title="官方旗舰店立减150",
                desc="下单立享优惠",
                type="优惠券",
                amount=150.00,
                condition_amount=0.00,
            )
        )

        # 5. Add Reviews
        db.add(
            Review(
                sku_id=jd_sku.id,
                rating=5,
                content="钛金属手感确实不一样，好评！",
                created_at=datetime.now(),
            )
        )
        db.add(
            Review(
                sku_id=tmall_sku.id,
                rating=4,
                content="物流稍慢，但正品无疑。",
                created_at=datetime.now(),
            )
        )

        # 6. Add Risk Score
        db.add(RiskScore(sku_id=jd_sku.id, score=95, comment_abnormal=False, sales_abnormal=False))
        db.add(RiskScore(sku_id=tmall_sku.id, score=98, comment_abnormal=False, sales_abnormal=False))

        # 7. Add another product for search testing
        macbook = Product(
            name="MacBook Air M3",
            brand="Apple",
            category="Laptop",
            main_image="https://example.com/macbook.jpg"
        )
        db.add(macbook)
        db.flush()
        
        db.add(ProductSKU(
            product_id=macbook.id,
            platform="JD",
            platform_sku_id="100095831600",
            title="Apple MacBook Air 13英寸 M3 8G 256G",
            price=8999.00,
            original_price=8999.00,
            shop_name="京东自营",
            is_official=True
        ))

        db.commit()
        print("Successfully seeded database with mock data.")

    except Exception as e:
        print(f"Error seeding data: {e}")
        db.rollback()
    finally:
        db.close()


def seed_users(db):
    print("Seeding users...")
    users = [
        {
            "username": "vben",
            "password": "123456",
            "real_name": "Vben",
            "roles": ["super"],
            "home_path": "/dashboard",
        },
        {
            "username": "admin",
            "password": "123456",
            "real_name": "Admin",
            "roles": ["admin"],
            "home_path": "/workspace",
        },
        {
            "username": "jack",
            "password": "123456",
            "real_name": "Jack",
            "roles": ["user"],
            "home_path": "/analytics",
        },
    ]
    
    for u_data in users:
        user = User(
            username=u_data["username"],
            hashed_password=get_password_hash(u_data["password"]),
            real_name=u_data["real_name"],
            roles=u_data["roles"],
            home_path=u_data["home_path"],
            is_active=True
        )
        db.add(user)
    db.commit()


if __name__ == "__main__":
    seed_data()
