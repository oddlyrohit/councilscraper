"""Scraper status monitoring and reporting."""

import logging
from datetime import datetime, timedelta
from typing import Optional
from dataclasses import dataclass

from sqlalchemy import select, func, and_, desc, Integer, case
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


@dataclass
class CouncilStatus:
    """Status of a council's scraper."""
    council_code: str
    council_name: str
    tier: int
    last_run: Optional[datetime]
    last_status: Optional[str]
    last_error: Optional[str]
    records_last_run: int
    total_runs_24h: int
    success_runs_24h: int
    failed_runs_24h: int
    health: str  # healthy, warning, critical


class ScraperStatus:
    """Monitor and report on scraper status."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self._models = None

    def _get_models(self):
        """Lazy import models."""
        if self._models is None:
            from src.models import Council, ScrapeLog, Application
            self._models = {
                'Council': Council,
                'ScrapeLog': ScrapeLog,
                'Application': Application,
            }
        return self._models

    async def get_overall_stats(self, hours: int = 24) -> dict:
        """Get overall scraper statistics."""
        models = self._get_models()
        ScrapeLog = models['ScrapeLog']
        Application = models['Application']

        cutoff = datetime.utcnow() - timedelta(hours=hours)

        # Get run statistics
        run_stats = await self.session.execute(
            select(
                func.count(ScrapeLog.id).label('total'),
                func.sum(case((ScrapeLog.status == 'success', 1), else_=0)).label('success'),
                func.sum(case((ScrapeLog.status == 'failed', 1), else_=0)).label('failed'),
                func.sum(func.coalesce(ScrapeLog.records_new, 0)).label('new'),
                func.sum(func.coalesce(ScrapeLog.records_updated, 0)).label('updated'),
            ).where(ScrapeLog.started_at >= cutoff)
        )
        stats = run_stats.first()

        # Get total applications
        total_apps = await self.session.execute(
            select(func.count(Application.id))
        )

        return {
            'period_hours': hours,
            'total_runs': stats.total or 0,
            'successful_runs': stats.success or 0,
            'failed_runs': stats.failed or 0,
            'total_new': stats.new or 0,
            'total_updated': stats.updated or 0,
            'total_applications': total_apps.scalar() or 0,
            'success_rate': round((stats.success or 0) / max(stats.total or 1, 1) * 100, 1),
        }

    async def get_council_status(self, council_code: str) -> Optional[CouncilStatus]:
        """Get detailed status for a specific council."""
        models = self._get_models()
        Council = models['Council']
        ScrapeLog = models['ScrapeLog']

        cutoff = datetime.utcnow() - timedelta(hours=24)

        # Get council info
        council_result = await self.session.execute(
            select(Council).where(Council.code == council_code)
        )
        council = council_result.scalar_one_or_none()
        if not council:
            return None

        # Get last run
        last_run_result = await self.session.execute(
            select(ScrapeLog)
            .where(ScrapeLog.council_id == council.id)
            .order_by(desc(ScrapeLog.started_at))
            .limit(1)
        )
        last_run = last_run_result.scalar_one_or_none()

        # Get 24h stats
        stats_result = await self.session.execute(
            select(
                func.count(ScrapeLog.id).label('total'),
                func.sum(case((ScrapeLog.status == 'success', 1), else_=0)).label('success'),
                func.sum(case((ScrapeLog.status == 'failed', 1), else_=0)).label('failed'),
            ).where(
                and_(
                    ScrapeLog.council_id == council.id,
                    ScrapeLog.started_at >= cutoff
                )
            )
        )
        stats = stats_result.first()

        # Determine health
        failed_24h = stats.failed or 0
        if failed_24h >= 3:
            health = 'critical'
        elif failed_24h >= 1:
            health = 'warning'
        else:
            health = 'healthy'

        return CouncilStatus(
            council_code=council.code,
            council_name=council.name,
            tier=council.tier,
            last_run=last_run.started_at if last_run else None,
            last_status=last_run.status if last_run else None,
            last_error=str(last_run.errors) if last_run and last_run.errors else None,
            records_last_run=(last_run.records_new or 0) + (last_run.records_updated or 0) if last_run else 0,
            total_runs_24h=stats.total or 0,
            success_runs_24h=stats.success or 0,
            failed_runs_24h=failed_24h,
            health=health,
        )

    async def get_all_council_status(self) -> list[dict]:
        """Get status for all councils."""
        models = self._get_models()
        Council = models['Council']
        ScrapeLog = models['ScrapeLog']

        cutoff = datetime.utcnow() - timedelta(hours=24)

        # Get all councils with their latest run info using a subquery
        from sqlalchemy.orm import aliased
        from sqlalchemy import Integer

        # Subquery to get the latest run for each council
        latest_run_subq = (
            select(
                ScrapeLog.council_id,
                func.max(ScrapeLog.started_at).label('last_run')
            )
            .group_by(ScrapeLog.council_id)
            .subquery()
        )

        # Get 24h failure counts
        failure_counts = (
            select(
                ScrapeLog.council_id,
                func.count(ScrapeLog.id).label('failures')
            )
            .where(
                and_(
                    ScrapeLog.status == 'failed',
                    ScrapeLog.started_at >= cutoff
                )
            )
            .group_by(ScrapeLog.council_id)
            .subquery()
        )

        # Main query
        result = await self.session.execute(
            select(
                Council.code,
                Council.name,
                Council.tier,
                latest_run_subq.c.last_run,
                func.coalesce(failure_counts.c.failures, 0).label('failures_24h')
            )
            .outerjoin(latest_run_subq, Council.id == latest_run_subq.c.council_id)
            .outerjoin(failure_counts, Council.id == failure_counts.c.council_id)
            .order_by(Council.tier, Council.name)
        )

        councils = []
        for row in result.all():
            failures = row.failures_24h or 0
            if failures >= 3:
                health = 'critical'
            elif failures >= 1:
                health = 'warning'
            else:
                health = 'healthy'

            councils.append({
                'code': row.code,
                'name': row.name,
                'tier': row.tier,
                'last_run': row.last_run.isoformat() if row.last_run else None,
                'failures_24h': failures,
                'health': health,
            })

        return councils

    async def get_failed_councils(self, hours: int = 24, min_failures: int = 3) -> list[str]:
        """Get councils with repeated failures."""
        models = self._get_models()
        Council = models['Council']
        ScrapeLog = models['ScrapeLog']

        cutoff = datetime.utcnow() - timedelta(hours=hours)

        result = await self.session.execute(
            select(Council.code)
            .join(ScrapeLog)
            .where(
                and_(
                    ScrapeLog.status == 'failed',
                    ScrapeLog.started_at >= cutoff
                )
            )
            .group_by(Council.code)
            .having(func.count(ScrapeLog.id) >= min_failures)
        )

        return [row[0] for row in result.all()]

    async def get_tier_summary(self) -> list[dict]:
        """Get summary by tier."""
        models = self._get_models()
        Council = models['Council']
        ScrapeLog = models['ScrapeLog']

        cutoff = datetime.utcnow() - timedelta(hours=24)

        result = await self.session.execute(
            select(
                Council.tier,
                func.count(func.distinct(Council.id)).label('total_councils'),
                func.count(ScrapeLog.id).label('runs_24h'),
                func.sum(case((ScrapeLog.status == 'success', 1), else_=0)).label('success'),
                func.sum(case((ScrapeLog.status == 'failed', 1), else_=0)).label('failed'),
                func.sum(func.coalesce(ScrapeLog.records_new, 0)).label('new_records'),
            )
            .outerjoin(ScrapeLog, and_(
                Council.id == ScrapeLog.council_id,
                ScrapeLog.started_at >= cutoff
            ))
            .group_by(Council.tier)
            .order_by(Council.tier)
        )

        return [
            {
                'tier': row.tier,
                'total_councils': row.total_councils,
                'runs_24h': row.runs_24h or 0,
                'success': row.success or 0,
                'failed': row.failed or 0,
                'new_records': row.new_records or 0,
            }
            for row in result.all()
        ]

    async def get_recent_errors(self, limit: int = 20) -> list[dict]:
        """Get most recent errors."""
        models = self._get_models()
        Council = models['Council']
        ScrapeLog = models['ScrapeLog']

        result = await self.session.execute(
            select(
                Council.code,
                Council.name,
                ScrapeLog.started_at,
                ScrapeLog.errors,
                ScrapeLog.duration_seconds,
            )
            .join(Council)
            .where(ScrapeLog.status == 'failed')
            .order_by(desc(ScrapeLog.started_at))
            .limit(limit)
        )

        return [
            {
                'council_code': row.code,
                'council_name': row.name,
                'time': row.started_at.isoformat() if row.started_at else None,
                'error': row.errors,
                'duration': row.duration_seconds,
            }
            for row in result.all()
        ]
