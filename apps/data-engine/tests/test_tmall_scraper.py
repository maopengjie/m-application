import pytest
from app.services.scraper.platform.tmall import TmallScraper
from app.services.scraper.models import ScrapeResult

class MockSKU:
    def __init__(self, platform="Tmall"):
        self.platform = platform
        self.platform_sku_id = "test_tmall_id"
        self.buy_url = "https://detail.tmall.com/item.htm?id=123"
        self.title = "Old Title"

def test_tmall_scraper_supports():
    scraper = TmallScraper()
    assert scraper.supports(MockSKU("Tmall")) is True
    assert scraper.supports(MockSKU("Taobao")) is True
    assert scraper.supports(MockSKU("JD")) is False

from unittest.mock import patch

@pytest.mark.asyncio
async def test_tmall_scraper_parse_success():
    scraper = TmallScraper()
    sku = MockSKU()
    
    # Mock network fetch
    mock_html = """
    <html>
        <div class="tm-detail-hd"><h1>Genuine Tmall Product</h1></div>
        <span class="tm-price">199.00</span>
    </html>
    """
    with patch("app.utils.crawler.NetworkFetcher.fetch_http") as mock_fetch:
        mock_fetch.return_value = mock_html
        result = await scraper._async_scrape(sku)
        assert result.success is True
        assert result.price == 199.00
        assert "Genuine Tmall Product" in result.title

@pytest.mark.asyncio
async def test_tmall_scraper_blocked():
    scraper = TmallScraper()
    sku = MockSKU()
    
    # Mock captcha page
    with patch("app.utils.crawler.NetworkFetcher.fetch_http") as mock_fetch:
        mock_fetch.return_value = "验证码 check your human status"
        result = await scraper._async_scrape(sku)
        assert result.success is False
        assert result.error_code == "BLOCKED"
