from app.utils.crawler import fetch_page_content


class ProductCrawler:
    def fetch(self, url: str, selector: str | None = None, dynamic: bool = False) -> dict[str, str]:
        content = fetch_page_content(url, selector=selector, use_playwright=dynamic)
        return {
            "url": url,
            "mode": "playwright" if dynamic else "httpx",
            "content_preview": content[:500],
        }
