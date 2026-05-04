"""create price time series tables

Revision ID: 20260504_0002
Revises: 20260430_0001
Create Date: 2026-05-04 10:00:00
"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "20260504_0002"
down_revision: Union[str, Sequence[str], None] = "20260430_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
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
          `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
          `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
          PRIMARY KEY (`id`),
          KEY `idx_price_snapshot_product_capture` (`sku_product_id`, `captured_at`),
          KEY `idx_price_snapshot_capture` (`captured_at`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='商品价格时序快照表'
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS `sku_price_snapshot`")
