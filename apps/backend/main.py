import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.core_dashboard import router as core_dashboard_router
from api.data_cleaning import router as data_cleaning_router
from api.sku_repository import router as sku_repository_router
from db.session import init_db, seed_demo_data


ENABLE_DEMO_SEED = os.getenv("ENABLE_DEMO_SEED", "").lower() in {"1", "true", "yes"}

app = FastAPI(title="m-application API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event():
    init_db()
    if ENABLE_DEMO_SEED:
        seed_demo_data()


app.include_router(sku_repository_router)
app.include_router(data_cleaning_router)
app.include_router(core_dashboard_router)

# Development proxy compatibility: some local dev servers forward /api/* without
# stripping the prefix. Keep canonical routes prefix-free while accepting /api.
app.include_router(sku_repository_router, prefix="/api")
app.include_router(data_cleaning_router, prefix="/api")
app.include_router(core_dashboard_router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "Welcome to m-application API", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "ok"}
