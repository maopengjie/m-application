# Data Engine 接口文档

本文档详细说明了 `apps/data-engine` 服务提供的 API 接口。

## 基础 URL
`http://localhost:8000`

## 身份认证 (Authentication)

### 登录
- **接口**: `POST /api/auth/login`
- **请求体 (Payload)**:
  ```json
  {
    "username": "vben",
    "password": "123456"
  }
  ```
- **响应**: 返回用户信息及 `accessToken`。同时会设置名为 `jwt` 的 HTTPOnly Refresh Cookie。

### 刷新 Token
- **接口**: `POST /api/auth/refresh`
- **Cookie**: 需要载入 `jwt` 刷新 Cookie。
- **响应**: 返回一个新的 `accessToken`。

### 登出
- **接口**: `POST /api/auth/logout`
- **响应**: 清除刷新 Cookie。

### 获取权限码
- **接口**: `GET /api/auth/codes`
- **请求头 (Header)**: `Authorization: Bearer <token>`
- **响应**: 当前用户的权限代码列表。

### 获取用户信息
- **接口**: `GET /api/user/info`
- **请求头 (Header)**: `Authorization: Bearer <token>`
- **响应**: 详细的用户个人信息。

## 核心功能 (Core Features)

### 状态检查
- **接口**: `GET /api/status`
- **响应**: 服务状态及基础统计信息。

### 启动采集器 (Crawler)
- **接口**: `POST /api/crawler/start`
- **查询参数**: `target_url` (string)
- **响应**: 返回任务 ID (`job_id`)。

### 分析摘要
- **接口**: `GET /api/analysis/summary`
- **响应**: 描述性统计数据（使用 pandas 计算）及用于演示的图表数据。

## 实现细节
- **框架**: FastAPI
- **安全**: JWT (Jose) + HTTPOnly Cookies
- **数据处理**: Pandas (用于数据分析)
- **CORS**: 已配置允许本地开发环境（端口 5777）的跨域请求。
