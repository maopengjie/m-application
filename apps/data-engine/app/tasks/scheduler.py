from contextlib import suppress

from apscheduler.schedulers.background import BackgroundScheduler

from app.tasks.jobs.alert_jobs import register_alert_jobs
from app.tasks.jobs.crawler_jobs import register_crawler_jobs
from app.tasks.jobs.price_jobs import register_price_jobs

scheduler = BackgroundScheduler()


def start_scheduler() -> None:
    if scheduler.running:
        return
    register_crawler_jobs(scheduler)
    register_price_jobs(scheduler)
    register_alert_jobs(scheduler)
    scheduler.start()


def stop_scheduler() -> None:
    with suppress(Exception):
        if scheduler.running:
            scheduler.shutdown(wait=False)
