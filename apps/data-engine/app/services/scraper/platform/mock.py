import random
from ..base import BasePlatformScraper
from ..models import ScrapeResult

class MockScraper(BasePlatformScraper):
    """
    A realistic mock scraper that follows the protocol.
    Used for integration testing and the 'simulation' mode.
    """
    def supports(self, sku: any) -> bool:
        # This mock scraper ONLY supports the 'MOCK' platform for explicit testing
        return getattr(sku, 'platform', '') == "MOCK"

    def scrape(self, sku: any) -> ScrapeResult:
        # Simulate a real scraping response
        old_price = float(sku.price)
        fluctuation = random.uniform(-0.02, 0.02)
        new_price = round(old_price * (1 + fluctuation), 2)
        
        return ScrapeResult(
            success=True,
            platform=sku.platform,
            sku_id=sku.platform_sku_id,
            price=new_price,
            original_price=sku.original_price,
            title=sku.title,
            shop_name=sku.shop_name,
            buy_url=sku.buy_url,
            raw_payload={"simulated": True}
        )
