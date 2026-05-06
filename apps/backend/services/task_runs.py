from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from models import ScrapeTaskRun


STALE_RUNNING_MINUTES = 30
STALE_PENDING_MINUTES = 10


def mark_stale_scrape_runs(db: Session, now: datetime | None = None) -> int:
    """Close task runs that can no longer be updated by a healthy worker."""
    current_time = now or datetime.now()
    running_cutoff = current_time - timedelta(minutes=STALE_RUNNING_MINUTES)
    pending_cutoff = current_time - timedelta(minutes=STALE_PENDING_MINUTES)

    runs = (
        db.query(ScrapeTaskRun)
        .filter(ScrapeTaskRun.status.in_(["PENDING", "RUNNING"]))
        .filter(
            (
                (ScrapeTaskRun.status == "RUNNING")
                & (ScrapeTaskRun.started_at.isnot(None))
                & (ScrapeTaskRun.started_at < running_cutoff)
            )
            | (
                (ScrapeTaskRun.status == "PENDING")
                & (ScrapeTaskRun.created_at < pending_cutoff)
            )
        )
        .all()
    )

    for run in runs:
        previous_status = run.status
        run.status = "TIMEOUT"
        run.finished_at = current_time
        run.failure_count = max(run.failure_count or 0, 1)
        run.summary_message = f"任务超时，已从 {previous_status} 自动关闭"
        run.error_message = (
            f"Worker did not report completion within "
            f"{STALE_RUNNING_MINUTES if previous_status == 'RUNNING' else STALE_PENDING_MINUTES} minutes."
        )

    if runs:
        db.flush()
    return len(runs)
