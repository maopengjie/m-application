import logging
import asyncio
from bs4 import BeautifulSoup
from typing import Optional, List, Dict
from ..base import BasePlatformScraper
from ..models import ScrapeResult
from app.utils.crawler import NetworkFetcher, CrawlerConfig

logger = logging.getLogger(__name__)

class PDDScraper(BasePlatformScraper):
    """
    Scraper implementation for Pinduoduo (PDD).
    PDD is highly dynamic and almost always requires Playwright.
    """
    def supports(self, sku: any) -> bool:
        return getattr(sku, 'platform', '') == "PDD"

    def scrape(self, sku: any) -> ScrapeResult:
        """Synchronous wrapper for internal callers."""
        import asyncio
        return asyncio.run(self._async_scrape(sku))

    async def _async_scrape(self, sku: any) -> ScrapeResult:
        url = sku.buy_url
        max_local_retries = 2
        last_result = None

        for attempt in range(max_local_retries + 1):
            html = None
            try:
                # 1. Fetch HTML (Favor Browser for PDD due to anti-scraper)
                try:
                    # Try browser directly for PDD or a very robust HTTP client
                    if CrawlerConfig.ENABLE_BROWSER_FALLBACK:
                        html = await NetworkFetcher.fetch_browser(
                            url, 
                            selector="[class*='enable_check']", 
                            wait_until="networkidle"
                        )
                    else:
                        html = await NetworkFetcher.fetch_http(url)
                except Exception as e:
                    logger.warning(f"PDD fetch attempt {attempt+1} failed: {e}")
                    last_result = ScrapeResult(success=False, platform="PDD", sku_id=sku.platform_sku_id, 
                                            error_code="FETCH_ERROR", error_message=str(e))
                
                if not html:
                    last_result = ScrapeResult(success=False, platform="PDD", sku_id=sku.platform_sku_id, 
                                            error_code="EMPTY_RESULT", error_message="No HTML content")
                else:
                    # 2. Block Check
                    if any(x in html for x in ["验证码", "antispam", "f-captcha"]):
                        return ScrapeResult(success=False, platform="PDD", sku_id=sku.platform_sku_id, 
                                            error_code="BLOCKED", error_message="PDD Antispam Triggered")

                    # 3. Parse Content
                    try:
                        soup = BeautifulSoup(html, "html.parser")
                        
                        # PDD often obscures classes, use more generic or multiple targets
                        title, title_tag = self._get_text_from_selectors([
                            "[class*='goods-name']", ".goods-title", "h1"
                        ], soup)
                        
                        price_str, price_tag = self._get_text_from_selectors([
                            "[class*='group-price']", ".p-price", ".price"
                        ], soup)

                        if not title_tag and not price_tag:
                            snippet = html[:500].replace("\n", " ") + "..."
                            return ScrapeResult(success=False, platform="PDD", sku_id=sku.platform_sku_id, 
                                                error_code="PARSE_ERROR", 
                                                error_message="Identity mismatch/Empty content",
                                                raw_payload={"html_snippet": snippet})

                        # 4. Success Path
                        return self._process_success_result(sku, title, price_str)
                    except Exception as parse_e:
                        return ScrapeResult(success=False, platform="PDD", sku_id=sku.platform_sku_id, 
                                            error_code="PARSE_ERROR", error_message=str(parse_e))

            except Exception as fe:
                last_result = ScrapeResult(success=False, platform="PDD", sku_id=sku.platform_sku_id, 
                                        error_code="FETCH_ERROR", error_message=str(fe))
            
            # Retry Decision
            if last_result and last_result.error_code in ["FETCH_ERROR", "TIMEOUT", "EMPTY_RESULT"]:
                if attempt < max_local_retries:
                    await asyncio.sleep((attempt + 1) * 3) # More aggressive wait for PDD
                    continue
            break

        return last_result

    def _get_text_from_selectors(self, selectors, soup):
        for s in selectors:
            tag = soup.select_one(s)
            if tag and tag.get_text(strip=True):
                return tag.get_text(strip=True), tag
        return None, None

    def _process_success_result(self, sku, title, price_str):
        try:
            import re
            p_match = re.search(r"(\d+\.?\d*)", price_str.replace(",", ""))
            price = float(p_match.group(1)) if p_match else 0.0
            
            return ScrapeResult(
                success=True,
                platform="PDD",
                sku_id=sku.platform_sku_id,
                price=price,
                title=title or sku.title,
                stock_status="unknown" # PDD stock status is harder to parse reliably
            )
        except Exception as e:
            return ScrapeResult(success=False, platform="PDD", sku_id=sku.platform_sku_id, 
                                error_code="PARSE_ERROR", error_message=f"PDD price extraction fail: {e}")
