# Decidely - 智能购物决策与价格监控平台

Decidely 是一个高效的购物决策助手，通过多维度数据抓取、历史价格追踪及智能决策模型，帮助用户在最佳时机以最低价格入手心仪商品。

## 🌟 核心特性

- **多平台比价**：支持京东、天猫等主流电商平台的实时价格对比。
- **智能决策引擎**：基于历史价格走势、商家信誉（风险分）、优惠力度等多维度给出 AVOID/WAIT/BUY 建议。
- **降价提醒系统**：用户可订阅心仪商品，当价格跌破目标价时自动触发通知。
- **采集链路增强**：内置重试、模拟延迟及任务状态追踪，确保数据更新的稳定性。
- **高性能架构**：后端基于 FastAPI + SQLAlchemy 2.0，引入 Redis 缓存加速详情页加载。

## 🛠️ 技术栈

### 后端 (Data Engine)

- **FastAPI**: 高性能 Web 框架。
- **SQLAlchemy 2.0**: 现代 ORM 映射。
- **Alembic**: 数据库迁移工具。
- **Redis**: 缓存与任务中间件。
- **APScheduler**: 定时任务调度。
- **MySQL**: 核心持久化存储。

### 前端 (Web Ele)

- **Vue 3**: 现代前端框架。
- **Element Plus**: 桌面端组件库。
- **Tailwind CSS**: 原子化样式引擎。
- **Vite**: 极速构建工具。

## 🚀 快速启动

### 1. 环境准备

确保已安装 Python 3.10+、Node.js 18+、MySQL 8.0+ 及 Redis。

### 2. 数据库初始化

```bash
cd apps/data-engine
# 创建并激活虚拟环境
python -m venv .venv
source .venv/bin/activate # macOS/Linux
# 安装依赖
pip install -r requirements.txt
# 设置环境变量 (.env)
cp .env.example .env # 请根据实际情况修改配置
# 一键初始化（包含迁移与种子数据）
python scripts/init_db.py
```

### 3. 启动后端

```bash
python src/main.py
```

API 文档访问：`http://localhost:8000/docs`

### 4. 启动前端

```bash
cd apps/web-ele
pnpm install
pnpm dev
```

访问地址：`http://localhost:5777`

## 📖 API 核心接口清单

| 模块     | 接口路径                             | 方法 | 功能描述                            |
| :------- | :----------------------------------- | :--- | :---------------------------------- |
| **搜索** | `/api/v1/search`                     | GET  | 关键词搜索，支持品牌/品类筛选与排序 |
| **商品** | `/api/v1/products/{id}`              | GET  | 获取商品详情，支持 Redis 缓存       |
| **决策** | `/api/v1/decision/{sku_id}`          | GET  | 获取智能购买建议及分数              |
| **提醒** | `/api/v1/alerts`                     | POST | 创建价格监控提醒                    |
| **历史** | `/api/v1/products/skus/{id}/history` | GET  | 获取 30/90 天价格历史走势           |

## 🏗️ 数据库 ER 关系说明

- **Product**: 商品主体信息（名称、品牌、品类）。
- **ProductSKU**: 挂载在 Product 下的具体平台记录（价格、原价、平台名）。
- **PriceHistory**: SKU 的历史价格流水。
- **PriceAlert**: 用户设置的降价触发器。
- **RiskScore**: SKU 对应的商家信誉与风险判定。
- **CrawlTask**: 后台采集任务执行记录。

## 🔮 后续规划

1. **AI 决策升级**：引入大模型 (LLM) 分析用户评论情感，细化商品优缺点总结。
2. **推荐系统**：基于用户浏览历史与搜索权重，推荐“历史低价”好物。
3. **用户体系**：完善个人中心、收藏夹及多端推送通知（邮件/微信/App）。
4. **采集深度**：接入真实平台协议层抓取，提升数据抓取的实时性与准确度。

---

© 2026 Decidely Team. All rights reserved.
