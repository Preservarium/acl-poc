"""
APScheduler configuration and setup for background jobs.

This module initializes the APScheduler and configures
background jobs for the ACL system.
"""

import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.tasks.permission_expiration import expire_permissions, notify_expiring_permissions

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler: AsyncIOScheduler = None


def create_scheduler() -> AsyncIOScheduler:
    """
    Create and configure the APScheduler instance.

    Returns:
        AsyncIOScheduler: Configured scheduler instance
    """
    global scheduler

    if scheduler is not None:
        logger.warning("Scheduler already exists, returning existing instance")
        return scheduler

    # Create scheduler with asyncio executor
    scheduler = AsyncIOScheduler(
        timezone="UTC",
        job_defaults={
            'coalesce': True,  # Combine multiple missed runs into one
            'max_instances': 1,  # Only one instance of each job at a time
            'misfire_grace_time': 300  # 5 minutes grace time for missed jobs
        }
    )

    logger.info("APScheduler created successfully")
    return scheduler


def add_jobs(scheduler: AsyncIOScheduler):
    """
    Add all scheduled jobs to the scheduler.

    Jobs can be configured via environment variables in a production system.
    For now, we use hardcoded schedules:
    - expire_permissions: Runs every hour
    - notify_expiring_permissions: Runs daily at 9 AM UTC

    Args:
        scheduler: The scheduler instance to add jobs to
    """
    try:
        # Job 1: Expire permissions - runs every hour
        scheduler.add_job(
            func=expire_permissions,
            trigger=IntervalTrigger(hours=1),
            id="expire_permissions",
            name="Expire old permissions",
            replace_existing=True,
        )
        logger.info("Added job: expire_permissions (runs every hour)")

        # Job 2: Notify about expiring permissions - runs daily at 9 AM UTC
        scheduler.add_job(
            func=notify_expiring_permissions,
            trigger=CronTrigger(hour=9, minute=0),
            id="notify_expiring_permissions",
            name="Notify about expiring permissions",
            replace_existing=True,
            kwargs={"days_ahead": 7}  # Notify 7 days in advance
        )
        logger.info("Added job: notify_expiring_permissions (runs daily at 9 AM UTC)")

        # Optional: Add a job for 30-day notifications
        scheduler.add_job(
            func=notify_expiring_permissions,
            trigger=CronTrigger(day=1, hour=9, minute=0),  # First day of month
            id="notify_expiring_permissions_monthly",
            name="Notify about permissions expiring in 30 days",
            replace_existing=True,
            kwargs={"days_ahead": 30}
        )
        logger.info("Added job: notify_expiring_permissions_monthly (runs monthly)")

    except Exception as e:
        logger.error(f"Error adding jobs to scheduler: {str(e)}")
        raise


def start_scheduler():
    """
    Start the scheduler.

    This should be called during application startup.
    """
    global scheduler

    if scheduler is None:
        scheduler = create_scheduler()
        add_jobs(scheduler)

    if not scheduler.running:
        scheduler.start()
        logger.info("APScheduler started successfully")
    else:
        logger.warning("Scheduler is already running")


def shutdown_scheduler():
    """
    Gracefully shutdown the scheduler.

    This should be called during application shutdown.
    """
    global scheduler

    if scheduler is not None and scheduler.running:
        scheduler.shutdown(wait=True)
        logger.info("APScheduler shutdown successfully")
    else:
        logger.warning("Scheduler is not running or does not exist")


def get_scheduler() -> AsyncIOScheduler:
    """
    Get the global scheduler instance.

    Returns:
        AsyncIOScheduler: The scheduler instance or None if not created
    """
    return scheduler


def list_jobs():
    """
    List all scheduled jobs.

    Returns:
        List of job information dictionaries
    """
    global scheduler

    if scheduler is None:
        return []

    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
            "trigger": str(job.trigger)
        })

    return jobs
