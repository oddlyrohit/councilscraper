"""Batch geocoding service for processing multiple addresses efficiently."""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from uuid import UUID

from src.services.geocoding.geocoder import Geocoder, GeocodingResult
from src.storage.database import DatabaseManager


logger = logging.getLogger(__name__)


@dataclass
class BatchGeocodingStats:
    """Statistics for a batch geocoding job."""

    total: int = 0
    successful: int = 0
    failed: int = 0
    cached: int = 0
    skipped: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total == 0:
            return 0.0
        return (self.successful + self.cached) / self.total

    @property
    def duration_seconds(self) -> float:
        """Calculate duration in seconds."""
        if not self.start_time or not self.end_time:
            return 0.0
        return (self.end_time - self.start_time).total_seconds()


@dataclass
class GeocodingJob:
    """A single geocoding job item."""

    application_id: UUID
    address: str
    suburb: Optional[str] = None
    postcode: Optional[str] = None
    state: Optional[str] = None
    result: Optional[GeocodingResult] = None
    error: Optional[str] = None


class BatchGeocoder:
    """
    Batch geocoding service for processing multiple applications.

    Features:
    - Concurrent processing with rate limiting
    - Progress tracking and reporting
    - Database integration for updating applications
    - Retry logic for failed geocodes
    """

    def __init__(
        self,
        geocoder: Optional[Geocoder] = None,
        concurrency: int = 5,
        db: Optional[DatabaseManager] = None,
    ):
        self.geocoder = geocoder or Geocoder()
        self.concurrency = concurrency
        self.db = db or DatabaseManager()
        self._semaphore = asyncio.Semaphore(concurrency)

    async def _geocode_single(self, job: GeocodingJob) -> GeocodingJob:
        """Geocode a single job with rate limiting."""
        async with self._semaphore:
            try:
                result = await self.geocoder.geocode(
                    address=job.address,
                    suburb=job.suburb,
                    postcode=job.postcode,
                    state=job.state,
                )
                job.result = result
            except Exception as e:
                job.error = str(e)
                logger.error(f"Geocoding failed for {job.application_id}: {e}")

            return job

    async def geocode_applications(
        self,
        council_code: Optional[str] = None,
        limit: int = 1000,
        force_regeocode: bool = False,
    ) -> BatchGeocodingStats:
        """
        Geocode applications that are missing coordinates.

        Args:
            council_code: Filter by council code
            limit: Maximum number of applications to process
            force_regeocode: Re-geocode even if coordinates exist

        Returns:
            BatchGeocodingStats with results
        """
        stats = BatchGeocodingStats(start_time=datetime.utcnow())

        # Get applications needing geocoding
        applications = await self.db.get_applications_needing_geocoding(
            council_code=council_code,
            limit=limit,
            include_with_coords=force_regeocode,
        )

        stats.total = len(applications)
        logger.info(f"Starting batch geocoding for {stats.total} applications")

        if not applications:
            stats.end_time = datetime.utcnow()
            return stats

        # Create jobs
        jobs = [
            GeocodingJob(
                application_id=app.id,
                address=app.address,
                suburb=app.suburb,
                postcode=app.postcode,
                state=app.state,
            )
            for app in applications
        ]

        # Process in batches to avoid overwhelming the geocoder
        batch_size = 50
        for i in range(0, len(jobs), batch_size):
            batch = jobs[i:i + batch_size]
            tasks = [self._geocode_single(job) for job in batch]
            completed = await asyncio.gather(*tasks)

            # Update database with results
            for job in completed:
                if job.result:
                    await self._update_application_coords(job)
                    stats.successful += 1
                elif job.error:
                    stats.failed += 1
                else:
                    stats.skipped += 1

            logger.info(
                f"Batch progress: {i + len(batch)}/{stats.total} "
                f"({stats.successful} successful, {stats.failed} failed)"
            )

        stats.end_time = datetime.utcnow()
        logger.info(
            f"Batch geocoding complete: {stats.successful}/{stats.total} successful "
            f"({stats.success_rate:.1%}) in {stats.duration_seconds:.1f}s"
        )

        return stats

    async def _update_application_coords(self, job: GeocodingJob) -> None:
        """Update application with geocoding result."""
        if not job.result:
            return

        await self.db.update_application_coordinates(
            application_id=job.application_id,
            latitude=job.result.latitude,
            longitude=job.result.longitude,
            geocoding_confidence=job.result.confidence,
            geocoding_provider=job.result.provider,
        )

    async def geocode_council_backlog(
        self,
        council_code: str,
        batch_size: int = 100,
    ) -> BatchGeocodingStats:
        """
        Process the entire geocoding backlog for a council.

        Processes in batches until all applications are geocoded.
        """
        total_stats = BatchGeocodingStats(start_time=datetime.utcnow())

        while True:
            batch_stats = await self.geocode_applications(
                council_code=council_code,
                limit=batch_size,
            )

            total_stats.total += batch_stats.total
            total_stats.successful += batch_stats.successful
            total_stats.failed += batch_stats.failed
            total_stats.cached += batch_stats.cached
            total_stats.skipped += batch_stats.skipped

            # Stop when no more applications to process
            if batch_stats.total < batch_size:
                break

            # Brief pause between batches
            await asyncio.sleep(1.0)

        total_stats.end_time = datetime.utcnow()
        return total_stats

    async def verify_existing_geocodes(
        self,
        council_code: Optional[str] = None,
        sample_size: int = 100,
    ) -> dict:
        """
        Verify accuracy of existing geocodes by re-geocoding a sample.

        Returns statistics on geocode quality and drift.
        """
        # Get sample of applications with coordinates
        applications = await self.db.get_applications_with_coordinates(
            council_code=council_code,
            limit=sample_size,
        )

        results = {
            "total_checked": len(applications),
            "matches": 0,
            "significant_drift": 0,
            "failures": 0,
            "average_drift_meters": 0.0,
        }

        drifts = []

        for app in applications:
            try:
                new_result = await self.geocoder.geocode(
                    address=app.address,
                    suburb=app.suburb,
                    postcode=app.postcode,
                    state=app.state,
                )

                if new_result:
                    # Calculate distance between old and new coordinates
                    drift = self._haversine_distance(
                        app.latitude, app.longitude,
                        new_result.latitude, new_result.longitude
                    )
                    drifts.append(drift)

                    if drift < 100:  # Less than 100 meters
                        results["matches"] += 1
                    else:
                        results["significant_drift"] += 1
                else:
                    results["failures"] += 1

            except Exception as e:
                results["failures"] += 1
                logger.error(f"Verification failed for {app.id}: {e}")

        if drifts:
            results["average_drift_meters"] = sum(drifts) / len(drifts)

        return results

    @staticmethod
    def _haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two coordinates in meters."""
        import math

        R = 6371000  # Earth's radius in meters

        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)

        a = (
            math.sin(delta_phi / 2) ** 2 +
            math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c
