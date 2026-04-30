from typing import List, Optional
from .base import BasePlatformScraper
from .models import ScrapeResult
from .platform.jd import JDScraper
from .platform.tmall import TmallScraper
from .platform.pdd import PDDScraper
from .platform.mock import MockScraper

class ScraperFactory:
    """
    Registry for all platform-specific scrapers.
    Responsible for dispatching SKUs to JD, Tmall, PDD or other scrapers.
    """
    _scrapers: List[BasePlatformScraper] = [
        JDScraper(),
        TmallScraper(),
        PDDScraper(),
        MockScraper()
    ]

    @classmethod
    def register(cls, scraper: BasePlatformScraper):
        """Register a new scraper implementation."""
        cls._scrapers.append(scraper)

    @classmethod
    def get_scraper(cls, sku: any) -> Optional[BasePlatformScraper]:
        """
        Find the first scraper that supports the given SKU.
        Checks for explicit platform matches or URL support.
        """
        platform = str(getattr(sku, 'platform', '')).upper()
        
        # 1. Try explicit support first
        for scraper in cls._scrapers:
            if scraper.supports(sku):
                return scraper
        
        # 2. Fallback: Direct platform name match if supports() was too strict
        mapping = {
            "JD": JDScraper,
            "TMALL": TmallScraper,
            "TAOBAO": TmallScraper,
            "PDD": PDDScraper,
            "MOCK": MockScraper
        }
        if platform in mapping:
            # Return a fresh instance or existing from _scrapers
            scraper_cls = mapping[platform]
            for s in cls._scrapers:
                if isinstance(s, scraper_cls):
                    return s
                    
        return None

    @classmethod
    def scrape(cls, sku: any) -> ScrapeResult:
        """
        Main entry point for scraping a SKU.
        Dispatches to the correct platform scraper or returns unsupported_platform.
        """
        scraper = cls.get_scraper(sku)
        platform = getattr(sku, 'platform', 'unknown')
        sku_id = getattr(sku, 'platform_sku_id', 'unknown')

        # 1. Routing Guard: Ensure we actually support this platform
        if not scraper:
            return ScrapeResult(
                success=False,
                platform=platform,
                sku_id=sku_id,
                error_code="UNSUPPORTED_PLATFORM",
                error_message=f"No specialized scraper implemented for platform: {platform}"
            )

        # 2. Configuration Guard: Ensure platform is active
        from app.utils.crawler import CrawlerConfig
        if platform.upper() not in [p.upper() for p in CrawlerConfig.ENABLED_PLATFORMS]:
            return ScrapeResult(
                success=False,
                platform=platform,
                sku_id=sku_id,
                error_code="PLATFORM_DISABLED",
                error_message=f"Platform {platform} is currently disabled in system configuration."
            )
        
        try:
            return scraper.scrape(sku)
        except Exception as e:
            return ScrapeResult(
                success=False,
                platform=platform,
                sku_id=sku_id,
                error_code="SCRAPE_ERROR",
                error_message=str(e)
            )
