"""
ThreatScan — Celery application configuration.
"""

from celery import Celery

from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "threatscan",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.worker.tasks"],
)

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,

    # Reliability
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,

    # Timeouts
    task_soft_time_limit=settings.celery_task_timeout,
    task_time_limit=settings.celery_task_timeout + 30,

    # Result expiry
    result_expires=3600,  # 1 hour

    # Task routes
    task_routes={
        "app.worker.tasks.run_analysis_pipeline": {"queue": "analysis"},
    },
)
