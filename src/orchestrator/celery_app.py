"""
Celery Application Configuration
Central configuration for the distributed task queue.
"""

from celery import Celery
from celery.schedules import crontab

from src.config import settings


# Create Celery app
celery_app = Celery(
    "council_scraper",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "src.orchestrator.tasks",
    ],
)

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Australia/Sydney",
    enable_utc=True,

    # Task execution
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_time_limit=600,  # 10 minutes max per task
    task_soft_time_limit=540,  # 9 minutes soft limit

    # Worker settings
    worker_prefetch_multiplier=1,
    worker_concurrency=4,

    # Result backend
    result_expires=86400,  # Results expire after 24 hours

    # Beat scheduler
    beat_scheduler="celery.beat:PersistentScheduler",
    beat_schedule_filename="data/cache/celerybeat-schedule",
)


def get_beat_schedule() -> dict:
    """
    Generate the Celery Beat schedule based on council tiers.

    Returns:
        Dictionary of scheduled tasks
    """
    from src.config.councils import (
        TIER_1_COUNCILS,
        TIER_2_COUNCILS,
        TIER_3_COUNCILS,
        TIER_4_COUNCILS,
    )

    schedule = {}

    # Tier 1: Every 6 hours (major metro councils)
    for council in TIER_1_COUNCILS:
        schedule[f"scrape-{council.code}-tier1"] = {
            "task": "src.orchestrator.tasks.scrape_council",
            "schedule": crontab(minute=0, hour="*/6"),
            "args": [council.code, "active"],
            "options": {"queue": "tier1"},
        }

    # Tier 2: Every 12 hours
    for i, council in enumerate(TIER_2_COUNCILS):
        # Stagger by 15 minutes to avoid thundering herd
        minute = (i * 15) % 60
        schedule[f"scrape-{council.code}-tier2"] = {
            "task": "src.orchestrator.tasks.scrape_council",
            "schedule": crontab(minute=minute, hour="*/12"),
            "args": [council.code, "active"],
            "options": {"queue": "tier2"},
        }

    # Tier 3-4: Daily
    all_tier34 = TIER_3_COUNCILS + TIER_4_COUNCILS
    for i, council in enumerate(all_tier34):
        hour = i % 24
        minute = (i * 3) % 60
        schedule[f"scrape-{council.code}-daily"] = {
            "task": "src.orchestrator.tasks.scrape_council",
            "schedule": crontab(minute=minute, hour=hour),
            "args": [council.code, "active"],
            "options": {"queue": "default"},
        }

    # Quality check - daily at 2 AM
    schedule["daily-quality-check"] = {
        "task": "src.orchestrator.tasks.run_quality_checks",
        "schedule": crontab(minute=0, hour=2),
    }

    # Data cleanup - weekly on Sunday at 3 AM
    schedule["weekly-cleanup"] = {
        "task": "src.orchestrator.tasks.cleanup_old_data",
        "schedule": crontab(minute=0, hour=3, day_of_week=0),
    }

    return schedule


# Apply beat schedule
celery_app.conf.beat_schedule = get_beat_schedule()
