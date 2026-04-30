import pytest
from unittest.mock import patch, MagicMock
from app.services.collector_service import CollectorService
from app.models.product import ProductSKU
from app.services.scraper.models import ScrapeResult
from sqlalchemy.orm import Session
from datetime import datetime

def test_collector_error_breakdown_logic():
    """Verify that CollectorService aggregates error types correctly."""
    db = MagicMock(spec=Session)
    
    # 1. Mock NO existing running task (to avoid HTTPException 409)
    db.query.return_value.filter.return_value.first.return_value = None
    
    # 2. Setup Mock SKUs
    sku1 = MagicMock(spec=ProductSKU); sku1.id = 1; sku1.platform = "JD"; sku1.price = 100.0; sku1.platform_sku_id = "p1"; sku1.shop_name = "s1"
    sku2 = MagicMock(spec=ProductSKU); sku2.id = 2; sku2.platform = "JD"; sku2.price = 200.0; sku2.platform_sku_id = "p2"; sku2.shop_name = "s2"
    sku3 = MagicMock(spec=ProductSKU); sku3.id = 3; sku3.platform = "Tmall"; sku3.price = 300.0; sku3.platform_sku_id = "p3"; sku3.shop_name = "s3"
    
    # Mock search for SKUs (filter(...).all())
    db.query.return_value.filter.return_value.all.return_value = [sku1, sku2, sku3]
    
    # 3. Setup Task Creation Mock
    from app.models.task import CrawlTask
    task = CrawlTask(id=99, status="running", start_time=datetime.now(), total_count=3)
    # This mock session should return THIS task when queried for the latest one
    db.query.return_value.filter.return_value.order_by.return_value.first.return_value = task
    
    # 4. Scrape Results
    res_success = ScrapeResult(success=True, platform="JD", sku_id="p1", price=99.0)
    res_blocked = ScrapeResult(success=False, platform="JD", sku_id="p2", error_code="BLOCKED")
    res_timeout = ScrapeResult(success=False, platform="Tmall", sku_id="p3", error_code="TIMEOUT")
    
    service = CollectorService()
    
    with patch("app.services.scraper.ScraperFactory.scrape") as mock_scrape:
        mock_scrape.side_effect = [res_success, res_blocked, res_timeout]
        with patch("time.sleep", return_value=None):
            service.run_collection(db)
        
        # Verify
        summary = task.metadata_json["summary"]
        assert summary["error_breakdown"]["BLOCKED"] == 1
        assert summary["error_breakdown"]["TIMEOUT"] == 1
        assert summary["success_rate"] == 33.33 
