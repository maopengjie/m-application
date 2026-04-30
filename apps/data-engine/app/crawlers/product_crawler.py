from typing import Any
from app.utils.ai_crawler import crawl_url_sync


class ProductCrawler:
    def fetch(self, url: str, selector: str | None = None, dynamic: bool = True) -> dict[str, Any]:
        """
        Fetches page content using the AI-powered crawler.
        """
        # Crawl4AI handles dynamic content by default with much better precision
        result = crawl_url_sync(url, css_selector=selector)
        
        if not result.get("success"):
            return {
                "url": url,
                "error": result.get("error", "Unknown crawl error"),
                "success": False
            }

        return {
            "success": True,
            "url": url,
            "mode": "crawl4ai",
            "markdown_preview": result["markdown"][:1000] if result.get("markdown") else "",
            "metadata": result.get("metadata", {}),
            "links_count": len(result.get("links", [])),
            "media_count": len(result.get("media", []))
        }
