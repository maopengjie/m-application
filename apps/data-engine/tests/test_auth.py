import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import Base, get_db
from app.models.user import User
from app.core.security import get_password_hash

# Setup in-memory SQLite for testing real database interactions safely
import os
TEST_DB_PATH = "./test_auth.db"
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
    
    # Setup the DB schema
    Base.metadata.create_all(bind=engine)
    
    # Seed a test user
    db = TestingSessionLocal()
    test_user = User(
        username="testuser",
        hashed_password=get_password_hash("password123"),
        real_name="Test User",
        roles=["user"],
        is_active=True
    )
    db.add(test_user)
    db.commit()
    db.close()
    
    with TestClient(app) as c:
        yield c
        
    # Teardown
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()

def test_login_success(client):
    response = client.post(
        "/api/v1/auth/login", 
        json={"username": "testuser", "password": "password123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    assert "accessToken" in data["data"]
    
    # Verify refresh token behaves correctly and is set in cookie
    assert "jwt" in response.cookies

def test_login_failure_and_lockout(client):
    # Try 5 wrong passwords
    for _ in range(5):
        response = client.post(
            "/api/v1/auth/login", 
            json={"username": "testuser", "password": "wrongpassword"}
        )
        assert response.status_code == 403
        assert "Username or password is incorrect" in response.json()["message"]
        
    # 6th attempt with correct password should STILL fail because account is locked
    response = client.post(
        "/api/v1/auth/login", 
        json={"username": "testuser", "password": "password123"}
    )
    assert response.status_code == 403
    assert "Username or password is incorrect or account is locked" in response.json()["message"]

def test_admin_unlock(client):
    # First, authenticate as super/admin to unlock
    db = TestingSessionLocal()
    admin_user = User(
        username="adminuser",
        hashed_password=get_password_hash("admin123"),
        real_name="Admin",
        roles=["admin"],
        is_active=True
    )
    db.add(admin_user)
    db.commit()
    
    # Verify the locked user exists and get their ID
    locked_user = db.query(User).filter_by(username="testuser").first()
    target_id = locked_user.id
    db.close()
    
    # Login admin
    admin_response = client.post(
        "/api/v1/auth/login", 
        json={"username": "adminuser", "password": "admin123"}
    )
    admin_token = admin_response.json()["data"]["accessToken"]
    
    # Unlock target
    unlock_response = client.post(
        f"/api/v1/user/{target_id}/unlock",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert unlock_response.status_code == 200
    
    # Target can login again
    success_response = client.post(
        "/api/v1/auth/login", 
        json={"username": "testuser", "password": "password123"}
    )
    assert success_response.status_code == 200

def test_refresh_token_rotation(client):
    # Login to get initial cookies
    login_resp = client.post(
        "/api/v1/auth/login", 
        json={"username": "testuser", "password": "password123"}
    )
    original_jwt_cookie = login_resp.cookies.get("jwt")
    assert original_jwt_cookie is not None
    
    # Hit refresh endpoint
    refresh_resp = client.post("/api/v1/auth/refresh", cookies={"jwt": original_jwt_cookie})
    assert refresh_resp.status_code == 200
    assert "accessToken" in refresh_resp.json()["data"]
    
    # Verify the cookie was rotated
    new_jwt_cookie = refresh_resp.cookies.get("jwt")
    assert new_jwt_cookie is not None
    assert new_jwt_cookie != original_jwt_cookie
