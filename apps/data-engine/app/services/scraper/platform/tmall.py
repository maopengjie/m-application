import logging
import asyncio
from bs4 import BeautifulSoup
from typing import Optional, List, Dict
from ..base import BasePlatformScraper
from ..models import ScrapeResult
from app.utils.crawler import NetworkFetcher, CrawlerConfig

logger = logging.getLogger(__name__)

class TmallScraper(BasePlatformScraper):
    """
    Standard implementation for Tmall/Taobao scraping with multi-selector fallback.
    """
    def supports(self, sku: any) -> bool:
        return getattr(sku, 'platform', '') in ["Tmall", "Taobao"]

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
                # 1. Fetch HTML (Tmall often requires browser or careful headers)
                try:
                    html = await NetworkFetcher.fetch_http(url)
                except Exception as e:
                    logger.warning(f"Tmall HTTP fetch attempt {attempt+1} failed, trying browser...")
                    html = await NetworkFetcher.fetch_browser(
                        url, 
                        selector=".tm-price, .tb-main-title",
                        wait_until="domcontentloaded"
                    )

                if not html:
                    last_result = ScrapeResult(success=False, platform="Tmall", sku_id=sku.platform_sku_id, 
                                            error_code="EMPTY_RESULT", error_message="Received null HTML")
                else:
                    # 2. Block Check
                    if any(x in html for x in ["验证码", "login.taobao.com", "滑动验证"]):
                        return ScrapeResult(success=False, platform="Tmall", sku_id=sku.platform_sku_id, 
                                            error_code="BLOCKED", error_message="Detected Tmall/Taobao Block")

                    # 3. Parse Content
                    try:
                        soup = BeautifulSoup(html, "html.parser")
                        
                        # Extract Title
                        title, title_tag = self._get_text_from_selectors([
                            ".tm-detail-hd h1", ".tb-main-title", ".item-name", "h1"
                        ], soup)
                        
                        # Extract Price
                        price_str, price_tag = self._get_text_from_selectors([
                            ".tm-price", ".tb-rmb-num", "#J_StrPrice", ".price"
                        ], soup)

                        if not title_tag and not price_tag:
                            snippet = html[:500].replace("\n", " ") + "..."
                            return ScrapeResult(success=False, platform="Tmall", sku_id=sku.platform_sku_id, 
                                                error_code="PARSE_ERROR", 
                                                error_message="Structure mismatch",
                                                raw_payload={"html_snippet": snippet})

                        # 4. Success Path
                        return self._process_success_result(sku, title, price_str)
                    except Exception as parse_e:
                        snippet = html[:500].replace("\n", " ") + "..."
                        return ScrapeResult(success=False, platform="Tmall", sku_id=sku.platform_sku_id, 
                                            error_code="PARSE_ERROR", 
                                            error_message=f"Parse crash: {str(parse_e)}",
                                            raw_payload={"html_snippet": snippet})

            except Exception as fe:
                error_msg = str(fe).lower()
                code = "FETCH_ERROR"
                if "429" in error_msg: code = "RATE_LIMITED"
                elif "timeout" in error_msg: code = "TIMEOUT"
                
                last_result = ScrapeResult(success=False, platform="Tmall", sku_id=sku.platform_sku_id, 
                                        error_code=code, error_message=str(fe))
            
            # Retry Logic
            if last_result and last_result.error_code in ["FETCH_ERROR", "TIMEOUT", "RATE_LIMITED"]:
                if attempt < max_local_retries:
                    await asyncio.sleep((attempt + 1) * 2)
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
            # Clean price string
            import re
            p_match = re.search(r"(\d+\.?\d*)", price_str.replace(",", ""))
            price = float(p_match.group(1)) if p_match else 0.0
            
            return ScrapeResult(
                success=True,
                platform="Tmall",
                sku_id=sku.platform_sku_id,
                price=price,
                title=title or sku.title,
                stock_status="in_stock" # Default for Tmall if we reached here
            )
        except Exception as e:
            return ScrapeResult(success=False, platform="Tmall", sku_id=sku.platform_sku_id, 
                                error_code="PARSE_ERROR", error_message=f"Clean price error: {e}")
