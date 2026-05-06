"""create price time series tables

Revision ID: 20260504_0002
Revises: 20260430_0001
Create Date: 2026-05-04 10:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260504_0002"
down_revision: Union[str, Sequence[str], None] = "20260430_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    if op.get_bind().dialect.name != "mysql":
        pk_type = sa.BigInteger().with_variant(sa.Integer(), "sqlite")
        op.create_table(
            "sku_price_snapshot",
            sa.Column("id", pk_type, primary_key=True, autoincrement=True, comment="自增主键"),
            sa.Column("sku_product_id", pk_type, nullable=False, comment="关联商品主表ID"),
            sa.Column("captured_at", sa.DateTime(), nullable=False, comment="抓取时间"),
            sa.Column("list_price", sa.Integer(), nullable=False, server_default="0", comment="标价，单位分"),
            sa.Column("reduction_amount", sa.Integer(), nullable=False, server_default="0", comment="满减金额，单位分"),
            sa.Column("coupon_amount", sa.Integer(), nullable=False, server_default="0", comment="优惠券金额，单位分"),
            sa.Column("other_discount_amount", sa.Integer(), nullable=False, server_default="0", comment="其他优惠金额，单位分"),
            sa.Column("final_price", sa.Integer(), nullable=False, server_default="0", comment="到手价，单位分"),
            sa.Column("promo_text", sa.String(255), nullable=True, comment="促销文案"),
            sa.Column("is_anomalous", sa.SmallInteger(), nullable=False, server_default="0", comment="是否异常快照（1:是, 0:否）"),
            sa.Column("anomaly_reason", sa.String(255), nullable=True, comment="异常原因"),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False, comment="创建时间"),
            sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False, comment="更新时间"),
            comment="商品价格时序快照表",
        )
        op.create_index(
            "idx_price_snapshot_product_capture",
            "sku_price_snapshot",
            ["sku_product_id", "captured_at"],
        )
        op.create_index("idx_price_snapshot_capture", "sku_price_snapshot", ["captured_at"])
        op.create_index("idx_price_snapshot_anomaly", "sku_price_snapshot", ["is_anomalous"])
        return

    op.execute(
        """
        CREATE TABLE `sku_price_snapshot` (
          `id` bigint NOT NULL AUTO_INCREMENT COMMENT '自增主键',
          `sku_product_id` bigint NOT NULL COMMENT '关联商品主表ID',
          `captured_at` datetime NOT NULL COMMENT '抓取时间',
          `list_price` int NOT NULL DEFAULT '0' COMMENT '标价，单位分',
          `reduction_amount` int NOT NULL DEFAULT '0' COMMENT '满减金额，单位分',
          `coupon_amount` int NOT NULL DEFAULT '0' COMMENT '优惠券金额，单位分',
          `other_discount_amount` int NOT NULL DEFAULT '0' COMMENT '其他优惠金额，单位分',
          `final_price` int NOT NULL DEFAULT '0' COMMENT '到手价，单位分',
          `promo_text` varchar(255) DEFAULT NULL COMMENT '促销文案',
          `is_anomalous` tinyint NOT NULL DEFAULT '0' COMMENT '是否异常快照（1:是, 0:否）',
          `anomaly_reason` varchar(255) DEFAULT NULL COMMENT '异常原因',
          `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
          `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
          PRIMARY KEY (`id`),
          KEY `idx_price_snapshot_product_capture` (`sku_product_id`, `captured_at`),
          KEY `idx_price_snapshot_capture` (`captured_at`),
          KEY `idx_price_snapshot_anomaly` (`is_anomalous`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='商品价格时序快照表'
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS `sku_price_snapshot`")
