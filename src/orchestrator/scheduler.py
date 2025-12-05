"""
Scraper Scheduler
Manages scheduling and execution of scraping tasks.
"""

from datetime import datetime, timedelta
from typing import Optional
import logging

from src.config.councils import ALL_COUNCILS, get_council_by_code
from src.scrapers.base.registry import get_registry
from .celery_app import celery_app
from .tasks import scrape_council, backfill_council, learn_field_mapping


logger = logging.getLogger(__name__)


class ScraperScheduler:
    """
    Central scheduler for managing scraping operations.
    """

    def __init__(self):
        self.registry = get_registry()

    def schedule_council(
        self,
        council_code: str,
        mode: str = "active",
        delay_seconds: int = 0,
    ) -> str:
        """
        Schedule a scraping task for a council.

        Args:
            council_code: Council identifier
            mode: 'active' or 'historical'
            delay_seconds: Delay before execution

        Returns:
            Task ID
        """
        if delay_seconds > 0:
            task = scrape_council.apply_async(
                args=[council_code, mode],
                countdown=delay_seconds,
            )
        else:
            task = scrape_council.delay(council_code, mode)

        logger.info(f"Scheduled scrape for {council_code} (mode={mode}): {task.id}")
        return task.id

    def schedule_tier(self, tier: int, mode: str = "active") -> list[str]:
        """
        Schedule scraping for all councils in a tier.

        Args:
            tier: Council tier (1-4)
            mode: Scraping mode

        Returns:
            List of task IDs
        """
        councils = [c for c in ALL_COUNCILS if c.tier == tier]
        task_ids = []

        for i, council in enumerate(councils):
            # Stagger tasks to avoid overwhelming the system
            delay = i * 30  # 30 seconds apart
            task_id = self.schedule_council(council.code, mode, delay_seconds=delay)
            task_ids.append(task_id)

        logger.info(f"Scheduled {len(task_ids)} councils for tier {tier}")
        return task_ids

    def schedule_state(self, state: str, mode: str = "active") -> list[str]:
        """
        Schedule scraping for all councils in a state.

        Args:
            state: State code (NSW, VIC, etc.)
            mode: Scraping mode

        Returns:
            List of task IDs
        """
        councils = [c for c in ALL_COUNCILS if c.state.value == state]
        task_ids = []

        for i, council in enumerate(councils):
            delay = i * 30
            task_id = self.schedule_council(council.code, mode, delay_seconds=delay)
            task_ids.append(task_id)

        logger.info(f"Scheduled {len(task_ids)} councils for state {state}")
        return task_ids

    def schedule_backfill(
        self,
        council_code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> str:
        """
        Schedule a historical backfill for a council.

        Args:
            council_code: Council identifier
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            Task ID
        """
        task = backfill_council.delay(council_code, start_date, end_date)
        logger.info(f"Scheduled backfill for {council_code}: {task.id}")
        return task.id

    def schedule_field_learning(self, council_code: str) -> str:
        """
        Schedule field mapping learning for a council.

        Args:
            council_code: Council identifier

        Returns:
            Task ID
        """
        task = learn_field_mapping.delay(council_code)
        logger.info(f"Scheduled field learning for {council_code}: {task.id}")
        return task.id

    def get_task_status(self, task_id: str) -> dict:
        """
        Get status of a task.

        Args:
            task_id: Celery task ID

        Returns:
            Task status dict
        """
        result = celery_app.AsyncResult(task_id)

        return {
            "task_id": task_id,
            "status": result.status,
            "ready": result.ready(),
            "successful": result.successful() if result.ready() else None,
            "result": result.result if result.ready() else None,
        }

    def get_active_tasks(self) -> list[dict]:
        """Get list of currently active tasks."""
        inspect = celery_app.control.inspect()
        active = inspect.active() or {}

        tasks = []
        for worker, worker_tasks in active.items():
            for task in worker_tasks:
                tasks.append({
                    "worker": worker,
                    "task_id": task["id"],
                    "name": task["name"],
                    "args": task.get("args", []),
                })

        return tasks

    def get_scheduled_tasks(self) -> list[dict]:
        """Get list of scheduled (pending) tasks."""
        inspect = celery_app.control.inspect()
        scheduled = inspect.scheduled() or {}

        tasks = []
        for worker, worker_tasks in scheduled.items():
            for task in worker_tasks:
                tasks.append({
                    "worker": worker,
                    "task_id": task["request"]["id"],
                    "name": task["request"]["name"],
                    "eta": task.get("eta"),
                })

        return tasks

    def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a pending task.

        Args:
            task_id: Task ID to cancel

        Returns:
            True if cancelled successfully
        """
        celery_app.control.revoke(task_id, terminate=True)
        logger.info(f"Cancelled task: {task_id}")
        return True

    def get_stats(self) -> dict:
        """Get scheduler statistics."""
        inspect = celery_app.control.inspect()

        active = inspect.active() or {}
        scheduled = inspect.scheduled() or {}
        reserved = inspect.reserved() or {}

        total_active = sum(len(tasks) for tasks in active.values())
        total_scheduled = sum(len(tasks) for tasks in scheduled.values())
        total_reserved = sum(len(tasks) for tasks in reserved.values())

        return {
            "active_tasks": total_active,
            "scheduled_tasks": total_scheduled,
            "reserved_tasks": total_reserved,
            "workers": list(active.keys()),
            "councils_with_adapters": len(self.registry.get_councils_with_adapters()),
            "total_councils": len(ALL_COUNCILS),
        }
