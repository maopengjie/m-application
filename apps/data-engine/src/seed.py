import os
import sys
from datetime import datetime, timedelta
import random

# Add project root to sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from app.core.database import SessionLocal, Base, engine
from app.models.user import User
from app.models.product import Product, ProductSKU, PriceHistory, Review, RiskScore, Coupon
from app.core.security import get_password_hash

def seed():
    print("Seed process started...")
    db = SessionLocal()
    
    # 1. Create Admin User
    admin = db.query(User).filter(User.username == "admin").first()
    if not admin:
        print("Creating admin user...")
        admin = User(
            username="admin",
            hashed_password=get_password_hash("admin123"),
            real_name="System Admin",
            roles=["admin"],
            is_active=True
        )
        db.add(admin)
        db.flush()
    
    # 2. Create Products
    products_to_create = [
        ("iPhone 15 Pro", "Apple", "Smartphones", "https://img14.360buyimg.com/n1/jfs/t1/116909/25/44477/23249/66960d75F79bda662/01c402170364f33b.jpg"),
        ("RTX 4090", "NVIDIA", "GPU", "https://img14.360buyimg.com/n1/jfs/t1/139265/29/42557/74039/65796c9dF53d9e802/52775f0a6311de6e.jpg"),
        ("Sony WH-1000XM5", "Sony", "Audio", "https://img14.360buyimg.com/n1/jfs/t1/133036/20/38944/32688/65c490a6Fd6e915f1/3d3d1f435ce08709.jpg")
    ]
    
    platforms = ["JD", "Tmall", "Pinduoduo"]
    
    for name, brand, cat, img in products_to_create:
        p = db.query(Product).filter(Product.name == name).first()
        if not p:
            print(f"Creating product: {name}")
            p = Product(name=name, brand=brand, category=cat, main_image=img)
            db.add(p)
            db.flush()
            
            # Create SKUs for each platform
            base_price = random.uniform(2000, 8000)
            for platform in platforms:
                sku = ProductSKU(
                    product_id=p.id,
                    platform=platform,
                    platform_sku_id=f"sku_{p.id}_{platform}",
                    title=f"{name} [{platform}]",
                    price=base_price * random.uniform(0.9, 1.1),
                    original_price=base_price * 1.2,
                    shop_name=f"{platform} Official Store",
                    is_official=True,
                    buy_url="https://www.jd.com"
                )
                db.add(sku)
                db.flush()
                
                # Create Price History for last 30 days
                for i in range(30):
                    hist = PriceHistory(
                        sku_id=sku.id,
                        price=sku.price * random.uniform(0.95, 1.05),
                        recorded_at=datetime.utcnow() - timedelta(days=i)
                    )
                    db.add(hist)
                
                # Create Risk Score
                risk = RiskScore(
                    sku_id=sku.id,
                    score=random.randint(30, 95),
                    comment_abnormal=random.choice([True, False, False, False]),
                    sales_abnormal=random.choice([True, False, False, False]),
                    updated_at=datetime.utcnow()
                )
                db.add(risk)

    # 3. Create Coupons
    print("Creating coupons...")
    # Get some valid SKUs to link coupons to
    skus = db.query(ProductSKU).limit(3).all()
    coupons_list = [
        {"title": "全场通用满减券", "amount": 20, "condition_amount": 200, "type": "JD_PLATFORM", "sku_id": skus[0].id},
        {"title": "电子产品专项券", "amount": 100, "condition_amount": 1000, "type": "TMALL_CATEGORY", "sku_id": skus[1].id},
        {"title": "百亿补贴无门槛", "amount": 5, "condition_amount": 0, "type": "PDD_SUBSIDY", "sku_id": skus[2].id}
    ]
    for c_data in coupons_list:
        db.add(Coupon(**c_data))

    # 4. Create Crawl Tasks
    print("Creating crawl tasks...")
    from app.models.task import CrawlTask
    db.add(CrawlTask(
        task_type="price_update",
        status="success",
        total_count=100,
        success_count=98,
        failed_count=2,
        start_time=datetime.utcnow() - timedelta(hours=2)
    ))
    db.add(CrawlTask(
        task_type="product_discovery",
        status="running",
        total_count=50,
        success_count=12,
        failed_count=0,
        start_time=datetime.utcnow() - timedelta(minutes=15)
    ))
    
    db.commit()
    db.close()
    print("Seed process completed successfully!")

if __name__ == "__main__":
    seed()
