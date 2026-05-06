"""create sku repository tables

Revision ID: 20260430_0001
Revises:
Create Date: 2026-04-30 00:00:01
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260430_0001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    if op.get_bind().dialect.name != "mysql":
        pk_type = sa.BigInteger().with_variant(sa.Integer(), "sqlite")
        op.create_table(
            "sku_product",
            sa.Column("id", pk_type, primary_key=True, autoincrement=True, comment="自增主键"),
            sa.Column("platform", sa.String(32), nullable=False, comment="平台标识（jd, tmall等）"),
            sa.Column("sku_id", sa.String(64), nullable=False, comment="原始平台SKU ID"),
            sa.Column("product_name", sa.String(512), nullable=False, comment="原始商品全名"),
            sa.Column("normalized_name", sa.String(512), nullable=True, comment="归一化后的商品名称"),
            sa.Column("brand_name", sa.String(128), nullable=True, comment="品牌名称"),
            sa.Column("main_image_url", sa.String(1024), nullable=True, comment="主图URL"),
            sa.Column("category_level_1", sa.String(64), nullable=True, comment="一级类目名称"),
            sa.Column("category_level_2", sa.String(64), nullable=True, comment="二级类目名称"),
            sa.Column("category_level_3", sa.String(64), nullable=True, comment="三级类目名称"),
            sa.Column("category_id_3", sa.BigInteger(), nullable=True, comment="原始平台三级类目ID"),
            sa.Column("shop_name", sa.String(128), nullable=True, comment="店铺名称"),
            sa.Column("product_url", sa.String(1024), nullable=True, comment="商品详情页链接"),
            sa.Column("status", sa.SmallInteger(), nullable=False, server_default="1", comment="状态（1:在售, 0:下架, -1:删除）"),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False, comment="创建时间"),
            sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False, comment="更新时间"),
            sa.UniqueConstraint("platform", "sku_id", name="uk_platform_sku"),
            comment="商品主表",
        )
        op.create_index("idx_brand_name", "sku_product", ["brand_name"])
        op.create_index("idx_category_id_3", "sku_product", ["category_id_3"])
        op.create_index("idx_normalized_name", "sku_product", ["normalized_name"])

        op.create_table(
            "sku_product_attr",
            sa.Column("id", pk_type, primary_key=True, autoincrement=True, comment="自增主键"),
            sa.Column("sku_product_id", pk_type, nullable=False, comment="关联商品主表ID"),
            sa.Column("attr_group", sa.String(64), server_default="主体", nullable=True, comment="属性分组"),
            sa.Column("attr_name", sa.String(64), nullable=False, comment="属性键名"),
            sa.Column("attr_value", sa.String(256), nullable=False, comment="属性值"),
            sa.Column("attr_unit", sa.String(32), nullable=True, comment="单位"),
            sa.Column("source_text", sa.Text(), nullable=True, comment="原始解析文本"),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False, comment="创建时间"),
            sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False, comment="更新时间"),
            comment="商品属性表",
        )
        op.create_index("idx_sku_product_id", "sku_product_attr", ["sku_product_id"])
        op.create_index("idx_attr_kv", "sku_product_attr", ["attr_name", "attr_value"])
        op.create_index("idx_sku_attr_name", "sku_product_attr", ["sku_product_id", "attr_name"])

        op.create_table(
            "tag_definition",
            sa.Column("id", pk_type, primary_key=True, autoincrement=True, comment="自增主键"),
            sa.Column("tag_code", sa.String(64), nullable=False, comment="标签唯一编码"),
            sa.Column("tag_name", sa.String(64), nullable=False, comment="标签名称"),
            sa.Column("tag_type", sa.String(32), nullable=False, server_default="SYSTEM", comment="类型（SYSTEM, MANUAL, RULE）"),
            sa.Column("description", sa.String(256), nullable=True, comment="说明"),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False, comment="创建时间"),
            sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False, comment="更新时间"),
            sa.UniqueConstraint("tag_code", name="uk_tag_code"),
            comment="标签定义表",
        )

        op.create_table(
            "sku_tag_relation",
            sa.Column("id", pk_type, primary_key=True, autoincrement=True, comment="自增主键"),
            sa.Column("sku_product_id", pk_type, nullable=False, comment="关联商品主表ID"),
            sa.Column("tag_id", pk_type, nullable=False, comment="关联标签定义表ID"),
            sa.Column("tag_value", sa.String(128), nullable=True, comment="标签附加值"),
            sa.Column("source_type", sa.String(32), nullable=False, server_default="AUTO", comment="来源（AUTO, MANUAL, RULE）"),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False, comment="创建时间"),
            sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False, comment="更新时间"),
            sa.UniqueConstraint("sku_product_id", "tag_id", name="uk_sku_tag"),
            comment="商品标签关联表",
        )
        op.create_index("idx_tag_id", "sku_tag_relation", ["tag_id"])
        op.create_index("idx_source_type", "sku_tag_relation", ["source_type"])
        return

    op.execute(
        """
        CREATE TABLE `sku_product` (
          `id` bigint NOT NULL AUTO_INCREMENT COMMENT '自增主键',
          `platform` varchar(32) NOT NULL COMMENT '平台标识（jd, tmall等）',
          `sku_id` varchar(64) NOT NULL COMMENT '原始平台SKU ID',
          `product_name` varchar(512) NOT NULL COMMENT '原始商品全名',
          `normalized_name` varchar(512) DEFAULT NULL COMMENT '归一化后的商品名称',
          `brand_name` varchar(128) DEFAULT NULL COMMENT '品牌名称',
          `main_image_url` varchar(1024) DEFAULT NULL COMMENT '主图URL',
          `category_level_1` varchar(64) DEFAULT NULL COMMENT '一级类目名称',
          `category_level_2` varchar(64) DEFAULT NULL COMMENT '二级类目名称',
          `category_level_3` varchar(64) DEFAULT NULL COMMENT '三级类目名称',
          `category_id_3` bigint DEFAULT NULL COMMENT '原始平台三级类目ID',
          `shop_name` varchar(128) DEFAULT NULL COMMENT '店铺名称',
          `product_url` varchar(1024) DEFAULT NULL COMMENT '商品详情页链接',
          `status` tinyint NOT NULL DEFAULT '1' COMMENT '状态（1:在售, 0:下架, -1:删除）',
          `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
          `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
          PRIMARY KEY (`id`),
          UNIQUE KEY `uk_platform_sku` (`platform`, `sku_id`),
          KEY `idx_brand_name` (`brand_name`),
          KEY `idx_category_id_3` (`category_id_3`),
          KEY `idx_normalized_name` (`normalized_name`(191))
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='商品主表'
        """
    )
    op.execute(
        """
        CREATE TABLE `sku_product_attr` (
          `id` bigint NOT NULL AUTO_INCREMENT COMMENT '自增主键',
          `sku_product_id` bigint NOT NULL COMMENT '关联商品主表ID',
          `attr_group` varchar(64) DEFAULT '主体' COMMENT '属性分组',
          `attr_name` varchar(64) NOT NULL COMMENT '属性键名',
          `attr_value` varchar(256) NOT NULL COMMENT '属性值',
          `attr_unit` varchar(32) DEFAULT NULL COMMENT '单位',
          `source_text` text COMMENT '原始解析文本',
          `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
          `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
          PRIMARY KEY (`id`),
          KEY `idx_sku_product_id` (`sku_product_id`),
          KEY `idx_attr_kv` (`attr_name`, `attr_value`(64)),
          KEY `idx_sku_attr_name` (`sku_product_id`, `attr_name`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='商品属性表'
        """
    )
    op.execute(
        """
        CREATE TABLE `tag_definition` (
          `id` bigint NOT NULL AUTO_INCREMENT COMMENT '自增主键',
          `tag_code` varchar(64) NOT NULL COMMENT '标签唯一编码',
          `tag_name` varchar(64) NOT NULL COMMENT '标签名称',
          `tag_type` varchar(32) NOT NULL DEFAULT 'SYSTEM' COMMENT '类型（SYSTEM, MANUAL, RULE）',
          `description` varchar(256) DEFAULT NULL COMMENT '说明',
          `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
          `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
          PRIMARY KEY (`id`),
          UNIQUE KEY `uk_tag_code` (`tag_code`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='标签定义表'
        """
    )
    op.execute(
        """
        CREATE TABLE `sku_tag_relation` (
          `id` bigint NOT NULL AUTO_INCREMENT COMMENT '自增主键',
          `sku_product_id` bigint NOT NULL COMMENT '关联商品主表ID',
          `tag_id` bigint NOT NULL COMMENT '关联标签定义表ID',
          `tag_value` varchar(128) DEFAULT NULL COMMENT '标签附加值',
          `source_type` varchar(32) NOT NULL DEFAULT 'AUTO' COMMENT '来源（AUTO, MANUAL, RULE）',
          `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
          `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
          PRIMARY KEY (`id`),
          UNIQUE KEY `uk_sku_tag` (`sku_product_id`, `tag_id`),
          KEY `idx_tag_id` (`tag_id`),
          KEY `idx_source_type` (`source_type`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='商品标签关联表'
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS `sku_tag_relation`")
    op.execute("DROP TABLE IF EXISTS `tag_definition`")
    op.execute("DROP TABLE IF EXISTS `sku_product_attr`")
    op.execute("DROP TABLE IF EXISTS `sku_product`")
