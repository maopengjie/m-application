import pytest
from unittest.mock import patch, MagicMock
from app.services.scraper.platform.jd import JDScraper
from app.models.product import ProductSKU

@pytest.mark.asyncio
async def test_jd_retry_on_fetch_error():
    """Verify that JDScraper retries on FETCH_ERROR but eventually fails."""
    sku = MagicMock(spec=ProductSKU)
    sku.platform = "JD"
    sku.platform_sku_id = "1000"
    sku.sku_id = "1000" # for safety
    sku.buy_url = "https://item.jd.com/1000.html"
    sku.price = 1000.0
    sku.title = "Old Title"
    
    scraper = JDScraper()
    
    with patch("app.utils.crawler.NetworkFetcher.fetch_http", side_effect=Exception("Connection Timeout")):
        with patch("app.utils.crawler.NetworkFetcher.fetch_browser", side_effect=Exception("Browser Timeout")):
            with patch("asyncio.sleep", return_value=None) as mock_sleep:
                result = await scraper._async_scrape(sku)
                
                assert result.success is False
                assert result.error_code == "TIMEOUT"
                assert mock_sleep.call_count == 2 

@pytest.mark.asyncio
async def test_jd_no_retry_on_blocked():
    """Verify that JDScraper does NOT retry when blocked by a captcha."""
    sku = MagicMock(spec=ProductSKU)
    sku.platform = "JD"
    sku.platform_sku_id = "1001"
    sku.buy_url = "https://item.jd.com/1001.html"
    sku.price = 1000.0
    sku.title = "Old Title"
    
    scraper = JDScraper()
    blocked_html = "<html><body>请向右滑动验证码</body></html>"
    
    with patch("app.utils.crawler.NetworkFetcher.fetch_http", return_value=blocked_html):
        with patch("asyncio.sleep", return_value=None) as mock_sleep:
            result = await scraper._async_scrape(sku)
            
            assert result.success is False
            assert result.error_code == "BLOCKED"
            assert mock_sleep.call_count == 0 

@pytest.mark.asyncio
async def test_jd_parse_error_audit_snippet():
    """Verify that PARSE_ERROR captures an HTML snippet."""
    sku = MagicMock(spec=ProductSKU)
    sku.platform = "JD"
    sku.platform_sku_id = "1002"
    sku.buy_url = "https://item.jd.com/1002.html"
    sku.price = 1000.0
    sku.title = "Old Title"
    
    scraper = JDScraper()
    garbage_html = "<html><body><h1>Unknown Page</h1></body></html>"
    
    with patch("app.utils.crawler.NetworkFetcher.fetch_http", return_value=garbage_html):
        result = await scraper._async_scrape(sku)
        
        # If it returns FETCH_ERROR, we need to know why. 
        # But here I'm adding a safeguard - ensure sku.platform_sku_id IS a string.
        assert result.success is False
        assert result.error_code == "PARSE_ERROR"
        assert "html_snippet" in result.raw_payload
