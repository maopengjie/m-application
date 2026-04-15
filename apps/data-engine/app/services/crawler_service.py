import time

from app.crawlers.product_crawler import ProductCrawler


class CrawlerService:
    def __init__(self, crawler: ProductCrawler | None = None):
        self.crawler = crawler or ProductCrawler()

    def start_crawler(self, target_url: str) -> dict[str, str]:
        return {"job_id": f"job_{int(time.time())}", "target_url": target_url}

    def fetch_page(self, target_url: str, dynamic: bool = False, selector: str | None = None) -> dict[str, str]:
        return self.crawler.fetch(target_url, selector=selector, dynamic=dynamic)
