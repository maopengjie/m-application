# SKU 资源库数据库设计

## 1. 模块设计说明
**核心理念**：采用“商品主表 + 扩展属性表（EAV）+ 标签体系”三层结构，兼顾高频查询性能、异构商品参数扩展能力和标签化运营需求。

**设计原则**：
- **高扩展性**：通过 `sku_product_attr` 承载动态属性，避免因不同品类参数差异频繁修改主表结构。
- **多平台兼容**：通过 `platform` + `sku_id` 作为业务唯一键，支持京东、天猫、拼多多等平台商品统一接入。
- **名称归一化**：通过 `normalized_name` 保存清洗后的标准商品名，用于搜索、聚合、比价和同款识别。
- **标签解耦**：标签定义与商品主体分离，通过关联表实现手动、规则、系统自动打标。
- **逻辑外键**：不强制创建数据库物理外键，适合高并发抓取和批量导入场景。

---

## 2. 表结构设计

### 2.1 sku_product (商品主表)
用于存储商品最基础、最常用、最稳定的主信息。

| 字段名 | 类型 | 必填 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- | :--- |
| **id** | bigint | 是 | - | 自增主键 |
| **platform** | varchar(32) | 是 | - | 平台标识，如 jd、tmall |
| **sku_id** | varchar(64) | 是 | - | 原始平台 SKU ID |
| **product_name** | varchar(512) | 是 | - | 原始商品全名 |
| **normalized_name** | varchar(512) | 否 | NULL | 归一化商品名称 |
| **brand_name** | varchar(128) | 否 | NULL | 品牌名称 |
| **main_image_url** | varchar(1024) | 否 | NULL | 主图 URL |
| **category_level_1** | varchar(64) | 否 | NULL | 一级类目名称 |
| **category_level_2** | varchar(64) | 否 | NULL | 二级类目名称 |
| **category_level_3** | varchar(64) | 否 | NULL | 三级类目名称 |
| **category_id_3** | bigint | 否 | NULL | 原始平台三级类目 ID |
| **shop_name** | varchar(128) | 否 | NULL | 店铺名称 |
| **product_url** | varchar(1024) | 否 | NULL | 商品详情页链接 |
| **status** | tinyint | 是 | 1 | 状态：1 在售，0 下架，-1 删除 |
| **created_at** | datetime | 是 | CURRENT_TIMESTAMP | 创建时间 |
| **updated_at** | datetime | 是 | CURRENT_TIMESTAMP | 更新时间 |

**索引设计**：
- `UNIQUE KEY uk_platform_sku` (platform, sku_id)
- `KEY idx_brand_name` (brand_name)
- `KEY idx_category_id_3` (category_id_3)
- `KEY idx_normalized_name` (normalized_name(191))

---

### 2.2 sku_product_attr (商品属性表)
用于存储商品动态规格参数，适配不同品类的属性差异。

| 字段名 | 类型 | 必填 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- | :--- |
| **id** | bigint | 是 | - | 自增主键 |
| **sku_product_id** | bigint | 是 | - | 关联商品主表 ID |
| **attr_group** | varchar(64) | 否 | '主体' | 属性分组，如主体、屏幕、存储 |
| **attr_name** | varchar(64) | 是 | - | 属性名 |
| **attr_value** | varchar(256) | 是 | - | 属性值 |
| **attr_unit** | varchar(32) | 否 | NULL | 单位，如 GB、英寸 |
| **source_text** | text | 否 | NULL | 原始解析文本 |
| **created_at** | datetime | 是 | CURRENT_TIMESTAMP | 创建时间 |
| **updated_at** | datetime | 是 | CURRENT_TIMESTAMP | 更新时间 |

**索引设计**：
- `KEY idx_sku_product_id` (sku_product_id)
- `KEY idx_attr_kv` (attr_name, attr_value(64))
- `KEY idx_sku_attr_name` (sku_product_id, attr_name)

---

### 2.3 tag_definition (标签定义表)
用于维护所有合法标签定义。

| 字段名 | 类型 | 必填 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- | :--- |
| **id** | bigint | 是 | - | 自增主键 |
| **tag_code** | varchar(64) | 是 | - | 标签唯一编码，如 JD_SELF_OPERATED |
| **tag_name** | varchar(64) | 是 | - | 标签名称，如“京东自营” |
| **tag_type** | varchar(32) | 是 | 'SYSTEM' | 标签类型：SYSTEM、MANUAL、RULE |
| **description** | varchar(256) | 否 | NULL | 标签说明 |
| **created_at** | datetime | 是 | CURRENT_TIMESTAMP | 创建时间 |
| **updated_at** | datetime | 是 | CURRENT_TIMESTAMP | 更新时间 |

**索引设计**：
- `UNIQUE KEY uk_tag_code` (tag_code)

---

### 2.4 sku_tag_relation (商品标签关联表)
用于维护商品与标签的多对多关联关系。

| 字段名 | 类型 | 必填 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- | :--- |
| **id** | bigint | 是 | - | 自增主键 |
| **sku_product_id** | bigint | 是 | - | 关联商品主表 ID |
| **tag_id** | bigint | 是 | - | 关联标签定义表 ID |
| **tag_value** | varchar(128) | 否 | NULL | 标签附加值，如补贴金额 |
| **source_type** | varchar(32) | 是 | 'AUTO' | 来源：AUTO、MANUAL、RULE |
| **created_at** | datetime | 是 | CURRENT_TIMESTAMP | 创建时间 |
| **updated_at** | datetime | 是 | CURRENT_TIMESTAMP | 更新时间 |

**索引设计**：
- `UNIQUE KEY uk_sku_tag` (sku_product_id, tag_id)
- `KEY idx_tag_id` (tag_id)
- `KEY idx_source_type` (source_type)

---

## 3. MySQL 建表 SQL

```sql
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='商品主表';

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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='商品属性表';

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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='标签定义表';

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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='商品标签关联表';
```
