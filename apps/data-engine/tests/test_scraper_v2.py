import pytest
from unittest.mock import patch, MagicMock
from decimal import Decimal
from datetime import datetime
from app.services.scraper import ScraperFactory
from app.services.collector_service import CollectorService
from app.models.product import ProductSKU, Product, PriceHistory
from app.models.task import CrawlTask
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.core.database import Base

# Setup In-Memory Test DB
engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)

def test_unsupported_platform_routing():
    """Verify that unsupported platforms return a clear error code."""
    sku = MagicMock(spec=ProductSKU)
    sku.platform = "Amazon"
    sku.platform_sku_id = "123"
    sku.price = 100.0
    
    result = ScraperFactory.scrape(sku)
    assert result.success is False
    assert result.error_code == "UNSUPPORTED_PLATFORM"

@pytest.mark.asyncio
async def test_jd_scraper_success_case():
    """Verify JDScraper correctly parses HTML."""
    from app.services.scraper.platform.jd import JDScraper
    sku = MagicMock(spec=ProductSKU)
    sku.platform = "JD"
    sku.platform_sku_id = "2000"
    sku.price = 1000.0
    sku.title = "Old Title"
    sku.buy_url = "https://item.jd.com/2000.html"
    sku.shop_name = "Original Shop"
    sku.original_price = 1100.0
    
    mock_html = """
    <div class="sku-name">New HUAWEI Watch GT 4</div>
    <div class="p-price"><span class="price">1488.00</span></div>
    <div class="shopName">Huawei Official Shop</div>
    <div class="store-prompt">有货</div>
    """
    
    scraper = JDScraper()
    with patch("app.utils.crawler.NetworkFetcher.fetch_http", return_value=mock_html):
        result = await scraper._async_scrape(sku)
        assert result.success is True
        assert result.price == 1488.0

@pytest.mark.asyncio
async def test_jd_scraper_failure_classification():
    """Verify JDScraper identifies blocked pages."""
    from app.services.scraper.platform.jd import JDScraper
    sku = MagicMock(spec=ProductSKU); sku.platform = "JD"; sku.platform_sku_id = "2001"; sku.price = 100.0
    sku.buy_url = "https://item.jd.com/2001.html"
    
    blocked_html = "<html><body>验证码校验</body></html>"
    
    scraper = JDScraper()
    with patch("app.utils.crawler.NetworkFetcher.fetch_http", return_value=blocked_html):
        result = await scraper._async_scrape(sku)
        assert result.success is False
        assert result.error_code == "BLOCKED"

def test_collector_full_persistence(db: Session):
    """Verify end-to-end collection persistence logic."""
    # 1. Setup Data
    product = Product(name="Test Watch", brand="Huawei")
    db.add(product)
    db.commit()
    
    sku = ProductSKU(
        product_id=product.id,
        platform="JD",
        platform_sku_id="test_sku",
        title="Original Title",
        price=Decimal("100.00"),
        buy_url="http://jd.com/test",
        shop_name="Old Shop"
    )
    db.add(sku)
    db.commit()
    
    # 2. Mock Scraper Result
    from app.services.scraper.models import ScrapeResult
    mock_result = ScrapeResult(success=True, platform="JD", sku_id="test_sku", price=88.88)
    
    service = CollectorService()
    # Path core factory
    with patch("app.services.scraper.ScraperFactory.scrape", return_value=mock_result):
        with patch("time.sleep", return_value=None):
            # This will use the REAL db session (in-memory sqlite)
            service.run_collection(db)
    
    db.refresh(sku)
    assert float(sku.price) == 88.88
    
    # Check history
    assert db.query(PriceHistory).filter(PriceHistory.sku_id == sku.id).count() >= 1
    # Check task
    task = db.query(CrawlTask).order_by(CrawlTask.id.desc()).first()
    assert task.status in ["success", "partial_success"]
    assert task.success_count == 1
