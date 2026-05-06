import os
from datetime import timedelta

from celery import Celery
from dotenv import load_dotenv

load_dotenv()

redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

app = Celery(
    "m_application_worker",
    broker=redis_url,
    backend=redis_url,
    include=["tasks.scraping"]
)

app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

maintenance_interval_minutes = int(os.getenv("MAINTENANCE_INTERVAL_MINUTES", "5"))
beat_schedule = {
    "close-stale-scrape-runs": {
        "task": "tasks.scraping.close_stale_scrape_runs",
        "schedule": timedelta(minutes=maintenance_interval_minutes),
    }
}

if os.getenv("ENABLE_PERIODIC_SCRAPE", "").lower() in {"1", "true", "yes"}:
    interval_minutes = int(os.getenv("PERIODIC_SCRAPE_INTERVAL_MINUTES", "30"))
    periodic_limit = int(os.getenv("PERIODIC_SCRAPE_LIMIT", "20"))
    periodic_platform = os.getenv("PERIODIC_SCRAPE_PLATFORM") or None
    beat_schedule["scrape-active-products-periodically"] = {
        "task": "tasks.scraping.scrape_active_products",
        "schedule": timedelta(minutes=interval_minutes),
        "args": (periodic_limit, periodic_platform),
    }

if os.getenv("ENABLE_PERIODIC_CATEGORY_SYNC", "").lower() in {"1", "true", "yes"}:
    category_sync_hours = int(os.getenv("PERIODIC_CATEGORY_SYNC_HOURS", "24"))
    beat_schedule["sync-jd-category-tree-periodically"] = {
        "task": "tasks.scraping.sync_jd_category_tree",
        "schedule": timedelta(hours=category_sync_hours),
    }

app.conf.beat_schedule = beat_schedule

if __name__ == "__main__":
    app.start()
