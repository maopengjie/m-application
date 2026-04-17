import sys
import os
from datetime import datetime, timedelta, timezone
from decimal import Decimal

# Add the parent directory to sys.path to allow imports from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal, engine
from app.models.product import Product, ProductSKU, PriceHistory, Coupon, RiskScore, Review
from app.models.user import User

def seed_real_data():
    db = SessionLocal()
    try:
        print("Seeding realistic data for final acceptance...")
        
        # 1. Clear existing non-user data (keep users for login)
        db.query(PriceHistory).delete()
        db.query(Coupon).delete()
        db.query(RiskScore).delete()
        db.query(Review).delete()
        db.query(ProductSKU).delete()
        db.query(Product).delete()
        db.commit()

        now = datetime.now(timezone.utc)

        # --- PRODUCT 1: iPhone 15 Pro ---
        p1 = Product(
            name="Apple iPhone 15 Pro (A3102) 256GB 原色钛金属",
            brand="Apple",
            category="手机",
            main_image="https://img14.360buyimg.com/n1/s450x450_jfs/t1/166318/3/43048/57661/660a6e03F5409cb34/4d1b7b7529432f8a.jpg",
            rating=4.9
        )
        db.add(p1); db.flush()

        # SKU 1: JD Official
        sku1_jd = ProductSKU(
            product_id=p1.id,
            platform="JD",
            platform_sku_id="100063910600",
            title="Apple iPhone 15 Pro 256GB 原色钛金属 支持移动联通电信5G",
            price=7999.00,
            original_price=8999.00,
            shop_name="京东自营Apple旗舰店",
            is_official=True,
            buy_url="https://item.jd.com/100063910600.html"
        )
        db.add(sku1_jd); db.flush()

        # History for JD (Slow decline)
        for i in range(30):
            price = 8999.00 - (i * 33.3)
            db.add(PriceHistory(sku_id=sku1_jd.id, price=price, recorded_at=now - timedelta(days=30-i)))

        # SKU 2: Tmall
        sku1_tmall = ProductSKU(
            product_id=p1.id,
            platform="Tmall",
            platform_sku_id="735829102",
            title="【官方直营】Apple/苹果 iPhone 15 Pro 256G 5G智能手机",
            price=8199.00,
            original_price=8999.00,
            shop_name="Apple Store官方旗舰店",
            is_official=True,
            buy_url="https://detail.tmall.com/item.htm?id=735829102"
        )
        db.add(sku1_tmall); db.flush()

        # SKU 3: Pinduoduo (Risk High)
        sku1_pdd = ProductSKU(
            product_id=p1.id,
            platform="PDD",
            platform_sku_id="pdd_ip15p_256",
            title="【补贴后¥7499】全新未拆封 iPhone 15 Pro 256GB 顺丰包邮",
            price=7499.00,
            original_price=8999.00,
            shop_name="远航数码海外直营",
            is_official=False,
            buy_url="https://mobile.yangkeduo.com/..."
        )
        db.add(sku1_pdd); db.flush()

        # Risk for PDD
        db.add(RiskScore(
            sku_id=sku1_pdd.id,
            score=65,
            comment_abnormal=True,
            sales_abnormal=True,
            price_abnormal=True,
            details_json='{"reason": "价格显著低于官方标价(>15%), 店铺非授权代理, 评价中存在假货反馈"}'
        ))

        # Coupons for JD
        db.add(Coupon(sku_id=sku1_jd.id, title="满7000减500", amount=500.0, condition_amount=7000.0, type="JD_COUPON"))
        db.add(Coupon(sku_id=sku1_jd.id, title="Plus会员专享95折", amount=400.0, type="PLUS_MEMBER"))

        # --- PRODUCT 2: Sony WH-1000XM5 ---
        p2 = Product(
            name="索尼（SONY）WH-1000XM5 头戴式无线降噪蓝牙耳机",
            brand="Sony",
            category="耳机",
            main_image="https://img14.360buyimg.com/n1/s450x450_jfs/t1/116812/32/31336/69542/63896593F380757a7/8051780f2d4f2f4e.jpg",
            rating=4.8
        )
        db.add(p2); db.flush()

        sku2_jd = ProductSKU(
            product_id=p2.id,
            platform="JD",
            platform_sku_id="100021678129",
            title="索尼 SONY WH-1000XM5 铂金银 智能AI旗舰降噪耳机",
            price=2299.00,
            original_price=2999.00,
            shop_name="索尼京东自营旗舰店",
            is_official=True
        )
        db.add(sku2_jd); db.flush()
        
        # Flash sale profile
        for i in range(15):
            p = 2999.0 if i < 10 else 2299.0
            db.add(PriceHistory(sku_id=sku2_jd.id, price=p, recorded_at=now - timedelta(days=15-i)))

        db.commit()
        print("Successfully seeded real-world data profiles.")

    except Exception as e:
        db.rollback()
        print(f"Failed to seed real data: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_real_data()
