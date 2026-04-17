import logging
from bs4 import BeautifulSoup
from ..base import BasePlatformScraper
from ..models import ScrapeResult
from app.utils.crawler import NetworkFetcher

logger = logging.getLogger(__name__)

class JDScraper(BasePlatformScraper):
    """
    Real implementation for JD (Jingdong) using Playwright + BeautifulSoup.
    """
    def supports(self, sku: any) -> bool:
        return getattr(sku, 'platform', '') == "JD"

    async def _async_scrape(self, sku: any) -> ScrapeResult:
        import asyncio
        # Construct URL safely
        url = getattr(sku, 'buy_url', None)
        if not url:
            sku_id = getattr(sku, 'platform_sku_id', None)
            if not sku_id:
                return ScrapeResult(success=False, platform="JD", sku_id="unknown", 
                                    error_code="INVALID_SKU", error_message="Missing SKU ID and URL")
            url = f"https://item.jd.com/{sku_id}.html"

        max_local_retries = 2
        last_result = None

        for attempt in range(max_local_retries + 1):
            html = None
            try:
                # 1. Fetch HTML (Try HTTP first for speed/stability)
                try:
                    html = await NetworkFetcher.fetch_http(url)
                except Exception as e:
                    logger.warning(f"JD HTTP fetch attempt {attempt+1} failed ({e}), trying browser...")
                    html = await NetworkFetcher.fetch_browser(
                        url, 
                        selector=".sku-name",
                        wait_until="domcontentloaded"
                    )

                if not html:
                    last_result = ScrapeResult(success=False, platform="JD", sku_id=sku.platform_sku_id, 
                                            error_code="EMPTY_RESULT", error_message="Received null HTML")
                else:
                    # 2. Check for Blocked/Captcha - (Do not retry BLOCKED)
                    if any(x in html for x in ["验证码", "captcha", "bot-detection", "deny.jd.com"]):
                        return ScrapeResult(success=False, platform="JD", sku_id=sku.platform_sku_id, 
                                            error_code="BLOCKED", error_message="Detected JD Captcha/Bot Block")

                    # 3. Parse Content (Internal parse failures should NOT retry)
                    try:
                        soup = BeautifulSoup(html, "html.parser")
                        
                        # Extract Title (with fallbacks)
                        title, title_tag = self._get_text_from_selectors([
                            ".sku-name", ".sku-name-main", "#name h1", 
                            ".item-name", ".detail-name", "h1"
                        ], soup)
                        
                        # Extract Price (with fallbacks)
                        price_str, price_tag = self._get_text_from_selectors([
                            ".p-price .price", "#jd-price", ".jd-price", 
                            "[class*='price-num']", "[class*='p-price'] .price",
                            "#price", ".p-price"
                        ], soup)

                        # If essential elements missing -> PARSE_ERROR (likely changed structure)
                        if not title_tag and not price_tag:
                            snippet = html[:500].replace("\n", " ") + "..."
                            return ScrapeResult(success=False, platform="JD", sku_id=sku.platform_sku_id, 
                                                error_code="PARSE_ERROR", 
                                                error_message="Essential elements missing. Structure might have changed.",
                                                raw_payload={"html_snippet": snippet})

                        # 4. Success Path
                        return self._process_success_result(sku, soup, title, price_str, title_tag, price_tag, url)
                    except Exception as parse_e:
                        snippet = html[:500].replace("\n", " ") + "..."
                        logger.error(f"JD Scraper Parsing error: {parse_e}")
                        return ScrapeResult(success=False, platform="JD", sku_id=sku.platform_sku_id, 
                                            error_code="PARSE_ERROR", 
                                            error_message=f"Parsing logic crash: {str(parse_e)}",
                                            raw_payload={"html_snippet": snippet})

            except Exception as fe:
                # Handle Network/Browser/Timeout errors (These ARE retryable)
                error_msg = str(fe).lower()
                code = "FETCH_ERROR"
                if "429" in error_msg or "too many requests" in error_msg:
                    code = "RATE_LIMITED"
                elif "timeout" in error_msg:
                    code = "TIMEOUT"
                
                last_result = ScrapeResult(success=False, platform="JD", sku_id=sku.platform_sku_id, 
                                        error_code=code, error_message=str(fe))
            
            # 5. Retry Logic Decision (Only for non-parsing, non-blocked failures)
            if last_result and last_result.error_code in ["FETCH_ERROR", "TIMEOUT", "RATE_LIMITED", "EMPTY_RESULT"]:
                if attempt < max_local_retries:
                    wait_time = (attempt + 1) * 2
                    logger.info(f"Retrying JD SKU {sku.platform_sku_id} (Attempt {attempt+2}/{max_local_retries+1}) in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                    continue
            
            break # If not retryable or max retries reached, break

        return last_result

    def _get_text_from_selectors(self, selectors, soup_obj):
        for s in selectors:
            tag = soup_obj.select_one(s)
            if tag:
                text = tag.get_text(strip=True)
                if text: return text, tag
        return None, None

    def _process_success_result(self, sku, soup, title, price_str, title_tag, price_tag, url):
        # Extract Shop Name (with fallbacks)
        shop_name, shop_tag = self._get_text_from_selectors([
            ".shopName", ".name a[title]", ".contact .name", 
            ".seller-infor a", ".J-shop-name", ".shop-name"
        ], soup)
        shop_name = shop_name or getattr(sku, 'shop_name', "未知店铺")

        # Extract Original Price (Market Price)
        orig_str, orig_tag = self._get_text_from_selectors([
            ".p-price-market", ".mr .price", ".market-price", ".old-price"
        ], soup)
        
        original_price = None
        if orig_str:
            try:
                import re
                match = re.search(r"(\d+\.?\d*)", orig_str.replace("￥", "").replace("¥", ""))
                if match:
                    original_price = float(match.group(1))
            except:
                pass

        # Extract Stock Status
        stock_str, stock_tag = self._get_text_from_selectors([
            ".store-prompt", "#store-prompt", ".summary-stock", 
            "#summary-stock", ".stock-status"
        ], soup)
        
        stock_status = "in_stock"
        if stock_str:
            if any(x in stock_str for x in ["无货", "下架", "售罄", "暂无", "缺货"]):
                stock_status = "out_of_stock"
        
        # Final price parsing
        price = float(sku.price)
        if price_str:
            try:
                import re
                clean_price = price_str.replace("￥", "").replace("¥", "").replace(",", "")
                match = re.search(r"(\d+\.?\d*)", clean_price)
                if match:
                    price = float(match.group(1))
            except:
                pass

        return ScrapeResult(
            success=True,
            platform="JD",
            sku_id=sku.platform_sku_id,
            title=title or sku.title,
            price=price,
            original_price=original_price or getattr(sku, 'original_price', None),
            shop_name=shop_name,
            stock_status=stock_status,
            buy_url=url,
            raw_payload={
                "title_found": bool(title_tag),
                "price_found": bool(price_tag),
                "stock_found": bool(stock_tag)
            }
        )

    def scrape(self, sku: any) -> ScrapeResult:
        """
        Entry point for the sync-to-async bridge.
        Handles execution within existing or new event loops.
        """
        import asyncio
        from concurrent.futures import ThreadPoolExecutor

        async def run_scrape():
            return await self._async_scrape(sku)

        try:
            # Check if there is an active loop in this thread
            loop = asyncio.get_running_loop()
            # If so, we need to run it in a separate thread to wait for it synchronously
            with ThreadPoolExecutor() as executor:
                future = executor.submit(lambda: asyncio.run(run_scrape()))
                return future.result()
        except RuntimeError:
            # No running loop, we can safe use asyncio.run
            return asyncio.run(run_scrape())
