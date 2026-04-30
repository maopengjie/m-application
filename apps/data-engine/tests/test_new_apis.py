import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import Base, get_db
from app.models.user import User
from app.models.product import Product, ProductSKU, Coupon, RiskScore
from app.models.task import CrawlTask
from app.core.security import get_password_hash

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
    # Create test user
    admin = User(
        username="testadmin", 
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
    resp = client.post("/api/v1/auth/login", json={"username": "testadmin", "password": "pass"})
    return {"Authorization": f"Bearer {resp.json()['data']['accessToken']}"}

def test_coupon_api(client, db):
    headers = get_auth_headers(client)
    # Add dummy data
    p = Product(name="P")
    db.add(p); db.flush()
    sku = ProductSKU(product_id=p.id, platform="JD", platform_sku_id="s1", title="T", price=100.0)
    db.add(sku); db.flush()
    db.add(Coupon(sku_id=sku.id, title="50 OFF", amount=50.0, type="coupon"))
    db.commit()

    resp = client.get("/api/v1/coupons", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["data"]) == 1
    assert data["data"][0]["title"] == "50 OFF"

def test_risk_api(client, db):
    headers = get_auth_headers(client)
    # Add dummy data
    p = Product(name="PR")
    db.add(p); db.flush()
    sku = ProductSKU(product_id=p.id, platform="JD", platform_sku_id="rs1", title="Risk SKU", price=100.0)
    db.add(sku); db.flush()
    db.add(RiskScore(sku_id=sku.id, score=85, comment_abnormal=True, sales_abnormal=False))
    db.commit()

    resp = client.get("/api/v1/risks", headers=headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) == 1
    assert data[0]["sku_title"] == "Risk SKU"
    assert data[0]["score"] == 85

def test_menu_api(client, db):
    headers = get_auth_headers(client)
    resp = client.get("/api/v1/menu/all", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["data"] == []

def test_crawler_tasks_list(client, db):
    headers = get_auth_headers(client)
    db.add(CrawlTask(task_type="price_update", status="success", total_count=10, success_count=10))
    db.commit()

    resp = client.get("/api/v1/crawler/tasks", headers=headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) >= 1
    assert data[0]["task_type"] == "price_update"
