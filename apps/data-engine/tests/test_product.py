import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
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
        # Restore mock to avoid breaking subsequent tests if added
        product_service.redis = original_redis
