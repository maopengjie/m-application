def register_crawler_jobs(scheduler) -> None:
    scheduler.add_job(
        lambda: None,
        "interval",
        minutes=30,
        id="crawler-heartbeat",
        replace_existing=True,
    )
