from datetime import datetime, timezone
from fastapi import HTTPException
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app
from app.models.product import Product, ProductSKU, PriceAlert, Coupon
from app.services.alert_service import AlertService

# Use in-memory SQLite for fast integration testing
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


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


def test_alert_trigger_cycle(db):
    # 1. Setup Data
    product = Product(name="Test Phone", brand="Test", category="Electronics")
    db.add(product)
    db.flush()
    
    sku = ProductSKU(
        product_id=product.id,
        platform="JD",
        platform_sku_id="test_sku",
        title="Test SKU",
        price=5000.0,
        original_price=6000.0
    )
    db.add(sku)
    db.flush()
    
    # 2. Create Alert for price 4800
    alert_service = AlertService()
    alert = alert_service.create_alert(db, {
        "user_id": 1,
        "sku_id": sku.id,
        "target_price": 4800.0
    })
    
    assert alert.id is not None
    assert alert.is_triggered is False
    
    # 3. Update price to 4900 (not triggered)
    sku.price = 4900.0
    db.commit()
    
    alert_service.check_alerts(db)
    db.refresh(alert)
    assert alert.is_triggered is False
    
    # 4. Update price to 4700 (triggered)
    sku.price = 4700.0
    db.commit()
    
    triggered = alert_service.check_alerts(db)
    db.refresh(alert)
    
    assert len(triggered) == 1
    assert alert.is_triggered is True
    assert alert.status == "triggered"

def test_alert_deletion_ownership(db):
    sku = ProductSKU(product_id=1, platform="JD", platform_sku_id="s1", title="T", price=100)
    db.add(sku)
    db.flush()
    
    alert_service = AlertService()
    alert = alert_service.create_alert(db, {"user_id": 1, "sku_id": sku.id, "target_price": 50})
    alert_id = alert.id
    
    # Attempt delete by another user (ID 2)
    success = alert_service.delete_alert(db, alert_id, user_id=2)
    assert success is False # Should fail because user 2 doesn't own it
    
    # Verify alert still exists
    assert db.query(PriceAlert).filter(PriceAlert.id == alert_id).first() is not None
    
    # Delete by owner (ID 1)
    success = alert_service.delete_alert(db, alert_id, user_id=1)
    assert success is True
    assert db.query(PriceAlert).filter(PriceAlert.id == alert_id).first() is None

def test_alert_status_aware_scanning(db):
    sku = ProductSKU(product_id=1, platform="JD", platform_sku_id="s2", title="T", price=100)
    db.add(sku)
    db.flush()
    
    alert_service = AlertService()
    alert = alert_service.create_alert(db, {"user_id": 1, "sku_id": sku.id, "target_price": 80})
    
    # Manually pause the alert
    alert.status = "paused"
    db.commit()
    
    # Price drops below target
    sku.price = 70
    db.commit()
    
    # Scan should ignore paused alert
    triggered = alert_service.check_alerts(db)
    assert len(triggered) == 0
    db.refresh(alert)
    assert alert.is_triggered is False

def test_alert_invalid_sku_rejection(db):
    alert_service = AlertService()
    with pytest.raises(HTTPException) as excinfo:
        alert_service.create_alert(db, {"user_id": 1, "sku_id": 9999, "target_price": 50})
    assert excinfo.value.status_code == 404

def test_alert_duplicate_prevention(db):
    sku = ProductSKU(product_id=1, platform="JD", platform_sku_id="s3", title="T", price=100)
    db.add(sku)
    db.flush()
    
    alert_service = AlertService()
    alert_service.create_alert(db, {"user_id": 1, "sku_id": sku.id, "target_price": 50})
    
    # Try creating same alert again for same user + SKU
    with pytest.raises(HTTPException) as excinfo:
        alert_service.create_alert(db, {"user_id": 1, "sku_id": sku.id, "target_price": 40})
    assert excinfo.value.status_code == 400

def test_alert_trigger_price_with_coupons(db):
    sku = ProductSKU(product_id=1, platform="JD", platform_sku_id="s4", title="T", price=1000)
    db.add(sku)
    db.flush()
    
    # 1. Create alert for 850
    alert_service = AlertService()
    alert = alert_service.create_alert(db, {"user_id": 1, "sku_id": sku.id, "target_price": 850})
    
    # 2. Add coupon for -200 -> final price 800
    coupon = Coupon(sku_id=sku.id, amount=200, title="-200", type="coupon")
    db.add(coupon)
    db.commit()
    
    # 3. Scan alerts
    triggered = alert_service.check_alerts(db)
    assert len(triggered) == 1
    
    db.refresh(alert)
    assert alert.is_triggered is True
    assert alert.triggered_price == 800.0 # Should be final price, not base price 1000
