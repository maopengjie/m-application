import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import Base, get_db
from app.models.user import User
from app.core.security import get_password_hash

import os
TEST_DB_PATH = "./test_permissions.db"
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
    # 1. Normal User
    user1 = User(
        username="normal_user",
        hashed_password=get_password_hash("pass"),
        real_name="Normal",
        roles=["user"],
        is_active=True
    )
    # 2. Admin User
    admin1 = User(
        username="admin_user",
        hashed_password=get_password_hash("pass"),
        real_name="Admin",
        roles=["admin"],
        is_active=True
    )
    db.add_all([user1, admin1])
    db.commit()
    db.close()
    
    with TestClient(app) as c:
        yield c
        
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()

def get_token_for(client, username):
    resp = client.post("/api/v1/auth/login", json={"username": username, "password": "pass"})
    return resp.json()["data"]["accessToken"]

def test_public_unauthorized(client):
    # Missing token -> 401
    resp = client.post("/api/v1/crawler/start", json={"target_url": "test"})
    assert resp.status_code == 401

def test_normal_user_forbidden_on_admin_route(client):
    token = get_token_for(client, "normal_user")
    
    # Crawler requires AC_100010 (Admin)
    resp = client.post(
        "/api/v1/crawler/start", 
        json={"target_url": "test"},
        headers={"Authorization": f"Bearer {token}"}
    )
    # They should be recognized, but forbidden
    assert resp.status_code == 403
    assert "Permission denied. Required code: AC_100010" in resp.json()["message"]

def test_admin_user_allowed_on_admin_route(client):
    token = get_token_for(client, "admin_user")
    
    # Crawler requires AC_100010
    resp = client.post(
        "/api/v1/crawler/trigger-update", 
        headers={"Authorization": f"Bearer {token}"}
    )
    # Should get past 401 and 403. Even if crawler fails functionally (500 or validation), authz succeeds.
    assert resp.status_code != 403
    assert resp.status_code != 401 
