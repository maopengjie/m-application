from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from db.base import Base
from models import SkuProduct, SkuProductAttr, SkuTagRelation, TagDefinition


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


def seed_demo_data() -> None:
    db = SessionLocal()
    try:
        if db.query(SkuProduct).count() > 0:
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
        db.commit()
    finally:
        db.close()
