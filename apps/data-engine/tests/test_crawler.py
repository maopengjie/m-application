import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi import HTTPException

from app.main import app
from app.core.database import Base, get_db
from app.models.task import CrawlTask
from app.models.product import Product, ProductSKU, PriceHistory
from app.services.collector_service import CollectorService
from app.core.security import get_password_hash
from app.models.user import User

# Use in-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    # Create admin user for permissions
    admin = User(
        username="admin", 
        hashed_password=get_password_hash("pass"), 
        real_name="Admin", 
        roles=["admin"], 
        is_active=True
    )
    db.add(admin)
    db.commit()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def get_auth_headers(client):
    resp = client.post("/api/v1/auth/login", json={"username": "admin", "password": "pass"})
    return {"Authorization": f"Bearer {resp.json()['data']['accessToken']}"}


def test_crawler_start_persists_task(client, db):
    headers = get_auth_headers(client)
    url = "https://example.com/product/123"
    
    resp = client.post("/api/v1/crawler/start", json={"target_url": url}, headers=headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    
    job_id = data["job_id"]
    assert job_id.startswith("job_")
    
    # Verify DB persistence
    task_id = int(job_id.split("_")[1])
    task = db.query(CrawlTask).filter(CrawlTask.id == task_id).first()
    assert task is not None
    assert task.status == "pending"
    assert task.metadata_json["target_url"] == url


def test_collector_run_lifecycle_and_history(db):
    # Setup Product
    p = Product(name="P", brand="B", category="C")
    db.add(p)
    db.flush()
    
    # Setup SKU
    sku = ProductSKU(product_id=p.id, platform="JD", platform_sku_id="s1", title="T", price=100.0)
    db.add(sku)
    db.commit()
    
    service = CollectorService()
    service.run_collection(db)
    
    # Verify task state
    task = db.query(CrawlTask).filter(CrawlTask.task_type == "price_update").first()
    assert task.status in ["success", "partial_success"]
    assert task.total_count == 1
    
    # Verify history write
    history = db.query(PriceHistory).filter(PriceHistory.sku_id == sku.id).first()
    assert history is not None
    assert history.price is not None


def test_collector_concurrency_lock(db):
    # Manually create a running task
    running_task = CrawlTask(task_type="price_update", status="running")
    db.add(running_task)
    db.commit()
    
    service = CollectorService()
    with pytest.raises(HTTPException) as excinfo:
        service.run_collection(db)
    
    assert excinfo.value.status_code == 409
    assert "already active" in excinfo.value.detail


def test_collector_error_accounting_metadata(db):
    # Setup Product
    p = Product(name="P", brand="B", category="C")
    db.add(p)
    db.flush()
    
    # Create multiple SKUs
    for i in range(5):
        db.add(ProductSKU(product_id=p.id, platform="JD", platform_sku_id=f"err_{i}", title="T", price=100.0))
    db.commit()
    
    service = CollectorService()
    
    # Mock scraper to fail every time
    service._scrape_sku_price = lambda sku: None
    
    service.run_collection(db)
    
    task = db.query(CrawlTask).filter(CrawlTask.task_type == "price_update").first()
    assert task.status == "partial_success"
    assert task.failed_count == 5
    assert len(task.metadata_json["all_errors"]) == 5
    assert "error" in task.error_log
