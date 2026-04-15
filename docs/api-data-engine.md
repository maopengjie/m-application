# Data Engine API Documentation

This document describes the API endpoints provided by the `apps/data-engine` service.

## Base URL
`http://localhost:8000`

## Authentication

### Login
- **Endpoint**: `POST /api/auth/login`
- **Payload**:
  ```json
  {
    "username": "vben",
    "password": "123456"
  }
  ```
- **Response**: Returns user info and `accessToken`. Sets a `jwt` refresh cookie.

### Refresh Token
- **Endpoint**: `POST /api/auth/refresh`
- **Cookie**: Requires `jwt` refresh cookie.
- **Response**: Returns a new `accessToken`.

### Logout
- **Endpoint**: `POST /api/auth/logout`
- **Response**: Clears the refresh cookie.

### Get Access Codes
- **Endpoint**: `GET /api/auth/codes`
- **Header**: `Authorization: Bearer <token>`
- **Response**: List of permission codes for the current user.

### Get User Info
- **Endpoint**: `GET /api/user/info`
- **Header**: `Authorization: Bearer <token>`
- **Response**: Detailed user information.

## Core Features

### Status Check
- **Endpoint**: `GET /api/status`
- **Response**: Service status and basic statistics.

### Start Crawler
- **Endpoint**: `POST /api/crawler/start`
- **Query Parameter**: `target_url` (string)
- **Response**: Returns a `job_id`.

### Analysis Summary
- **Endpoint**: `GET /api/analysis/summary`
- **Response**: Descriptive statistics (using pandas) and chart data for demo purposes.

## Implementation Details
- **Framework**: FastAPI
- **Security**: JWT (Jose) + HTTPOnly Cookies
- **Data Processing**: Pandas (for analysis)
- **CORS**: Configured for local development at port 5777.
