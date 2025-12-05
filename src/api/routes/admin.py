"""Admin endpoints for scraper management."""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from src.orchestrator.scheduler import ScraperScheduler
from src.scrapers.base.registry import get_registry


router = APIRouter()
scheduler = ScraperScheduler()


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
