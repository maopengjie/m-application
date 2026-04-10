from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import time

app = FastAPI(title="Vben Data Engine (Python)")

# 配置跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Vben Data Engine (Python) is running"}

@app.get("/api/status")
async def get_status():
    return {
        "code": 0,
        "data": {
            "status": "online",
            "engine": "FastAPI",
            "task_count": 0
        },
        "message": "ok"
    }

# 示例：爬虫触发接口
@app.post("/api/crawler/start")
async def start_crawler(target_url: str):
    # 这里将来集成 playwright 或 scrapy
    print(f"Starting crawler for: {target_url}")
    return {
        "code": 0,
        "data": {"job_id": f"job_{int(time.time())}"},
        "message": "Crawler task started"
    }

# 示例：数据分析接口
@app.get("/api/analysis/summary")
async def get_analysis():
    # 模拟 Pandas 数据分析
    data = {
        'City': ['Beijing', 'Shanghai', 'Guangzhou', 'Shenzhen'],
        'Sales': [100, 150, 120, 200]
    }
    df = pd.DataFrame(data)
    summary = df.describe().to_dict()
    return {
        "code": 0,
        "data": {
            "summary": summary,
            "chart_data": data
        },
        "message": "Analysis completed"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
