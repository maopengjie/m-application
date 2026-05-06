from __future__ import annotations

import os

from celery import Celery


REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_client = Celery(
    "m_application_backend",
    broker=REDIS_URL,
    backend=REDIS_URL,
)


def enqueue_task(task_name: str, *args, **kwargs) -> str:
    task = celery_client.send_task(task_name, args=args, kwargs=kwargs)
    return task.id
