import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from unittest.mock import MagicMock

from app.main import app
from app.core.database import Base, get_db
from app.models.user import User
from app.models.product import Product
from app.core.security import get_password_hash

import os
TEST_DB_PATH = "./test_product.db"
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


@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="module")
def client():
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.create_all(bind=engine)
    
    db = TestingSessionLocal()
    admin = User(username="admin", hashed_password=get_password_hash("pass"), real_name="Admin", roles=["admin"], is_active=True)
    db.add(admin)
    db.commit()
    
    # Create product
    p = Product(id=999, name="Test Delete Product", brand="Test", category="Test")
    db.add(p)
    db.commit()
    db.close()
    
    with TestClient(app) as c:
        yield c
        
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()


def get_auth_headers(client):
    resp = client.post("/api/v1/auth/login", json={"username": "admin", "password": "pass"})
    return {"Authorization": f"Bearer {resp.json()['data']['accessToken']}"}


def test_product_cache_invalidation_on_delete(client):
    headers = get_auth_headers(client)
    
    # Intercept the instantiated product_service bound to the router
    from app.api.v1.endpoints.product import product_service
    mock_redis = MagicMock()
    original_redis = product_service.redis
    product_service.redis = mock_redis
    
    try:
        resp = client.delete("/api/v1/products/999", headers=headers)
        assert resp.status_code == 200
        mock_redis.delete.assert_called_with("product:999")
    finally:
        # Restore original redis
        product_service.redis = original_redis


def test_product_cache_data_parity(client, db):
    # 1. Create a product with complex fields (Decimal price, etc.)
    from app.models.product import ProductSKU
    p = Product(id=888, name="Parity Test Product", brand="Test", category="Test")
    db.add(p)
    db.flush()
    
    sku = ProductSKU(
        product_id=p.id,
        platform="JD",
        platform_sku_id="sku_888",
        title="SKU 888",
        price=123.45,
        original_price=150.0
    )
    db.add(sku)
    db.commit()

    # 2. Setup Redis Mock to simulate real string-based caching
    from app.api.v1.endpoints.product import product_service
    mock_redis = MagicMock()
    cache_store = {}
    
    def mock_setex(key, ttl, value):
        cache_store[key] = value
    def mock_get(key):
        return cache_store.get(key)
        
    mock_redis.setex.side_effect = mock_setex
    mock_redis.get.side_effect = mock_get
    
    original_redis = product_service.redis
    product_service.redis = mock_redis

    try:
        # 3. First call: Cold Path (triggers cache write)
        resp_cold = client.get(f"/api/v1/products/{p.id}")
        assert resp_cold.status_code == 200
        data_cold = resp_cold.json()["data"]
        assert "sku_888" in str(data_cold)
        assert mock_redis.setex.called

        # 4. Second call: Hot Path (triggers cache read)
        resp_hot = client.get(f"/api/v1/products/{p.id}")
        assert resp_hot.status_code == 200
        data_hot = resp_hot.json()["data"]

        # 5. Assert Field-for-Field Parity
        assert data_cold == data_hot
        assert float(data_hot["skus"][0]["price"]) == 123.45
        assert "final_price" in data_hot["skus"][0]
    finally:
        product_service.redis = original_redis


def test_numeric_precision_integrity(db: Session):
    """
    Verify that our Numeric(10, 2) columns correctly handle precision,
    bridging the parity gap between SQLite (lenient) and MySQL (strict).
    """
    from app.models.product import ProductSKU, Product
    from decimal import Decimal
    
    p = Product(name="Precision Test", brand="Test", category="Test")
    db.add(p)
    db.flush()
    
    # Intentionally use a high-precision decimal
    precise_price = Decimal("123.456789") 
    sku = ProductSKU(
        product_id=p.id,
        platform="JD",
        platform_sku_id="precision_sku",
        title="Precision SKU",
        price=precise_price
    )
    db.add(sku)
    db.commit()
    db.refresh(sku)
    
    # In SQLite, this might stay a float/decimal, but our model specifies (10, 2).
    # We want to ensure that our application logic sees the correctly rounded value.
    assert sku.price == Decimal("123.46") # Standard rounding to 2 places
