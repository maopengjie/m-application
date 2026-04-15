# 一、技术选型确认

## 1. 前端
- Vue 3
- Vite
- Vue Router
- Pinia
- Element Plus
- Axios
- ECharts

## 2. 后端
- FastAPI
- SQLAlchemy 2.0
- Pydantic
- Alembic
- Redis
- Celery 或 APScheduler
- httpx / requests
- Playwright（如需动态页面采集）

## 3. 数据层
- MySQL 8
- Redis
- Elasticsearch（商品搜索量大时再接入）

---

# 二、重构后的系统架构

## 1. 总体架构
```text
[ Vue3 + Element Plus ]
        ↓
[ FastAPI API Layer ]
        ↓
[ Service Layer ]
  ├─ 商品服务
  ├─ 价格服务
  ├─ 优惠服务
  ├─ 风险分析服务
  ├─ 决策引擎服务
  └─ 提醒服务
        ↓
[ MySQL + Redis + Elasticsearch(可选) ]
        ↓
[ 采集任务 / 定时任务 / 异步任务 ]
```

## 2. 为什么这套技术栈适合你这个项目

### Vue 3 + Element Plus
适合后台类、数据展示类、运营类系统，开发效率高，组件成熟，尤其适合：
- 商品搜索页
- 比价表格
- 优惠信息列表
- 风险分析面板
- 管理后台

### FastAPI
很适合这个项目，因为它同时满足：
- 接口开发快
- 数据校验清晰
- 文档自动生成
- Python 生态方便做爬虫、分析、规则引擎、价格预测

也就是说，这个项目的“采集 + 分析 + API”都能放在 Python 里，整体成本更低。

---

# 三、PRD（按该技术栈可落地）

## 1. 产品目标
构建一个以比价 + 优惠 + 历史价格 + 风险识别 + 购买建议为核心的智能购物决策平台，帮助用户快速完成购买决策。

---

## 2. MVP 功能范围

### P0
- 商品搜索
- 商品详情
- 多平台比价
- 历史价格走势
- 优惠汇总
- 决策建议
- 降价提醒

### P1
- 评论真实性分析
- 店铺可信度分析
- 收藏与订阅
- 优惠中心

### P2
- AI 购买建议
- 个性化推荐
- 价格预测

---

## 3. 页面设计

### 3.1 商品搜索页
- **功能**
  - 输入商品关键词
  - 返回商品聚合结果
  - 支持按平台、价格区间筛选
- **前端实现建议**
  - el-input
  - el-select
  - el-table
  - el-pagination
- **接口**
  - `GET /api/v1/search?q=xxx&page=1&page_size=20`

---

### 3.2 商品详情页
- **模块**
  - 商品基础信息
  - 决策卡片
  - 平台价格对比
  - 历史价格曲线
  - 优惠信息
  - 风险分析
  - 设置提醒
- **前端实现建议**
  - 顶部 el-card
  - 比价区域 el-table
  - 图表用 ECharts
  - 决策区域用 el-alert / el-tag / el-descriptions

---

### 3.3 降价提醒页
- **功能**
  - 用户设置目标价格
  - 查看已订阅商品
  - 查看提醒状态
- **前端实现建议**
  - el-form
  - el-dialog
  - el-table

---

# 四、前端项目结构建议

```text
frontend/
├─ src/
│  ├─ api/
│  │  ├─ product.ts
│  │  ├─ price.ts
│  │  ├─ alert.ts
│  │  └─ decision.ts
│  ├─ assets/
│  ├─ components/
│  │  ├─ ProductCard.vue
│  │  ├─ PriceCompareTable.vue
│  │  ├─ PriceTrendChart.vue
│  │  ├─ DecisionCard.vue
│  │  └─ RiskPanel.vue
│  ├─ layout/
│  ├─ router/
│  │  └─ index.ts
│  ├─ stores/
│  │  ├─ product.ts
│  │  └─ user.ts
│  ├─ views/
│  │  ├─ SearchView.vue
│  │  ├─ ProductDetailView.vue
│  │  ├─ AlertView.vue
│  │  └─ HomeView.vue
│  ├─ utils/
│  ├─ App.vue
│  └─ main.ts
├─ package.json
└─ vite.config.ts
```

# 五、后端项目结构建议

建议采用 FastAPI 分层结构，不要把所有逻辑都堆在 main.py。

```text
backend/
├─ app/
│  ├─ api/
│  │  └─ v1/
│  │     ├─ endpoints/
│  │     │  ├─ product.py
│  │     │  ├─ search.py
│  │     │  ├─ decision.py
│  │     │  ├─ alert.py
│  │     │  └─ coupon.py
│  ├─ core/
│  │  ├─ config.py
│  │  ├─ database.py
│  │  ├─ redis.py
│  │  └─ security.py
│  ├─ models/
│  │  ├─ product.py
│  │  ├─ product_sku.py
│  │  ├─ price_history.py
│  │  ├─ coupon.py
│  │  ├─ review.py
│  │  ├─ risk_score.py
│  │  └─ price_alert.py
│  ├─ schemas/
│  │  ├─ product.py
│  │  ├─ decision.py
│  │  ├─ alert.py
│  │  └─ search.py
│  ├─ services/
│  │  ├─ product_service.py
│  │  ├─ search_service.py
│  │  ├─ price_service.py
│  │  ├─ coupon_service.py
│  │  ├─ risk_service.py
│  │  ├─ decision_service.py
│  │  └─ alert_service.py
│  ├─ repositories/
│  │  ├─ product_repo.py
│  │  ├─ price_repo.py
│  │  └─ alert_repo.py
│  ├─ tasks/
│  │  ├─ crawler_tasks.py
│  │  ├─ price_tasks.py
│  │  └─ alert_tasks.py
│  ├─ utils/
│  └─ main.py
├─ alembic/
├─ requirements.txt
└─ alembic.ini
```

# 六、数据库设计

下面这版适配 FastAPI + SQLAlchemy。

## 1. product 商品主表
```sql
CREATE TABLE product (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(255) NOT NULL,
  brand VARCHAR(100) DEFAULT NULL,
  category VARCHAR(100) DEFAULT NULL,
  main_image VARCHAR(500) DEFAULT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_name (name),
  INDEX idx_category (category)
);
```

## 2. product_sku 平台 SKU 表
```sql
CREATE TABLE product_sku (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  product_id BIGINT NOT NULL,
  platform VARCHAR(50) NOT NULL,
  platform_sku_id VARCHAR(100) NOT NULL,
  title VARCHAR(255) NOT NULL,
  price DECIMAL(10,2) NOT NULL DEFAULT 0,
  original_price DECIMAL(10,2) DEFAULT NULL,
  final_price DECIMAL(10,2) DEFAULT NULL,
  shop_name VARCHAR(255) DEFAULT NULL,
  is_official TINYINT(1) NOT NULL DEFAULT 0,
  product_url VARCHAR(1000) DEFAULT NULL,
  status TINYINT NOT NULL DEFAULT 1,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uk_platform_sku (platform, platform_sku_id),
  KEY idx_product_id (product_id),
  KEY idx_platform (platform)
);
```

## 3. price_history 价格历史表
```sql
CREATE TABLE price_history (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  sku_id BIGINT NOT NULL,
  price DECIMAL(10,2) NOT NULL,
  final_price DECIMAL(10,2) DEFAULT NULL,
  source_type VARCHAR(50) DEFAULT 'crawler',
  recorded_at DATETIME NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  KEY idx_sku_time (sku_id, recorded_at)
);
```
后期数据量大时可按月分表或按 sku_id hash 分表。

## 4. coupon 优惠表
```sql
CREATE TABLE coupon (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  sku_id BIGINT NOT NULL,
  coupon_type VARCHAR(50) NOT NULL,
  coupon_name VARCHAR(255) DEFAULT NULL,
  amount DECIMAL(10,2) DEFAULT 0,
  condition_amount DECIMAL(10,2) DEFAULT 0,
  start_time DATETIME DEFAULT NULL,
  end_time DATETIME DEFAULT NULL,
  is_active TINYINT(1) NOT NULL DEFAULT 1,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  KEY idx_sku_id (sku_id),
  KEY idx_active_time (is_active, start_time, end_time)
);
```

## 5. review 评论表
```sql
CREATE TABLE review (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  sku_id BIGINT NOT NULL,
  platform_review_id VARCHAR(100) DEFAULT NULL,
  rating INT DEFAULT NULL,
  content TEXT,
  is_positive TINYINT(1) DEFAULT NULL,
  review_time DATETIME DEFAULT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  KEY idx_sku_id (sku_id),
  KEY idx_review_time (review_time)
);
```

## 6. risk_score 风险评分表
```sql
CREATE TABLE risk_score (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  sku_id BIGINT NOT NULL,
  risk_score INT NOT NULL DEFAULT 0,
  risk_level VARCHAR(20) NOT NULL DEFAULT 'LOW',
  comment_abnormal TINYINT(1) NOT NULL DEFAULT 0,
  sales_abnormal TINYINT(1) NOT NULL DEFAULT 0,
  low_price_trap TINYINT(1) NOT NULL DEFAULT 0,
  summary VARCHAR(500) DEFAULT NULL,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uk_sku_id (sku_id)
);
```

## 7. price_alert 降价提醒表
```sql
CREATE TABLE price_alert (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  user_id BIGINT NOT NULL,
  sku_id BIGINT NOT NULL,
  target_price DECIMAL(10,2) NOT NULL,
  is_active TINYINT(1) NOT NULL DEFAULT 1,
  notified_at DATETIME DEFAULT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  KEY idx_user_id (user_id),
  KEY idx_sku_id (sku_id),
  KEY idx_active (is_active)
);
```

# 七、FastAPI 接口设计

## 1. 搜索接口
`GET /api/v1/search`

- **参数**：
  - `q`: 商品关键词
  - `page`
  - `page_size`

- **返回**：
```json
{
  "list": [
    {
      "product_id": 1,
      "name": "iPhone 15 256G",
      "image": "xxx",
      "min_price": 4899
    }
  ],
  "total": 100
}
```

## 2. 商品详情接口
`GET /api/v1/products/{product_id}`

- **返回**：
```json
{
  "product": {
    "id": 1,
    "name": "iPhone 15 256G"
  },
  "price_compare": [
    {
      "platform": "JD",
      "price": 4999,
      "final_price": 4899,
      "shop_name": "Apple京东自营旗舰店",
      "is_official": true
    }
  ],
  "price_history": [
    {
      "date": "2026-04-01",
      "price": 5200,
      "final_price": 5100
    }
  ],
  "coupons": [],
  "risk": {
    "risk_score": 20,
    "risk_level": "LOW"
  },
  "decision": {
    "suggestion": "BUY",
    "reason": "当前价格接近30天低位"
  }
}
```

## 3. 决策接口
`GET /api/v1/decisions/{sku_id}`

- **返回**：
```json
{
  "sku_id": 1001,
  "suggestion": "BUY",
  "confidence": 0.86,
  "price_level": "LOW",
  "risk_level": "LOW",
  "best_platform": "JD",
  "reason": "当前到手价接近历史最低价"
}
```

## 4. 创建提醒接口
`POST /api/v1/alerts`

- **请求体**：
```json
{
  "sku_id": 1001,
  "target_price": 4599
}
```

- **返回**：
```json
{
  "id": 1,
  "message": "提醒创建成功"
}
```

# 八、核心后端模块职责

## 1. search_service
**负责**：
- 商品关键词搜索
- 商品聚合
- 同款商品列表

## 2. price_service
**负责**：
- 当前价读取
- 历史价格统计
- 最低价、均价计算

## 3. coupon_service
**负责**：
- 优惠券汇总
- 满减规则计算
- 最终到手价计算

## 4. risk_service
**负责**：
- 评论异常识别
- 销量异常规则
- 风险等级输出

## 5. decision_service
**负责**：
- 综合价格、历史、优惠、风险
- 输出 BUY / WAIT / AVOID

---

# 九、决策引擎规则

MVP 阶段不建议一开始就上机器学习，先上规则引擎。

## 评分建议
`总分 = 价格分 40 + 历史分 30 + 优惠分 15 + 风险分 15`

## 示例规则

### 价格分
- 当前到手价 <= 历史最低价 * 1.05 ：40分
- 当前到手价 <= 30日均价：30分
- 当前到手价 > 30日均价：15分

### 历史分
- 当前价格处于30天最低区间：30分
- 当前价格处于中位：20分
- 当前价格偏高：10分

### 优惠分
- 有大额券/满减：15分
- 有普通优惠：8分
- 无优惠：0分

### 风险分
- 低风险：15分
- 中风险：8分
- 高风险：0分

## 输出
- `>= 80`：BUY
- `50 ~ 79`：WAIT
- `< 50`：AVOID

---

# 十、前端页面组件建议

## 搜索页
- SearchFilterBar
- ProductList
- PriceTag

## 详情页
- DecisionCard
- PriceCompareTable
- PriceTrendChart
- CouponPanel
- RiskAnalysisCard
- AlertDialog

## 个人中心
- AlertList
- FavoriteList

---

# 十一、开发顺序建议

## 第一阶段
- MySQL 表结构
- FastAPI 基础骨架
- Vue3 页面骨架
- 商品搜索接口
- 商品详情接口

## 第二阶段
- 历史价格
- 优惠计算
- 决策引擎
- 降价提醒

## 第三阶段
- 风险识别
- 评论分析
- 定时采集
- 管理后台

---

# 十二、你现在这套技术栈下的最佳方案

如果你用的是：
- Vue 3 + Element Plus
- FastAPI

那最合理的落地方式就是：

## 前端
做一个偏中后台风格的 Web 应用，优先把：
- 搜索
- 详情
- 比价
- 决策卡片
做出来。

## 后端
用 FastAPI 作为统一 API 层，把：
- 接口
- 采集
- 决策逻辑
- 定时任务
尽量统一在 Python 体系里。

这样开发成本最低，后续演进也最顺。
