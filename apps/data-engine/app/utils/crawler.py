import asyncio
import random
import logging
from typing import Optional, Dict, Any, Callable
from playwright.async_api import async_playwright
import httpx

logger = logging.getLogger(__name__)

class CrawlerConfig:
    """Centralized configuration for network fetching and scraper behavior."""
    DEFAULT_TIMEOUT = 30
    BROWSER_TIMEOUT = 60000
    MAX_RETRIES = 3
    
    # Concurrency & Throttling
    HTTP_CONCURRENCY = 5
    JD_REQUEST_INTERVAL = 1.5      # Seconds between JD requests
    
    # Platform Toggles & Governance
    ENABLED_PLATFORMS = ["JD", "Tmall", "PDD", "Mock"]
    JD_ENABLED = True
    TMALL_ENABLED = True
    PDD_ENABLED = True

    # Monitoring & Smoke Test Config
    PLATFORM_SMOKE_SAMPLE_SIZE = 5 # Number of items to probe per platform
    ALERT_FAILURE_THRESHOLD = 0.5  # Trigger alert if success rate falls below 50%

    # Network Resilience
    PROXY_URL = None               # Production proxy endpoint
    ENABLE_BROWSER_FALLBACK = True
    RETRYABLE_ERROR_CODES = [429, 500, 502, 503, 504]
    BLOCK_THRESHOLD = 5            # Consecutive BLOCKED results
    
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1"
    ]

    @classmethod
    def get_random_headers(cls) -> Dict[str, str]:
        return {
            "User-Agent": random.choice(cls.USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
        }

class NetworkFetcher:
    """
    Submerged utility layer for all network fetching needs.
    Supports HTTP (Fast) and Playwright (Dynamic) with automatic retries.
    """

    @staticmethod
    async def fetch_with_retry(
        func: Callable, 
        *args, 
        max_retries: int = CrawlerConfig.MAX_RETRIES, 
        **kwargs
    ) -> Any:
        """Utility wrapper for async retries with exponential backoff."""
        last_exception = None
        for attempt in range(max_retries):
            try:
                # Random jitter between attempts
                if attempt > 0:
                    await asyncio.sleep(random.uniform(1, 3) * attempt)
                return await func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                logger.warning(f"Fetch attempt {attempt + 1} failed: {e}")
        
        logger.error(f"Max retries reached. Final failure: {last_exception}")
        raise last_exception

    @classmethod
    async def fetch_http(
        cls, 
        url: str, 
        headers: Optional[Dict] = None, 
        timeout: int = CrawlerConfig.DEFAULT_TIMEOUT
    ) -> str:
        """Fetch page content using httpx (stateless/fast)."""
        headers = headers or CrawlerConfig.get_random_headers()
        proxies = CrawlerConfig.PROXY_URL if CrawlerConfig.PROXY_URL else None
        
        async def _do_fetch():
            async with httpx.AsyncClient(
                headers=headers, 
                timeout=timeout, 
                follow_redirects=True,
                proxy=proxies
            ) as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.text
                
        return await cls.fetch_with_retry(_do_fetch)

    @classmethod
    async def fetch_browser(
        cls, 
        url: str, 
        selector: Optional[str] = None, 
        timeout: int = CrawlerConfig.BROWSER_TIMEOUT,
        wait_until: str = "networkidle"
    ) -> str:
        """Fetch page content using Playwright (stateful/JS-enabled)."""
        if not CrawlerConfig.ENABLE_BROWSER_FALLBACK:
            raise Exception("Browser fallback is disabled in config.")

        headers = CrawlerConfig.get_random_headers()
        proxy_cfg = {"server": CrawlerConfig.PROXY_URL} if CrawlerConfig.PROXY_URL else None

        async def _do_fetch():
            async with async_playwright() as p:
                launch_kwargs = {"headless": True}
                if proxy_cfg:
                    launch_kwargs["proxy"] = proxy_cfg
                    
                browser = await p.chromium.launch(**launch_kwargs)
                # Reuse random UA for consistency in the session
                context = await browser.new_context(user_agent=headers["User-Agent"])
                page = await context.new_page()
                try:
                    await page.goto(url, wait_until=wait_until, timeout=timeout)
                    if selector:
                        await page.wait_for_selector(selector, timeout=timeout)
                    return await page.content()
                finally:
                    await browser.close()
        
        return await cls.fetch_with_retry(_do_fetch)

def fetch_page_content(url: str, selector: Optional[str] = None, use_playwright: bool = False) -> str:
    """Backward compatibility wrapper for sync callers."""
    if use_playwright:
        return asyncio.run(NetworkFetcher.fetch_browser(url, selector))
    return asyncio.run(NetworkFetcher.fetch_http(url))
