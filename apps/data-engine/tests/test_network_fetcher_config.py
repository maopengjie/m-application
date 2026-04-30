import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from app.utils.crawler import NetworkFetcher, CrawlerConfig

@pytest.mark.asyncio
async def test_network_fetcher_respects_proxy():
    """Verify that NetworkFetcher passes proxies to httpx and playwright."""
    CrawlerConfig.PROXY_URL = "http://myproxy:8080"
    
    # Test HTTP Proxy
    with patch("httpx.AsyncClient") as mock_client:
        mock_instance = mock_client.return_value.__aenter__.return_value
        mock_instance.get = AsyncMock(return_value=MagicMock(status_code=200, text="ok"))
        
        await NetworkFetcher.fetch_http("http://example.com")
        
        args, kwargs = mock_client.call_args
        assert kwargs.get("proxy") == "http://myproxy:8080"

    # Test Browser Proxy (using a simplified mock)
    with patch("app.utils.crawler.async_playwright") as mock_pw:
        mock_p = mock_pw.return_value.__aenter__.return_value
        mock_launch = mock_p.chromium.launch = AsyncMock()
        mock_browser = mock_launch.return_value = MagicMock()
        mock_browser.new_context = AsyncMock()
        mock_browser.close = AsyncMock()

        CrawlerConfig.ENABLE_BROWSER_FALLBACK = True
        
        try:
            await NetworkFetcher.fetch_browser("http://example.com")
        except:
            pass 
            
        args, kwargs = mock_launch.call_args
        assert kwargs["proxy"]["server"] == "http://myproxy:8080"

@pytest.mark.asyncio
async def test_network_fetcher_browser_fallback_switch():
    """Verify that fetch_browser raises error when fallback is disabled."""
    CrawlerConfig.ENABLE_BROWSER_FALLBACK = False
    
    with pytest.raises(Exception) as excinfo:
        await NetworkFetcher.fetch_browser("http://example.com")
    
    assert "Browser fallback is disabled" in str(excinfo.value)
    
    # Cleanup
    CrawlerConfig.ENABLE_BROWSER_FALLBACK = True
    CrawlerConfig.PROXY_URL = None
