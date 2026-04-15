def register_alert_jobs(scheduler) -> None:
    scheduler.add_job(
        lambda: None,
        "interval",
        minutes=10,
        id="alert-dispatch",
        replace_existing=True,
    )
