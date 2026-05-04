from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.sku_repository import router as sku_repository_router
from db.session import init_db, seed_demo_data

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
    seed_demo_data()


app.include_router(sku_repository_router)

@app.get("/")
async def root():
    return {"message": "Welcome to m-application API", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "ok"}
