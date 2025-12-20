"""
Celery application configuration.
"""
from celery import Celery
from celery.schedules import crontab

from ..core.config import settings

# Create Celery app
celery_app = Celery(
    "stock_screener",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["src.tasks.ingestion_tasks", "src.tasks.scoring_tasks"]
)

# Configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",  # Indian time zone
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
)

# Scheduled tasks (Celery Beat)
celery_app.conf.beat_schedule = {
    "ingest-fundamental-data": {
        "task": "src.tasks.ingestion_tasks.ingest_fundamental_data",
        "schedule": crontab(
            hour=17,  # 5 PM IST
            minute=0,
            day_of_week="1-5"  # Monday to Friday
        ),
    },
    "ingest-news-data": {
        "task": "src.tasks.ingestion_tasks.ingest_news_data",
        "schedule": crontab(
            minute=0,
            hour="*/2"  # Every 2 hours
        ),
    },
    "analyze-sentiment": {
        "task": "src.tasks.ingestion_tasks.analyze_pending_sentiment",
        "schedule": crontab(
            minute=30,
            hour="*/2"  # Every 2 hours, offset by 30 mins from news ingestion
        ),
    },
    "compute-scores": {
        "task": "src.tasks.scoring_tasks.compute_all_scores",
        "schedule": crontab(
            hour=18,  # 6 PM IST
            minute=0,
            day_of_week="1-5"  # Monday to Friday
        ),
    },
}
