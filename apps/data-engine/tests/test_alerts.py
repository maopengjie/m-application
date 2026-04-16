import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app
from app.models.product import Product, ProductSKU, PriceAlert
from app.services.alert_service import AlertService
from app.services.collector_service import CollectorService

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

def test_alert_deletion(db):
    sku = ProductSKU(product_id=1, platform="JD", platform_sku_id="s1", title="T", price=100)
    db.add(sku)
    db.flush()
    
    alert_service = AlertService()
    alert = alert_service.create_alert(db, {"user_id": 1, "sku_id": sku.id, "target_price": 50})
    alert_id = alert.id
    
    success = alert_service.delete_alert(db, alert_id)
    assert success is True
    
    res = db.query(PriceAlert).filter(PriceAlert.id == alert_id).first()
    assert res is None
