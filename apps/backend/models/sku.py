from sqlalchemy import Column, BigInteger, String, SmallInteger, Text, DateTime, UniqueConstraint, Index, func
from sqlalchemy.orm import relationship, foreign
from db.base import Base, TimestampMixin

class SkuProduct(Base, TimestampMixin):
    __tablename__ = "sku_product"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="自增主键")
    platform = Column(String(32), nullable=False, comment="平台标识（jd, tmall等）")
    sku_id = Column(String(64), nullable=False, comment="原始平台SKU ID")
    product_name = Column(String(512), nullable=False, comment="原始商品全名")
    normalized_name = Column(String(512), nullable=True, comment="归一化后的商品名称")
    brand_name = Column(String(128), nullable=True, comment="品牌名称")
    main_image_url = Column(String(1024), nullable=True, comment="主图URL")
    category_level_1 = Column(String(64), nullable=True, comment="一级类目名称")
    category_level_2 = Column(String(64), nullable=True, comment="二级类目名称")
    category_level_3 = Column(String(64), nullable=True, comment="三级类目名称")
    category_id_3 = Column(BigInteger, nullable=True, comment="原始平台三级类目ID")
    shop_name = Column(String(128), nullable=True, comment="店铺名称")
    product_url = Column(String(1024), nullable=True, comment="商品详情页链接")
    status = Column(SmallInteger, nullable=False, default=1, comment="状态（1:在售, 0:下架, -1:删除）")

    # Relationships
    attributes = relationship(
        "SkuProductAttr",
        back_populates="product",
        cascade="all, delete-orphan",
        primaryjoin=lambda: SkuProduct.id == foreign(SkuProductAttr.sku_product_id),
    )
    tags = relationship(
        "SkuTagRelation",
        back_populates="product",
        cascade="all, delete-orphan",
        primaryjoin=lambda: SkuProduct.id == foreign(SkuTagRelation.sku_product_id),
    )

    __table_args__ = (
        UniqueConstraint("platform", "sku_id", name="uk_platform_sku"),
        Index("idx_brand_name", "brand_name"),
        Index("idx_category_id_3", "category_id_3"),
        Index("idx_normalized_name", "normalized_name"),
        {"comment": "商品主表"}
    )


class SkuProductAttr(Base, TimestampMixin):
    __tablename__ = "sku_product_attr"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="自增主键")
    sku_product_id = Column(BigInteger, nullable=False, comment="关联商品主表ID")
    attr_group = Column(String(64), default="主体", comment="属性分组")
    attr_name = Column(String(64), nullable=False, comment="属性键名")
    attr_value = Column(String(256), nullable=False, comment="属性值")
    attr_unit = Column(String(32), nullable=True, comment="单位")
    source_text = Column(Text, nullable=True, comment="原始解析文本")

    # Relationships
    product = relationship(
        "SkuProduct",
        back_populates="attributes",
        primaryjoin=lambda: foreign(SkuProductAttr.sku_product_id) == SkuProduct.id,
    )

    __table_args__ = (
        Index("idx_sku_product_id", "sku_product_id"),
        Index("idx_attr_kv", "attr_name", "attr_value"),
        Index("idx_sku_attr_name", "sku_product_id", "attr_name"),
        {"comment": "商品属性表"}
    )


class TagDefinition(Base, TimestampMixin):
    __tablename__ = "tag_definition"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="自增主键")
    tag_code = Column(String(64), nullable=False, comment="标签唯一编码")
    tag_name = Column(String(64), nullable=False, comment="标签名称")
    tag_type = Column(String(32), nullable=False, default="SYSTEM", comment="类型（SYSTEM, MANUAL, RULE）")
    description = Column(String(256), nullable=True, comment="说明")

    sku_relations = relationship(
        "SkuTagRelation",
        back_populates="tag",
        primaryjoin=lambda: TagDefinition.id == foreign(SkuTagRelation.tag_id),
    )

    __table_args__ = (
        UniqueConstraint("tag_code", name="uk_tag_code"),
        {"comment": "标签定义表"}
    )


class SkuTagRelation(Base):
    __tablename__ = "sku_tag_relation"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="自增主键")
    sku_product_id = Column(BigInteger, nullable=False, comment="关联商品主表ID")
    tag_id = Column(BigInteger, nullable=False, comment="关联标签定义表ID")
    tag_value = Column(String(128), nullable=True, comment="标签附加值")
    source_type = Column(String(32), nullable=False, default="AUTO", comment="来源（AUTO, MANUAL, RULE）")
    created_at = Column(DateTime, server_default=func.now(), nullable=False, comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False, comment="更新时间")

    # Relationships
    product = relationship(
        "SkuProduct",
        back_populates="tags",
        primaryjoin=lambda: foreign(SkuTagRelation.sku_product_id) == SkuProduct.id,
    )
    tag = relationship(
        "TagDefinition",
        back_populates="sku_relations",
        primaryjoin=lambda: foreign(SkuTagRelation.tag_id) == TagDefinition.id,
    )

    __table_args__ = (
        UniqueConstraint("sku_product_id", "tag_id", name="uk_sku_tag"),
        Index("idx_tag_id", "tag_id"),
        Index("idx_source_type", "source_type"),
        {"comment": "商品标签关联表"}
    )
