"""Raw data storage for scraped records."""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional
from uuid import uuid4

from src.config import settings


class RawDataStore:
    """
    Stores raw scraped data before processing.
    Used for debugging, reprocessing, and audit trails.
    """

    def __init__(self, base_path: Optional[str] = None):
        self.base_path = Path(base_path or settings.raw_data_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _get_batch_path(self, council_code: str, date: datetime) -> Path:
        """Get the directory path for a batch."""
        date_str = date.strftime("%Y/%m/%d")
        path = self.base_path / council_code / date_str
        path.mkdir(parents=True, exist_ok=True)
        return path

    async def store_batch(
        self,
        council_code: str,
        records: list[dict],
        metadata: Optional[dict] = None,
    ) -> str:
        """
        Store a batch of raw records.

        Args:
            council_code: Council identifier
            records: List of raw scraped records
            metadata: Optional metadata about the scrape

        Returns:
            Batch ID
        """
        now = datetime.utcnow()
        batch_id = f"{council_code}_{now.strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:8]}"

        batch_path = self._get_batch_path(council_code, now)
        file_path = batch_path / f"{batch_id}.json"

        batch_data = {
            "batch_id": batch_id,
            "council_code": council_code,
            "scraped_at": now.isoformat(),
            "record_count": len(records),
            "metadata": metadata or {},
            "records": records,
        }

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(batch_data, f, indent=2, default=str)

        return batch_id

    async def get_batch(self, batch_id: str) -> Optional[dict]:
        """
        Retrieve a batch by ID.

        Args:
            batch_id: Batch identifier

        Returns:
            Batch data or None if not found
        """
        # Parse batch_id to find the file
        parts = batch_id.split("_")
        if len(parts) < 3:
            return None

        council_code = parts[0]
        date_str = parts[1]

        try:
            date = datetime.strptime(date_str, "%Y%m%d")
            batch_path = self._get_batch_path(council_code, date)
            file_path = batch_path / f"{batch_id}.json"

            if file_path.exists():
                with open(file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except (ValueError, FileNotFoundError):
            pass

        return None

    async def list_batches(
        self,
        council_code: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
    ) -> list[dict]:
        """
        List batches with optional filters.

        Args:
            council_code: Filter by council
            start_date: Filter by start date
            end_date: Filter by end date
            limit: Maximum number of results

        Returns:
            List of batch metadata
        """
        batches = []

        # Determine directories to search
        if council_code:
            search_dirs = [self.base_path / council_code]
        else:
            search_dirs = [
                d for d in self.base_path.iterdir() if d.is_dir()
            ]

        for council_dir in search_dirs:
            if not council_dir.exists():
                continue

            for year_dir in sorted(council_dir.iterdir(), reverse=True):
                if not year_dir.is_dir():
                    continue

                for month_dir in sorted(year_dir.iterdir(), reverse=True):
                    if not month_dir.is_dir():
                        continue

                    for day_dir in sorted(month_dir.iterdir(), reverse=True):
                        if not day_dir.is_dir():
                            continue

                        for batch_file in sorted(day_dir.glob("*.json"), reverse=True):
                            if len(batches) >= limit:
                                return batches

                            try:
                                with open(batch_file, "r", encoding="utf-8") as f:
                                    data = json.load(f)

                                batch_date = datetime.fromisoformat(data["scraped_at"])

                                if start_date and batch_date < start_date:
                                    continue
                                if end_date and batch_date > end_date:
                                    continue

                                batches.append({
                                    "batch_id": data["batch_id"],
                                    "council_code": data["council_code"],
                                    "scraped_at": data["scraped_at"],
                                    "record_count": data["record_count"],
                                })
                            except (json.JSONDecodeError, KeyError):
                                continue

        return batches

    async def get_latest_batch(self, council_code: str) -> Optional[dict]:
        """
        Get the most recent batch for a council.

        Args:
            council_code: Council identifier

        Returns:
            Latest batch data or None
        """
        batches = await self.list_batches(council_code=council_code, limit=1)
        if batches:
            return await self.get_batch(batches[0]["batch_id"])
        return None

    def get_storage_stats(self) -> dict:
        """Get storage statistics."""
        total_files = 0
        total_size = 0
        councils = set()

        for path in self.base_path.rglob("*.json"):
            total_files += 1
            total_size += path.stat().st_size
            # Extract council code from path
            relative = path.relative_to(self.base_path)
            if len(relative.parts) > 0:
                councils.add(relative.parts[0])

        return {
            "total_batches": total_files,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "councils_with_data": len(councils),
            "base_path": str(self.base_path),
        }
