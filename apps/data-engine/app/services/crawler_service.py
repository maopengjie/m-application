import time


class CrawlerService:
    def start_crawler(self, target_url: str) -> dict[str, str]:
        return {"job_id": f"job_{int(time.time())}", "target_url": target_url}
