from .base import BaseScraper, BasePlatformScraper
from .models import ScrapeResult
from .factory import ScraperFactory
from .platform.jd import JDScraper
from .platform.mock import MockScraper

def init_scrapers():
    """Register all available scraper implementations."""
    ScraperFactory.register(JDScraper())
    ScraperFactory.register(MockScraper())

# Initialize on import
init_scrapers()

__all__ = ["BaseScraper", "BasePlatformScraper", "ScrapeResult", "ScraperFactory"]
