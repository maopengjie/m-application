import time
import random
import httpx
import logging
from abc import ABC, abstractmethod
from typing import Optional
from .models import ScrapeResult

logger = logging.getLogger(__name__)

class BaseScraper:
    def __init__(self, timeout: int = 10, max_retries: int = 3):
        self.timeout = timeout
        self.max_retries = max_retries
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }

    def fetch_url(self, url: str) -> Optional[str]:
        """Fetch URL with retry logic and random delay for rate limiting."""
        for attempt in range(self.max_retries):
            try:
                # Random delay between 1-3 seconds to stay under the radar
                time.sleep(random.uniform(1, 3))
                
                with httpx.Client(headers=self.headers, timeout=self.timeout) as client:
                    response = client.get(url)
                    response.raise_for_status()
                    return response.text
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt == self.max_retries - 1:
                    logger.error(f"Failed to fetch {url} after {self.max_retries} attempts.")
                    return None
        return None

class BasePlatformScraper(ABC):
    """
    Abstract base interface for all platform-specific scrapers.
    Ensures a consistent protocol for the scraper registry.
    """
    @abstractmethod
    def supports(self, sku: any) -> bool:
        """
        Return True if this scraper instance can handle the given SKU.
        Typically checks sku.platform or URL patterns.
        """
        pass

    @abstractmethod
    def scrape(self, sku: any) -> ScrapeResult:
        """
        Execute the scraping logic for a specific SKU.
        Must return a ScrapeResult object.
        """
        pass
