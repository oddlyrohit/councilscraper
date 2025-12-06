"""Admin endpoints for scraper management and monitoring."""

from typing import Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.orchestrator.scheduler import ScraperScheduler
from src.scrapers.base.registry import get_registry
from src.storage.database import get_db_session
from src.monitoring.status import ScraperStatus
from src.monitoring.alerts import AlertManager


router = APIRouter()
scheduler = ScraperScheduler()
alert_manager = AlertManager()


class ScrapeRequest(BaseModel):
    """Request to trigger a scrape."""
    council_code: str
    mode: str = "active"


class BackfillRequest(BaseModel):
    """Request to trigger a historical backfill."""
    council_code: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None


@router.post("/scrape")
async def trigger_scrape(request: ScrapeRequest):
    """
    Trigger a scrape for a specific council.

    Admin only endpoint.
    """
    task_id = scheduler.schedule_council(request.council_code, request.mode)

    return {
        "message": f"Scrape scheduled for {request.council_code}",
        "task_id": task_id,
        "mode": request.mode,
    }


@router.post("/scrape/tier/{tier}")
async def trigger_tier_scrape(tier: int, mode: str = "active"):
    """
    Trigger scrapes for all councils in a tier.
    """
    if tier < 1 or tier > 4:
        raise HTTPException(status_code=400, detail="Tier must be 1-4")

    task_ids = scheduler.schedule_tier(tier, mode)

    return {
        "message": f"Scheduled {len(task_ids)} councils for tier {tier}",
        "task_ids": task_ids,
    }


@router.post("/scrape/state/{state}")
async def trigger_state_scrape(state: str, mode: str = "active"):
    """
    Trigger scrapes for all councils in a state.
    """
    task_ids = scheduler.schedule_state(state.upper(), mode)

    return {
        "message": f"Scheduled {len(task_ids)} councils for state {state}",
        "task_ids": task_ids,
    }


@router.post("/backfill")
async def trigger_backfill(request: BackfillRequest):
    """
    Trigger historical backfill for a council.
    """
    task_id = scheduler.schedule_backfill(
        request.council_code,
        request.start_date,
        request.end_date,
    )

    return {
        "message": f"Backfill scheduled for {request.council_code}",
        "task_id": task_id,
    }


@router.post("/learn-mapping/{council_code}")
async def trigger_field_learning(council_code: str):
    """
    Trigger field mapping learning for a council.
    """
    task_id = scheduler.schedule_field_learning(council_code)

    return {
        "message": f"Field learning scheduled for {council_code}",
        "task_id": task_id,
    }


@router.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    """
    Get status of a task.
    """
    return scheduler.get_task_status(task_id)


@router.get("/tasks/active")
async def get_active_tasks():
    """
    Get list of currently running tasks.
    """
    return {"tasks": scheduler.get_active_tasks()}


@router.get("/tasks/scheduled")
async def get_scheduled_tasks():
    """
    Get list of scheduled tasks.
    """
    return {"tasks": scheduler.get_scheduled_tasks()}


@router.delete("/tasks/{task_id}")
async def cancel_task(task_id: str):
    """
    Cancel a pending task.
    """
    scheduler.cancel_task(task_id)
    return {"message": f"Task {task_id} cancelled"}


@router.get("/stats")
async def get_scheduler_stats():
    """
    Get scheduler statistics.
    """
    return scheduler.get_stats()


@router.get("/scrapers")
async def list_scrapers():
    """
    List all registered scrapers and their status.
    """
    registry = get_registry()

    return {
        "stats": registry.get_portal_stats(),
        "councils_with_adapters": [
            c.code for c in registry.get_councils_with_adapters()
        ],
        "councils_without_adapters": [
            c.code for c in registry.get_councils_without_adapters()
        ],
    }


# =============================================================================
# MONITORING ENDPOINTS
# =============================================================================

@router.get("/status")
async def get_scraper_status(
    session: AsyncSession = Depends(get_db_session)
):
    """
    Get overall scraper status dashboard.

    Returns statistics for the last 24 hours including:
    - Total runs, successes, failures
    - New and updated DAs
    - Success rate
    """
    try:
        status = ScraperStatus(session)
        stats = await status.get_overall_stats(hours=24)
        tier_summary = await status.get_tier_summary()
        failed_councils = await status.get_failed_councils(hours=24, min_failures=3)
        recent_errors = await status.get_recent_errors(limit=10)

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "overall": stats,
            "by_tier": tier_summary,
            "critical_councils": failed_councils,
            "recent_errors": recent_errors,
            "alerts_configured": alert_manager.is_configured(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")


@router.get("/status/councils")
async def get_all_councils_status(
    session: AsyncSession = Depends(get_db_session)
):
    """
    Get status for all councils.

    Returns list of all councils with their health status.
    """
    try:
        status = ScraperStatus(session)
        councils = await status.get_all_council_status()

        # Group by health
        summary = {
            'healthy': sum(1 for c in councils if c['health'] == 'healthy'),
            'warning': sum(1 for c in councils if c['health'] == 'warning'),
            'critical': sum(1 for c in councils if c['health'] == 'critical'),
        }

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "summary": summary,
            "councils": councils,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get council status: {str(e)}")


@router.get("/status/council/{council_code}")
async def get_council_status(
    council_code: str,
    session: AsyncSession = Depends(get_db_session)
):
    """
    Get detailed status for a specific council.
    """
    try:
        status = ScraperStatus(session)
        council_status = await status.get_council_status(council_code.upper())

        if not council_status:
            raise HTTPException(status_code=404, detail=f"Council {council_code} not found")

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "council": {
                "code": council_status.council_code,
                "name": council_status.council_name,
                "tier": council_status.tier,
                "health": council_status.health,
                "last_run": council_status.last_run.isoformat() if council_status.last_run else None,
                "last_status": council_status.last_status,
                "last_error": council_status.last_error,
                "records_last_run": council_status.records_last_run,
                "runs_24h": council_status.total_runs_24h,
                "success_24h": council_status.success_runs_24h,
                "failed_24h": council_status.failed_runs_24h,
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get council status: {str(e)}")


@router.get("/status/errors")
async def get_recent_errors(
    limit: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Get recent scraper errors.
    """
    try:
        status = ScraperStatus(session)
        errors = await status.get_recent_errors(limit=limit)

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "count": len(errors),
            "errors": errors,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get errors: {str(e)}")


@router.post("/alerts/test")
async def test_alert():
    """
    Send a test alert email to verify configuration.
    """
    if not alert_manager.is_configured():
        return {
            "success": False,
            "message": "Email alerts not configured. Set SMTP_USER and SMTP_PASSWORD environment variables.",
        }

    success = alert_manager.send_email(
        subject="[Council Scraper] Test Alert",
        body=f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2 style="color: #28a745;">Test Alert</h2>
            <p>This is a test alert from Council DA Scraper.</p>
            <p>If you received this, email alerts are working correctly!</p>
            <p>Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
        </body>
        </html>
        """
    )

    return {
        "success": success,
        "message": "Test email sent successfully" if success else "Failed to send test email",
    }


@router.post("/alerts/digest")
async def send_daily_digest(
    session: AsyncSession = Depends(get_db_session)
):
    """
    Manually trigger a daily digest email.
    """
    if not alert_manager.is_configured():
        return {
            "success": False,
            "message": "Email alerts not configured.",
        }

    try:
        status = ScraperStatus(session)
        stats = await status.get_overall_stats(hours=24)
        failed_councils = await status.get_failed_councils(hours=24, min_failures=3)

        success = alert_manager.send_daily_digest(stats, failed_councils)

        return {
            "success": success,
            "message": "Daily digest sent" if success else "Failed to send digest",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send digest: {str(e)}")
