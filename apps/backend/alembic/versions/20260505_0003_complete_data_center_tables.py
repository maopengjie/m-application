"""complete data center tables

Revision ID: 20260505_0003
Revises: 9eb34adc420a
Create Date: 2026-05-05 00:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260505_0003"
down_revision: Union[str, Sequence[str], None] = "9eb34adc420a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


PK_TYPE = sa.BigInteger().with_variant(sa.Integer(), "sqlite")


def _table_exists(table_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return table_name in inspector.get_table_names()


def _column_exists(table_name: str, column_name: str) -> bool:
    if not _table_exists(table_name):
        return False
    inspector = sa.inspect(op.get_bind())
    return column_name in {column["name"] for column in inspector.get_columns(table_name)}


def _index_exists(table_name: str, index_name: str) -> bool:
    if not _table_exists(table_name):
        return False
    inspector = sa.inspect(op.get_bind())
    return index_name in {index["name"] for index in inspector.get_indexes(table_name)}


def _add_column_if_missing(table_name: str, column: sa.Column) -> None:
    if not _column_exists(table_name, column.name):
        op.add_column(table_name, column)


def _create_index_if_missing(index_name: str, table_name: str, columns: list[str]) -> None:
    if not _index_exists(table_name, index_name):
        op.create_index(index_name, table_name, columns)


def upgrade() -> None:
    _add_column_if_missing(
        "sku_product",
        sa.Column("min_price", sa.Integer(), nullable=True, comment="历史最低价，单位分"),
    )
    _add_column_if_missing(
        "sku_product",
        sa.Column("max_price", sa.Integer(), nullable=True, comment="历史最高价，单位分"),
    )
    _add_column_if_missing(
        "sku_product",
        sa.Column("avg_price", sa.Integer(), nullable=True, comment="历史平均价，单位分"),
    )
    _add_column_if_missing(
        "sku_product",
        sa.Column(
            "snapshot_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
            comment="价格快照总数",
        ),
    )
    _add_column_if_missing(
        "sku_price_snapshot",
        sa.Column(
            "is_anomalous",
            sa.SmallInteger(),
            nullable=False,
            server_default="0",
            comment="是否异常快照（1:是, 0:否）",
        ),
    )
    _add_column_if_missing(
        "sku_price_snapshot",
        sa.Column("anomaly_reason", sa.String(255), nullable=True, comment="异常原因"),
    )
    _create_index_if_missing("idx_price_snapshot_anomaly", "sku_price_snapshot", ["is_anomalous"])

    if not _table_exists("category_node"):
        op.create_table(
            "category_node",
            sa.Column("id", PK_TYPE, primary_key=True, autoincrement=True, comment="自增主键"),
            sa.Column("platform", sa.String(32), nullable=False, server_default="jd", comment="平台标识"),
            sa.Column("external_id", sa.String(64), nullable=True, comment="原始平台类目ID"),
            sa.Column("name", sa.String(128), nullable=False, comment="类目名称"),
            sa.Column("level", sa.SmallInteger(), nullable=False, comment="层级（1, 2, 3）"),
            sa.Column("parent_id", PK_TYPE, nullable=True, comment="父类目ID"),
            sa.Column("path", sa.String(256), nullable=True, comment="类目路径（例如 1/2/3）"),
            sa.Column("sort_order", sa.Integer(), nullable=True, server_default="0", comment="排序权重"),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False, comment="创建时间"),
            sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False, comment="更新时间"),
            comment="类目树节点表",
        )
    _create_index_if_missing("idx_category_platform_level", "category_node", ["platform", "level"])
    _create_index_if_missing("idx_category_parent_id", "category_node", ["parent_id"])

    if not _table_exists("mapping_rule"):
        op.create_table(
            "mapping_rule",
            sa.Column("id", PK_TYPE, primary_key=True, autoincrement=True, comment="自增主键"),
            sa.Column("rule_type", sa.String(32), nullable=False, server_default="KEYWORD", comment="规则类型（KEYWORD, REGEX）"),
            sa.Column("platform", sa.String(32), nullable=True, comment="适用平台（空表示全平台）"),
            sa.Column("category_id", PK_TYPE, nullable=True, comment="适用类目ID"),
            sa.Column("pattern", sa.String(256), nullable=False, comment="匹配模式/关键字"),
            sa.Column("unified_label", sa.String(128), nullable=False, comment="归一化后的标签名称"),
            sa.Column("is_active", sa.SmallInteger(), nullable=True, server_default="1", comment="是否启用（1:启用, 0:禁用）"),
            sa.Column("priority", sa.Integer(), nullable=True, server_default="0", comment="优先级"),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False, comment="创建时间"),
            sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False, comment="更新时间"),
            comment="商品名称映射规则表",
        )
    _create_index_if_missing("idx_mapping_rule_pattern", "mapping_rule", ["pattern"])

    if not _table_exists("sku_comparison"):
        op.create_table(
            "sku_comparison",
            sa.Column("id", PK_TYPE, primary_key=True, autoincrement=True, comment="自增主键"),
            sa.Column("master_sku_id", PK_TYPE, nullable=False, comment="主SKU ID（通常是基准SKU）"),
            sa.Column("linked_sku_id", PK_TYPE, nullable=False, comment="关联SKU ID（对比SKU）"),
            sa.Column("match_score", sa.Integer(), nullable=True, comment="匹配度分数（0-100）"),
            sa.Column("match_type", sa.String(32), nullable=True, server_default="MANUAL", comment="匹配方式（MANUAL, AUTO）"),
            sa.Column("status", sa.SmallInteger(), nullable=True, server_default="1", comment="状态（1:高置信, 0:待人工确认, -1:低分过滤）"),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False, comment="创建时间"),
            sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False, comment="更新时间"),
            sa.UniqueConstraint("master_sku_id", "linked_sku_id", name="uk_sku_comparison"),
            comment="商品对照/竞品匹配表",
        )
    _create_index_if_missing("idx_linked_sku_id", "sku_comparison", ["linked_sku_id"])

    if not _table_exists("scrape_task_run"):
        op.create_table(
            "scrape_task_run",
            sa.Column("id", PK_TYPE, primary_key=True, autoincrement=True, comment="自增主键"),
            sa.Column("task_id", sa.String(128), nullable=True, comment="异步任务ID"),
            sa.Column("task_name", sa.String(64), nullable=False, comment="任务名称"),
            sa.Column("trigger_source", sa.String(32), nullable=False, server_default="MANUAL", comment="触发来源（MANUAL, SCHEDULED）"),
            sa.Column("platform", sa.String(32), nullable=True, comment="平台标识"),
            sa.Column("requested_limit", sa.Integer(), nullable=True, comment="批量任务请求数量"),
            sa.Column("requested_url", sa.String(1024), nullable=True, comment="单商品抓取链接"),
            sa.Column("status", sa.String(32), nullable=False, server_default="PENDING", comment="任务状态"),
            sa.Column("processed_count", sa.Integer(), nullable=False, server_default="0", comment="处理数"),
            sa.Column("success_count", sa.Integer(), nullable=False, server_default="0", comment="成功数"),
            sa.Column("failure_count", sa.Integer(), nullable=False, server_default="0", comment="失败数"),
            sa.Column("started_at", sa.DateTime(), nullable=True, comment="开始执行时间"),
            sa.Column("finished_at", sa.DateTime(), nullable=True, comment="结束时间"),
            sa.Column("summary_message", sa.String(512), nullable=True, comment="任务摘要"),
            sa.Column("error_message", sa.Text(), nullable=True, comment="错误详情"),
            sa.Column("failed_items_json", sa.Text(), nullable=True, comment="失败明细JSON"),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False, comment="创建时间"),
            sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False, comment="更新时间"),
            sa.UniqueConstraint("task_id", name="uk_scrape_task_run_task_id"),
            comment="抓取任务执行记录表",
        )
    else:
        _add_column_if_missing("scrape_task_run", sa.Column("failed_items_json", sa.Text(), nullable=True, comment="失败明细JSON"))
    _create_index_if_missing("idx_scrape_task_run_status", "scrape_task_run", ["status"])
    _create_index_if_missing("idx_scrape_task_run_created_at", "scrape_task_run", ["created_at"])

    if not _table_exists("etl_log"):
        op.create_table(
            "etl_log",
            sa.Column("id", PK_TYPE, primary_key=True, autoincrement=True, comment="自增主键"),
            sa.Column("event_type", sa.String(32), nullable=False, comment="事件类型（CLEANING, ANOMALY, SYSTEM）"),
            sa.Column("platform", sa.String(32), nullable=True, comment="平台标识"),
            sa.Column("sku_id", sa.String(64), nullable=True, comment="原始SKU ID"),
            sa.Column("product_id", PK_TYPE, nullable=True, comment="关联商品ID"),
            sa.Column("field_name", sa.String(64), nullable=True, comment="处理字段名"),
            sa.Column("original_value", sa.Text(), nullable=True, comment="原始值"),
            sa.Column("cleaned_value", sa.Text(), nullable=True, comment="清洗后的值"),
            sa.Column("status", sa.SmallInteger(), nullable=True, server_default="1", comment="状态（1:已处理, 0:待人工校验, -1:已忽略）"),
            sa.Column("message", sa.String(512), nullable=True, comment="日志消息"),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False, comment="创建时间"),
            sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False, comment="更新时间"),
            comment="数据清洗与处理日志表",
        )
    _create_index_if_missing("idx_etl_event_type", "etl_log", ["event_type"])
    _create_index_if_missing("idx_etl_sku_id", "etl_log", ["sku_id"])

    if not _table_exists("anomaly_alert"):
        op.create_table(
            "anomaly_alert",
            sa.Column("id", PK_TYPE, primary_key=True, autoincrement=True, comment="自增主键"),
            sa.Column("alert_type", sa.String(32), nullable=False, comment="报警类型（PRICE_BUG, STOCK_BUG, DATA_MISSING, SCRAPE_FAILURE）"),
            sa.Column("platform", sa.String(32), nullable=False, comment="平台标识"),
            sa.Column("sku_id", sa.String(64), nullable=False, comment="原始SKU ID"),
            sa.Column("product_id", PK_TYPE, nullable=True, comment="关联商品ID"),
            sa.Column("alert_value", sa.String(256), nullable=False, comment="异常值（如 0.1 元）"),
            sa.Column("threshold", sa.String(256), nullable=True, comment="触发阈值"),
            sa.Column("is_verified", sa.SmallInteger(), nullable=True, server_default="0", comment="是否已人工核实（1:是, 0:否）"),
            sa.Column("verification_result", sa.String(256), nullable=True, comment="核实结果"),
            sa.Column("message", sa.String(512), nullable=True, comment="异常消息"),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False, comment="创建时间"),
            sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False, comment="更新时间"),
            comment="异常报警记录表",
        )
    _create_index_if_missing("idx_anomaly_sku_id", "anomaly_alert", ["sku_id"])
    _create_index_if_missing("idx_anomaly_type", "anomaly_alert", ["alert_type"])

    if not _table_exists("crawl_efficiency"):
        op.create_table(
            "crawl_efficiency",
            sa.Column("id", PK_TYPE, primary_key=True, autoincrement=True, comment="自增主键"),
            sa.Column("platform", sa.String(32), nullable=False, comment="平台标识"),
            sa.Column("target_api", sa.String(128), nullable=False, comment="抓取接口名"),
            sa.Column("response_time_ms", sa.Integer(), nullable=False, comment="响应耗时(ms)"),
            sa.Column("status_code", sa.Integer(), nullable=False, comment="HTTP状态码"),
            sa.Column("captured_at", sa.DateTime(), server_default=sa.func.now(), nullable=False, comment="抓取时间"),
            comment="采集效率监控表",
        )
    _create_index_if_missing("idx_crawl_platform_time", "crawl_efficiency", ["platform", "captured_at"])


def downgrade() -> None:
    for table_name in (
        "crawl_efficiency",
        "anomaly_alert",
        "etl_log",
        "scrape_task_run",
        "sku_comparison",
        "mapping_rule",
        "category_node",
    ):
        if _table_exists(table_name):
            op.drop_table(table_name)

    for column_name in ("snapshot_count", "avg_price", "max_price", "min_price"):
        if _column_exists("sku_product", column_name):
            op.drop_column("sku_product", column_name)
