import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import Base, get_db
from app.models.user import User
from app.models.product import Product, ProductSKU, Coupon, Review
from app.core.security import get_password_hash

import os
TEST_DB_PATH = "./test_search.db"
if os.path.exists(TEST_DB_PATH):
    os.remove(TEST_DB_PATH)

engine = create_engine(
    f"sqlite:///{TEST_DB_PATH}",
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


@pytest.fixture(scope="module")
def client():
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.create_all(bind=engine)
    
    db = TestingSessionLocal()
    
    # User for auth
    user = User(username="testuser", hashed_password=get_password_hash("pass"), real_name="Tester", roles=["user"], is_active=True)
    db.add(user)
    
    # Create products
    p1 = Product(name="MacBook Pro", brand="Apple", category="Laptop", rating=4.5)
    p2 = Product(name="MacBook Air", brand="Apple", category="Laptop", rating=4.8)
    db.add_all([p1, p2])
    db.commit()
    
    # Create SKUs
    # MacBook Pro has JD and Taobao
    sku1 = ProductSKU(product_id=p1.id, platform="JD", platform_sku_id="JD001", title="MacBook Pro 14", price=10000, original_price=10000)
    sku2 = ProductSKU(product_id=p1.id, platform="Taobao", platform_sku_id="TB001", title="MacBook Pro 14 TB", price=9500, original_price=9800)
    
    # MacBook Air has JD only
    sku3 = ProductSKU(product_id=p2.id, platform="JD", platform_sku_id="JD002", title="MacBook Air 13", price=8000, original_price=8000)
    db.add_all([sku1, sku2, sku3])
    db.commit()
    
    # Create Coupons
    # SKU 1: 500 off -> effective 9500
    # SKU 2: 1000 off -> effective 8500
    # SKU 3: 0 off -> effective 8000
    c1 = Coupon(sku_id=sku1.id, title="500 OFF", amount=500, type="coupon")
    c2 = Coupon(sku_id=sku2.id, title="1000 OFF", amount=1000, type="coupon")
    db.add_all([c1, c2])
    
    # Reviews
    r1 = Review(sku_id=sku1.id, rating=5, content="Great")
    r2 = Review(sku_id=sku2.id, rating=4, content="Good")
    r3 = Review(sku_id=sku2.id, rating=1, content="Bad")
    db.add_all([r1, r2, r3])
    
    db.commit()
    db.close()
    
    with TestClient(app) as c:
        yield c
        
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()


def get_auth_headers(client):
    resp = client.post("/api/v1/auth/login", json={"username": "testuser", "password": "pass"})
    return {"Authorization": f"Bearer {resp.json()['data']['accessToken']}"}


def test_search_pagination_and_sorting(client):
    headers = get_auth_headers(client)
    
    # Ascending order: P2 (8000) first, P1 (8500) second
    resp = client.get("/api/v1/search?q=MacBook&sort_by=price_asc", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    
    assert data["data"]["total"] == 2
    assert len(data["data"]["items"]) == 2
    assert data["data"]["items"][0]["product_id"] == 2 # P2
    assert data["data"]["items"][1]["product_id"] == 1 # P1
    
    # Descending order: P1 first, P2 second
    resp_desc = client.get("/api/v1/search?q=MacBook&sort_by=price_desc", headers=headers)
    data_desc = resp_desc.json()
    assert data_desc["data"]["items"][0]["product_id"] == 1
    assert data_desc["data"]["items"][1]["product_id"] == 2


def test_search_platform_filtering_metadata(client):
    headers = get_auth_headers(client)
    
    # Search only JD
    resp = client.get("/api/v1/search?q=MacBook&platforms=JD&sort_by=price_asc", headers=headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    
    # For P1 (MacBook Pro), total reviews across all platforms is 3 (1 from JD, 2 from Taobao)
    # Total platforms is 2 (JD, Taobao)
    # When filtered by JD, we should ONLY see platforms_count = 1, comments_count = 1
    p1_item = next(item for item in data["items"] if item["product_id"] == 1)
    
    assert p1_item["platform_count"] == 1
    assert p1_item["comments_count"] == 1
    assert p1_item["final_price"] == 9500.0 # NOT 8500 (Taobao)
    assert "多平台比价" not in p1_item["tags"]
