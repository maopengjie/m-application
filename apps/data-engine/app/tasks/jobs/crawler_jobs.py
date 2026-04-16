import logging

logger = logging.getLogger(__name__)


def crawler_heartbeat_job():
    """Simple heartbeat job to ensure the scheduler is alive and running tasks."""
    logger.info("Scheduler Heartbeat: Active")


def register_crawler_jobs(scheduler) -> None:
    scheduler.add_job(
        crawler_heartbeat_job,
        "interval",
        minutes=30,
        id="crawler-heartbeat",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
        misfire_grace_time=60,
    )
