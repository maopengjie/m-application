def register_price_jobs(scheduler) -> None:
    scheduler.add_job(
        lambda: None,
        "interval",
        minutes=15,
        id="price-refresh",
        replace_existing=True,
    )
