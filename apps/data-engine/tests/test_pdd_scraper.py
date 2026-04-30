import pytest
from app.services.scraper.platform.pdd import PDDScraper
from app.services.scraper.models import ScrapeResult

class MockSKU:
    def __init__(self, platform="PDD"):
        self.platform = platform
        self.platform_sku_id = "test_pdd_id"
        self.buy_url = "https://mobile.yangkeduo.com/goods.html?id=456"
        self.title = "Old PDD Title"

def test_pdd_scraper_supports():
    scraper = PDDScraper()
    assert scraper.supports(MockSKU("PDD")) is True
    assert scraper.supports(MockSKU("JD")) is False

from unittest.mock import patch

@pytest.mark.asyncio
async def test_pdd_scraper_parse_success():
    scraper = PDDScraper()
    sku = MockSKU()
    
    # Mock browser fetch
    mock_html = """
    <html>
        <div class="goods-name">PDD Best Deal</div>
        <div class="group-price">9.9</div>
    </html>
    """
    with patch("app.utils.crawler.NetworkFetcher.fetch_browser") as mock_browser:
        mock_browser.return_value = mock_html
        with patch("app.utils.crawler.CrawlerConfig.ENABLE_BROWSER_FALLBACK", True):
            result = await scraper._async_scrape(sku)
            assert result.success is True
            assert result.price == 9.9
            assert result.title == "PDD Best Deal"

@pytest.mark.asyncio
async def test_pdd_scraper_parse_error():
    scraper = PDDScraper()
    sku = MockSKU()
    
    # Mock messy HTML
    with patch("app.utils.crawler.NetworkFetcher.fetch_http") as mock_fetch:
        mock_fetch.return_value = "<html>Empty</html>"
        with patch("app.utils.crawler.CrawlerConfig.ENABLE_BROWSER_FALLBACK", False):
            result = await scraper._async_scrape(sku)
            assert result.success is False
            assert result.error_code == "PARSE_ERROR"
