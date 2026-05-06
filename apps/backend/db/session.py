from __future__ import annotations

import os
from pathlib import Path
from datetime import datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session, sessionmaker

from db.base import Base
from models import SkuPriceSnapshot, SkuProduct, SkuProductAttr, SkuTagRelation, TagDefinition, EtlLog, AnomalyAlert, CrawlEfficiency, ScrapeTaskRun


DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "app.db"


def _build_database_url() -> str:
    configured = os.getenv("DATABASE_URL")
    if configured:
        return configured

    DEFAULT_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{DEFAULT_DB_PATH}"


DATABASE_URL = _build_database_url()
IS_SQLITE = DATABASE_URL.startswith("sqlite")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if IS_SQLITE else {},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    _run_sqlite_compat_migrations()


def _run_sqlite_compat_migrations() -> None:
    if not IS_SQLITE:
        return

    inspector = inspect(engine)
    if "scrape_task_run" in inspector.get_table_names():
        columns = {column["name"] for column in inspector.get_columns("scrape_task_run")}
        if "failed_items_json" not in columns:
            with engine.begin() as connection:
                connection.execute(
                    text("ALTER TABLE scrape_task_run ADD COLUMN failed_items_json TEXT")
                )

    if "sku_price_snapshot" in inspector.get_table_names():
        columns = {column["name"] for column in inspector.get_columns("sku_price_snapshot")}
        if "is_anomalous" not in columns:
            with engine.begin() as connection:
                connection.execute(
                    text("ALTER TABLE sku_price_snapshot ADD COLUMN is_anomalous SMALLINT DEFAULT 0")
                )
        if "anomaly_reason" not in columns:
            with engine.begin() as connection:
                connection.execute(
                    text("ALTER TABLE sku_price_snapshot ADD COLUMN anomaly_reason VARCHAR(255)")
                )


def seed_demo_data() -> None:
    db = SessionLocal()
    try:
        if db.query(SkuProduct).count() > 0:
            _ensure_recent_demo_activity(db)
            return

        tag_self = TagDefinition(
            tag_code="JD_SELF_OPERATED",
            tag_name="京东自营",
            tag_type="SYSTEM",
            description="平台自营商品",
        )
        tag_subsidy = TagDefinition(
            tag_code="HUNDRED_BILLION_SUBSIDY",
            tag_name="百亿补贴",
            tag_type="RULE",
            description="命中百亿补贴活动",
        )
        tag_plus = TagDefinition(
            tag_code="PLUS_EXCLUSIVE",
            tag_name="PLUS专享",
            tag_type="RULE",
            description="会员专享价格或权益",
        )
        db.add_all([tag_self, tag_subsidy, tag_plus])
        db.flush()

        products = [
            SkuProduct(
                platform="jd",
                sku_id="100058155719",
                product_name="Apple iPhone 15 Pro Max 256GB 黑色钛金属 5G手机",
                normalized_name="iPhone 15 Pro Max 256GB 黑色钛金属",
                brand_name="Apple",
                main_image_url="https://img14.360buyimg.com/n1/jfs/t1/demo/iphone15pm.jpg",
                category_level_1="手机通讯",
                category_level_2="手机",
                category_level_3="智能手机",
                category_id_3=9987,
                shop_name="Apple产品京东自营旗舰店",
                product_url="https://item.jd.com/100058155719.html",
                status=1,
            ),
            SkuProduct(
                platform="jd",
                sku_id="100081422201",
                product_name="小米 14 16GB+512GB 岩石青 徕卡影像旗舰手机",
                normalized_name="小米14 16GB+512GB 岩石青",
                brand_name="Xiaomi",
                main_image_url="https://img14.360buyimg.com/n1/jfs/t1/demo/xiaomi14.jpg",
                category_level_1="手机通讯",
                category_level_2="手机",
                category_level_3="智能手机",
                category_id_3=9987,
                shop_name="小米京东自营旗舰店",
                product_url="https://item.jd.com/100081422201.html",
                status=1,
            ),
            SkuProduct(
                platform="jd",
                sku_id="100046307503",
                product_name="联想拯救者 Y9000P 16英寸 i9 RTX4060 电竞游戏本",
                normalized_name="联想拯救者 Y9000P i9 RTX4060",
                brand_name="Lenovo",
                main_image_url="https://img14.360buyimg.com/n1/jfs/t1/demo/y9000p.jpg",
                category_level_1="电脑办公",
                category_level_2="电脑整机",
                category_level_3="游戏本",
                category_id_3=670,
                shop_name="联想京东自营旗舰店",
                product_url="https://item.jd.com/100046307503.html",
                status=1,
            ),
        ]
        db.add_all(products)
        db.flush()

        attrs = [
            SkuProductAttr(sku_product_id=products[0].id, attr_group="主体", attr_name="机身颜色", attr_value="黑色钛金属"),
            SkuProductAttr(sku_product_id=products[0].id, attr_group="存储", attr_name="机身内存", attr_value="256", attr_unit="GB"),
            SkuProductAttr(sku_product_id=products[0].id, attr_group="芯片", attr_name="处理器", attr_value="A17 Pro"),
            SkuProductAttr(sku_product_id=products[1].id, attr_group="存储", attr_name="运行内存", attr_value="16", attr_unit="GB"),
            SkuProductAttr(sku_product_id=products[1].id, attr_group="存储", attr_name="机身存储", attr_value="512", attr_unit="GB"),
            SkuProductAttr(sku_product_id=products[1].id, attr_group="芯片", attr_name="处理器", attr_value="骁龙8 Gen3"),
            SkuProductAttr(sku_product_id=products[2].id, attr_group="处理器", attr_name="CPU型号", attr_value="Intel Core i9"),
            SkuProductAttr(sku_product_id=products[2].id, attr_group="显卡", attr_name="显卡型号", attr_value="RTX 4060"),
            SkuProductAttr(sku_product_id=products[2].id, attr_group="屏幕", attr_name="屏幕尺寸", attr_value="16", attr_unit="英寸"),
        ]
        db.add_all(attrs)

        relations = [
            SkuTagRelation(sku_product_id=products[0].id, tag_id=tag_self.id, source_type="AUTO"),
            SkuTagRelation(sku_product_id=products[0].id, tag_id=tag_plus.id, source_type="RULE"),
            SkuTagRelation(sku_product_id=products[1].id, tag_id=tag_self.id, source_type="AUTO"),
            SkuTagRelation(sku_product_id=products[1].id, tag_id=tag_subsidy.id, source_type="RULE", tag_value="直降500元"),
            SkuTagRelation(sku_product_id=products[2].id, tag_id=tag_self.id, source_type="AUTO"),
        ]
        db.add_all(relations)
        db.flush()

        # Seed ETL Logs
        etl_logs = [
            EtlLog(
                event_type="CLEANING",
                platform="jd",
                sku_id="100058155719",
                product_id=products[0].id,
                field_name="product_name",
                original_value="【4月狂欢】Apple iPhone 15 Pro Max 256GB 黑色钛金属 直播间专享",
                cleaned_value="Apple iPhone 15 Pro Max 256GB 黑色钛金属",
                message="Filtered slogans: 【4月狂欢】, 直播间专享"
            ),
            EtlLog(
                event_type="CLEANING",
                platform="jd",
                sku_id="100081422201",
                product_id=products[1].id,
                field_name="product_name",
                original_value="限时秒杀！小米 14 16GB+512GB 岩石青 领券立减200",
                cleaned_value="小米 14 16GB+512GB 岩石青",
                message="Filtered slogans: 限时秒杀！, 领券立减200"
            )
        ]
        db.add_all(etl_logs)

        # Seed Anomaly Alerts
        anomalies = [
            AnomalyAlert(
                alert_type="PRICE_BUG",
                platform="jd",
                sku_id="100058155719",
                product_id=products[0].id,
                alert_value="0.10元",
                threshold="1.00元",
                message="Possible BUG price detected: 0.10 RMB",
                is_verified=0
            ),
            AnomalyAlert(
                alert_type="PRICE_BUG",
                platform="jd",
                sku_id="100081422201",
                product_id=products[1].id,
                alert_value="0.99元",
                threshold="1.00元",
                message="Possible BUG price detected: 0.99 RMB",
                is_verified=1,
                verification_result="Confirmed BUG, fixed."
            )
        ]
        db.add_all(anomalies)

        # Seed Crawl Efficiency
        import random
        from datetime import datetime, timedelta
        efficiency_data = []
        now = datetime.now()
        for i in range(24):
            time = now - timedelta(hours=i)
            efficiency_data.append(CrawlEfficiency(
                platform="jd",
                target_api="item.jd.com/detail",
                response_time_ms=random.randint(200, 800),
                status_code=200,
                captured_at=time
            ))
        db.add_all(efficiency_data)

        # Seed Price Snapshots
        from datetime import datetime, timedelta
        price_snapshots = []
        now = datetime.now()
        
        # Product 0: iPhone 15 Pro Max
        prices_0 = [999900, 999900, 949900, 949900, 899900, 899900, 949900]
        promos_0 = ["", "", "满减500", "满减500", "券后价", "券后价", ""]
        for i, price in enumerate(prices_0):
            snap = SkuPriceSnapshot(
                sku_product_id=products[0].id,
                captured_at=now - timedelta(days=7-i),
                list_price=999900,
                final_price=price,
                reduction_amount=50000 if "满减" in promos_0[i] else 0,
                coupon_amount=100000 if "券" in promos_0[i] else 0,
                promo_text=promos_0[i] or None
            )
            price_snapshots.append(snap)
            
        # Product 1: Xiaomi 14
        prices_1 = [429900, 429900, 399900, 399900, 399900, 429900, 429900]
        for i, price in enumerate(prices_1):
            snap = SkuPriceSnapshot(
                sku_product_id=products[1].id,
                captured_at=now - timedelta(days=7-i),
                list_price=429900,
                final_price=price,
                reduction_amount=30000 if price < 429900 else 0,
                promo_text="限时秒杀" if price < 429900 else None
            )
            price_snapshots.append(snap)
            
        # Product 2: Legion Y9000P
        prices_2 = [999900, 999900, 999900, 999900, 999900, 999900, 999900]
        for i, price in enumerate(prices_2):
            snap = SkuPriceSnapshot(
                sku_product_id=products[2].id,
                captured_at=now - timedelta(days=7-i),
                list_price=999900,
                final_price=price
            )
            price_snapshots.append(snap)
            
        db.add_all(price_snapshots)
        db.flush()
        
        # Update product cached fields
        for p in products:
            snaps = [s for s in price_snapshots if s.sku_product_id == p.id]
            if snaps:
                final_prices = [s.final_price for s in snaps]
                p.min_price = min(final_prices)
                p.max_price = max(final_prices)
                p.avg_price = int(sum(final_prices) / len(final_prices))
                p.snapshot_count = len(snaps)

        _ensure_recent_demo_activity(db)
        db.commit()
    finally:
        db.close()


def _round_to_five_minutes(value: datetime) -> datetime:
    rounded = value.replace(second=0, microsecond=0)
    return rounded - timedelta(minutes=rounded.minute % 5)


def _build_recent_price_plan(product: SkuProduct) -> list[tuple[int, int, int, str | None]]:
    base = product.max_price or product.avg_price or product.min_price or 0
    floor = product.min_price or base

    if product.platform == "jd" and "iPhone" in (product.product_name or ""):
        return [
            (55, base, max(base - 20_000, floor), "晚间满减"),
            (30, base, max(base - 40_000, floor), "PLUS 券"),
            (0, base, max(base - 70_000, floor), "百亿补贴叠券"),
        ]
    if product.platform == "jd" and "小米" in (product.product_name or ""):
        return [
            (55, base, max(base - 10_000, floor), "秒杀预热"),
            (30, base, max(base - 20_000, floor), "限时秒杀"),
            (0, base, max(base - 30_000, floor), "直播间券后"),
        ]
    if product.platform == "jd":
        return [
            (55, base, base, None),
            (30, base, max(base - 5_000, floor), "店铺满减"),
            (0, base, max(base - 10_000, floor), "晒单返券"),
        ]
    if product.platform == "tmall":
        return [
            (55, base, max(base - 8_000, floor), "88VIP 预估"),
            (30, base, max(base - 15_000, floor), "官方立减"),
            (0, base, max(base - 25_000, floor), "跨店满减"),
        ]
    return [
        (55, base, max(base - 12_000, floor), "平台补贴"),
        (30, base, max(base - 20_000, floor), "百亿补贴"),
        (0, base, max(base - 35_000, floor), "限时补贴"),
    ]


def _ensure_recent_demo_activity(db: Session) -> None:
    now = datetime.now()
    bucket_end = _round_to_five_minutes(now)
    buckets = [bucket_end - timedelta(minutes=offset) for offset in (55, 30, 0)]

    products = (
        db.query(SkuProduct)
        .filter(SkuProduct.status == 1)
        .order_by(SkuProduct.id.asc())
        .limit(6)
        .all()
    )

    inserted_snapshot = False
    for product in products:
        recent_count = (
            db.query(SkuPriceSnapshot)
            .filter(
                SkuPriceSnapshot.sku_product_id == product.id,
                SkuPriceSnapshot.captured_at >= bucket_end - timedelta(hours=1),
            )
            .count()
        )
        if recent_count >= 3:
            continue

        plan = _build_recent_price_plan(product)
        for captured_at, (_, list_price, final_price, promo_text) in zip(buckets, plan, strict=False):
            exists = (
                db.query(SkuPriceSnapshot)
                .filter(
                    SkuPriceSnapshot.sku_product_id == product.id,
                    SkuPriceSnapshot.captured_at == captured_at,
                )
                .first()
            )
            if exists:
                continue

            reduction_amount = max(list_price - final_price, 0)
            db.add(
                SkuPriceSnapshot(
                    sku_product_id=product.id,
                    captured_at=captured_at,
                    list_price=list_price,
                    reduction_amount=reduction_amount,
                    coupon_amount=0,
                    other_discount_amount=0,
                    final_price=final_price,
                    promo_text=promo_text,
                )
            )
            inserted_snapshot = True

    if inserted_snapshot:
        db.flush()
        for product in products:
            stats = (
                db.query(
                    SkuPriceSnapshot.final_price,
                )
                .filter(SkuPriceSnapshot.sku_product_id == product.id)
                .all()
            )
            if not stats:
                continue
            final_prices = [item.final_price for item in stats]
            product.min_price = min(final_prices)
            product.max_price = max(final_prices)
            product.avg_price = int(sum(final_prices) / len(final_prices))
            product.snapshot_count = len(final_prices)

    existing_efficiency = {
        item.captured_at
        for item in db.query(CrawlEfficiency)
        .filter(CrawlEfficiency.captured_at >= bucket_end - timedelta(hours=1))
        .all()
    }
    efficiency_plan = [
        (55, 420, 200),
        (50, 410, 200),
        (45, 460, 200),
        (40, 480, 200),
        (35, 520, 200),
        (30, 505, 200),
        (25, 470, 200),
        (20, 450, 200),
        (15, 430, 200),
        (10, 440, 200),
        (5, 390, 200),
        (0, 405, 200),
    ]
    for minute_offset, response_time_ms, status_code in efficiency_plan:
        captured_at = bucket_end - timedelta(minutes=minute_offset)
        if captured_at in existing_efficiency:
            continue
        db.add(
            CrawlEfficiency(
                platform="jd",
                target_api="item.jd.com/detail",
                response_time_ms=response_time_ms,
                status_code=status_code,
                captured_at=captured_at,
            )
        )

    db.commit()
