from sqlalchemy import Column, BigInteger, Integer, String, SmallInteger, Text, DateTime, UniqueConstraint, Index, func
from sqlalchemy.orm import relationship, foreign
from db.base import Base, TimestampMixin

PK_TYPE = BigInteger().with_variant(Integer, "sqlite")

class SkuProduct(Base, TimestampMixin):
    __tablename__ = "sku_product"

    id = Column(PK_TYPE, primary_key=True, autoincrement=True, comment="自增主键")
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
    
    # Price Extremes (denormalized for performance)
    min_price = Column(Integer, nullable=True, comment="历史最低价，单位分")
    max_price = Column(Integer, nullable=True, comment="历史最高价，单位分")
    avg_price = Column(Integer, nullable=True, comment="历史平均价，单位分")
    snapshot_count = Column(Integer, nullable=False, default=0, comment="价格快照总数")

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
    price_snapshots = relationship(
        "SkuPriceSnapshot",
        back_populates="product",
        cascade="all, delete-orphan",
        primaryjoin=lambda: SkuProduct.id == foreign(SkuPriceSnapshot.sku_product_id),
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

    id = Column(PK_TYPE, primary_key=True, autoincrement=True, comment="自增主键")
    sku_product_id = Column(PK_TYPE, nullable=False, comment="关联商品主表ID")
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

    id = Column(PK_TYPE, primary_key=True, autoincrement=True, comment="自增主键")
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

    id = Column(PK_TYPE, primary_key=True, autoincrement=True, comment="自增主键")
    sku_product_id = Column(PK_TYPE, nullable=False, comment="关联商品主表ID")
    tag_id = Column(PK_TYPE, nullable=False, comment="关联标签定义表ID")
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


class SkuPriceSnapshot(Base):
    __tablename__ = "sku_price_snapshot"

    id = Column(PK_TYPE, primary_key=True, autoincrement=True, comment="自增主键")
    sku_product_id = Column(PK_TYPE, nullable=False, comment="关联商品主表ID")
    captured_at = Column(DateTime, nullable=False, comment="抓取时间")
    list_price = Column(Integer, nullable=False, default=0, comment="标价，单位分")
    reduction_amount = Column(Integer, nullable=False, default=0, comment="满减金额，单位分")
    coupon_amount = Column(Integer, nullable=False, default=0, comment="优惠券金额，单位分")
    other_discount_amount = Column(Integer, nullable=False, default=0, comment="其他优惠金额，单位分")
    final_price = Column(Integer, nullable=False, default=0, comment="到手价，单位分")
    promo_text = Column(String(255), nullable=True, comment="促销文案")
    is_anomalous = Column(SmallInteger, nullable=False, default=0, comment="是否异常快照（1:是, 0:否）")
    anomaly_reason = Column(String(255), nullable=True, comment="异常原因")
    created_at = Column(DateTime, server_default=func.now(), nullable=False, comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False, comment="更新时间")

    product = relationship(
        "SkuProduct",
        back_populates="price_snapshots",
        primaryjoin=lambda: foreign(SkuPriceSnapshot.sku_product_id) == SkuProduct.id,
    )

    __table_args__ = (
        Index("idx_price_snapshot_product_capture", "sku_product_id", "captured_at"),
        Index("idx_price_snapshot_capture", "captured_at"),
        Index("idx_price_snapshot_anomaly", "is_anomalous"),
        {"comment": "商品价格时序快照表"}
    )


class CategoryNode(Base, TimestampMixin):
    __tablename__ = "category_node"

    id = Column(PK_TYPE, primary_key=True, autoincrement=True, comment="自增主键")
    platform = Column(String(32), nullable=False, default="jd", comment="平台标识")
    external_id = Column(String(64), nullable=True, comment="原始平台类目ID")
    name = Column(String(128), nullable=False, comment="类目名称")
    level = Column(SmallInteger, nullable=False, comment="层级（1, 2, 3）")
    parent_id = Column(PK_TYPE, nullable=True, comment="父类目ID")
    path = Column(String(256), nullable=True, comment="类目路径（例如 1/2/3）")
    sort_order = Column(Integer, default=0, comment="排序权重")

    __table_args__ = (
        Index("idx_category_platform_level", "platform", "level"),
        Index("idx_category_parent_id", "parent_id"),
        {"comment": "类目树节点表"}
    )


class MappingRule(Base, TimestampMixin):
    __tablename__ = "mapping_rule"

    id = Column(PK_TYPE, primary_key=True, autoincrement=True, comment="自增主键")
    rule_type = Column(String(32), nullable=False, default="KEYWORD", comment="规则类型（KEYWORD, REGEX）")
    platform = Column(String(32), nullable=True, comment="适用平台（空表示全平台）")
    category_id = Column(PK_TYPE, nullable=True, comment="适用类目ID")
    pattern = Column(String(256), nullable=False, comment="匹配模式/关键字")
    unified_label = Column(String(128), nullable=False, comment="归一化后的标签名称")
    is_active = Column(SmallInteger, default=1, comment="是否启用（1:启用, 0:禁用）")
    priority = Column(Integer, default=0, comment="优先级")

    __table_args__ = (
        Index("idx_mapping_rule_pattern", "pattern"),
        {"comment": "商品名称映射规则表"}
    )


class SkuComparison(Base, TimestampMixin):
    __tablename__ = "sku_comparison"

    id = Column(PK_TYPE, primary_key=True, autoincrement=True, comment="自增主键")
    master_sku_id = Column(PK_TYPE, nullable=False, comment="主SKU ID（通常是基准SKU）")
    linked_sku_id = Column(PK_TYPE, nullable=False, comment="关联SKU ID（对比SKU）")
    match_score = Column(Integer, nullable=True, comment="匹配度分数（0-100）")
    match_type = Column(String(32), default="MANUAL", comment="匹配方式（MANUAL, AUTO）")
    status = Column(SmallInteger, default=1, comment="状态（1:高置信, 0:待人工确认, -1:低分过滤）")

    __table_args__ = (
        UniqueConstraint("master_sku_id", "linked_sku_id", name="uk_sku_comparison"),
        Index("idx_linked_sku_id", "linked_sku_id"),
        {"comment": "商品对照/竞品匹配表"}
    )


class ScrapeTaskRun(Base, TimestampMixin):
    __tablename__ = "scrape_task_run"

    id = Column(PK_TYPE, primary_key=True, autoincrement=True, comment="自增主键")
    task_id = Column(String(128), nullable=True, comment="异步任务ID")
    task_name = Column(String(64), nullable=False, comment="任务名称")
    trigger_source = Column(String(32), nullable=False, default="MANUAL", comment="触发来源（MANUAL, SCHEDULED）")
    platform = Column(String(32), nullable=True, comment="平台标识")
    requested_limit = Column(Integer, nullable=True, comment="批量任务请求数量")
    requested_url = Column(String(1024), nullable=True, comment="单商品抓取链接")
    status = Column(String(32), nullable=False, default="PENDING", comment="任务状态")
    processed_count = Column(Integer, nullable=False, default=0, comment="处理数")
    success_count = Column(Integer, nullable=False, default=0, comment="成功数")
    failure_count = Column(Integer, nullable=False, default=0, comment="失败数")
    started_at = Column(DateTime, nullable=True, comment="开始执行时间")
    finished_at = Column(DateTime, nullable=True, comment="结束执行时间")
    summary_message = Column(String(512), nullable=True, comment="任务摘要")
    error_message = Column(Text, nullable=True, comment="错误详情")
    failed_items_json = Column(Text, nullable=True, comment="失败明细JSON")

    __table_args__ = (
        UniqueConstraint("task_id", name="uk_scrape_task_run_task_id"),
        Index("idx_scrape_task_run_status", "status"),
        Index("idx_scrape_task_run_created_at", "created_at"),
        {"comment": "抓取任务执行记录表"}
    )


class EtlLog(Base, TimestampMixin):
    __tablename__ = "etl_log"

    id = Column(PK_TYPE, primary_key=True, autoincrement=True, comment="自增主键")
    event_type = Column(String(32), nullable=False, comment="事件类型（CLEANING, ANOMALY, SYSTEM）")
    platform = Column(String(32), nullable=True, comment="平台标识")
    sku_id = Column(String(64), nullable=True, comment="原始SKU ID")
    product_id = Column(PK_TYPE, nullable=True, comment="关联商品ID")
    field_name = Column(String(64), nullable=True, comment="处理字段名")
    original_value = Column(Text, nullable=True, comment="原始值")
    cleaned_value = Column(Text, nullable=True, comment="清洗后的值")
    status = Column(SmallInteger, default=1, comment="状态（1:已处理, 0:待人工校验, -1:已忽略）")
    message = Column(String(512), nullable=True, comment="日志消息")

    __table_args__ = (
        Index("idx_etl_event_type", "event_type"),
        Index("idx_etl_sku_id", "sku_id"),
        {"comment": "数据清洗与处理日志表"}
    )


class AnomalyAlert(Base, TimestampMixin):
    __tablename__ = "anomaly_alert"

    id = Column(PK_TYPE, primary_key=True, autoincrement=True, comment="自增主键")
    alert_type = Column(String(32), nullable=False, comment="报警类型（PRICE_BUG, STOCK_BUG, DATA_MISSING, SCRAPE_FAILURE）")
    platform = Column(String(32), nullable=False, comment="平台标识")
    sku_id = Column(String(64), nullable=False, comment="原始SKU ID")
    product_id = Column(PK_TYPE, nullable=True, comment="关联商品ID")
    alert_value = Column(String(256), nullable=False, comment="异常值（如 0.1 元）")
    threshold = Column(String(256), nullable=True, comment="触发阈值")
    is_verified = Column(SmallInteger, default=0, comment="是否已人工核实（1:是, 0:否）")
    verification_result = Column(String(256), nullable=True, comment="核实结果")
    message = Column(String(512), nullable=True, comment="异常消息")

    __table_args__ = (
        Index("idx_anomaly_sku_id", "sku_id"),
        Index("idx_anomaly_type", "alert_type"),
        {"comment": "异常报警记录表"}
    )


class CrawlEfficiency(Base):
    __tablename__ = "crawl_efficiency"

    id = Column(PK_TYPE, primary_key=True, autoincrement=True, comment="自增主键")
    platform = Column(String(32), nullable=False, comment="平台标识")
    target_api = Column(String(128), nullable=False, comment="抓取接口名")
    response_time_ms = Column(Integer, nullable=False, comment="响应耗时(ms)")
    status_code = Column(Integer, nullable=False, comment="HTTP状态码")
    captured_at = Column(DateTime, server_default=func.now(), nullable=False, comment="抓取时间")

    __table_args__ = (
        Index("idx_crawl_platform_time", "platform", "captured_at"),
        {"comment": "采集效率监控表"}
    )
