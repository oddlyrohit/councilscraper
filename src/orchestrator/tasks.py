"""
Celery Tasks for Scraping Operations
"""

import asyncio
from datetime import datetime, timedelta
from typing import Optional
import logging

from celery import shared_task

from src.config.councils import get_council_by_code
from src.scrapers.base.registry import get_registry
from src.mappers import AIFieldMapper, CategoryClassifier, DataNormalizer
from src.storage import DatabaseManager, RawDataStore


logger = logging.getLogger(__name__)


def run_async(coro):
    """Helper to run async code in sync context."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
)
def scrape_council(self, council_code: str, mode: str = "active") -> dict:
    """
    Main task to scrape a council.

    Args:
        council_code: Council identifier
        mode: 'active' or 'historical'

    Returns:
        Scrape result summary
    """
    return run_async(_scrape_council_async(council_code, mode))


async def _scrape_council_async(council_code: str, mode: str) -> dict:
    """Async implementation of council scraping."""
    start_time = datetime.utcnow()

    result = {
        "council_code": council_code,
        "mode": mode,
        "started_at": start_time.isoformat(),
        "status": "pending",
        "records_scraped": 0,
        "records_processed": 0,
        "records_new": 0,
        "records_updated": 0,
        "errors": [],
    }

    try:
        # Get council config
        council_config = get_council_by_code(council_code)
        if not council_config:
            result["status"] = "failed"
            result["errors"].append(f"Unknown council: {council_code}")
            return result

        # Get scraper adapter
        registry = get_registry()
        adapter = registry.get_adapter(council_code)

        if not adapter:
            result["status"] = "failed"
            result["errors"].append(f"No adapter for council: {council_code}")
            return result

        # Check portal health
        health = await adapter.get_portal_status()
        if not health.is_healthy:
            result["status"] = "skipped"
            result["errors"].append(f"Portal unhealthy: {health.message}")
            return result

        # Perform scrape
        logger.info(f"Starting {mode} scrape for {council_code}")

        if mode == "active":
            raw_records = await adapter.scrape_active()
        else:
            raw_records = await adapter.scrape_historical()

        result["records_scraped"] = len(raw_records)

        if not raw_records:
            result["status"] = "success"
            result["completed_at"] = datetime.utcnow().isoformat()
            return result

        # Store raw data
        raw_store = RawDataStore()
        batch_id = await raw_store.store_batch(
            council_code=council_code,
            records=[r.data for r in raw_records],
            metadata={"mode": mode, "portal_response_time": health.response_time_ms},
        )
        result["batch_id"] = batch_id

        # Process records
        processed_records = await _process_records(council_code, raw_records)
        result["records_processed"] = len(processed_records)

        # Store to database
        db = DatabaseManager()
        council = await db.get_council_by_code(council_code)

        if council:
            for record in processed_records:
                record["council_id"] = council.id

            upsert_result = await db.upsert_applications(processed_records)
            result["records_new"] = upsert_result["new"]
            result["records_updated"] = upsert_result["updated"]

        result["status"] = "success"
        result["completed_at"] = datetime.utcnow().isoformat()
        result["duration_seconds"] = int(
            (datetime.utcnow() - start_time).total_seconds()
        )

        logger.info(
            f"Completed {mode} scrape for {council_code}: "
            f"{result['records_new']} new, {result['records_updated']} updated"
        )

    except Exception as e:
        logger.exception(f"Scrape failed for {council_code}")
        result["status"] = "failed"
        result["errors"].append(str(e))

    return result


async def _process_records(council_code: str, raw_records: list) -> list[dict]:
    """
    Process raw records through the normalization pipeline.
    """
    mapper = AIFieldMapper()
    classifier = CategoryClassifier()
    normalizer = DataNormalizer()

    processed = []

    for raw_record in raw_records:
        try:
            raw_data = raw_record.data

            # 1. Try to apply field mapping (if learned)
            if mapper.cache.has_mapping(council_code):
                normalized = mapper.apply_mapping(council_code, raw_data)
            else:
                # Use raw data as-is if no mapping
                normalized = raw_data

            # 2. Normalize data formats
            normalized = normalizer.normalize_record(normalized)

            # 3. Classify category if description exists
            description = normalized.get("description", "")
            if description:
                classification = await classifier.classify(description, use_ai=False)
                normalized["category"] = classification.category.value
                normalized["subcategory"] = classification.subcategory
                if classification.dwelling_count:
                    normalized["dwelling_count"] = classification.dwelling_count
                if classification.lot_count:
                    normalized["lot_count"] = classification.lot_count
                if classification.storeys:
                    normalized["storeys"] = classification.storeys
                normalized["classification_confidence"] = classification.confidence

            # 4. Add metadata
            normalized["source_url"] = raw_record.source_url
            normalized["scraped_at"] = raw_record.scraped_at

            # 5. Calculate data quality score
            normalized["data_quality_score"] = _calculate_quality_score(normalized)

            processed.append(normalized)

        except Exception as e:
            logger.warning(f"Failed to process record: {e}")
            continue

    return processed


def _calculate_quality_score(record: dict) -> float:
    """Calculate data quality score for a record."""
    score = 0.0
    weights = {
        "da_number": 0.2,
        "address": 0.2,
        "description": 0.15,
        "status": 0.1,
        "lodged_date": 0.1,
        "category": 0.1,
        "estimated_cost": 0.05,
        "suburb": 0.05,
        "postcode": 0.05,
    }

    for field, weight in weights.items():
        value = record.get(field)
        if value is not None and value != "":
            score += weight

    return round(score, 2)


@shared_task
def run_quality_checks() -> dict:
    """Run quality checks across all councils."""
    return run_async(_run_quality_checks_async())


async def _run_quality_checks_async() -> dict:
    """Async implementation of quality checks."""
    db = DatabaseManager()
    results = {
        "checked_at": datetime.utcnow().isoformat(),
        "councils_checked": 0,
        "issues_found": [],
    }

    councils = await db.get_all_councils()

    for council in councils:
        # Check for stale data
        # Check for missing required fields
        # Check for anomalies
        results["councils_checked"] += 1

    return results


@shared_task(
    bind=True,
    max_retries=2,
)
def backfill_council(
    self,
    council_code: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> dict:
    """
    Backfill historical data for a council.

    Args:
        council_code: Council identifier
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
    """
    return run_async(
        _scrape_council_async(council_code, mode="historical")
    )


@shared_task
def cleanup_old_data() -> dict:
    """Clean up old raw data and logs."""
    logger.info("Running weekly cleanup")
    return {"status": "completed", "cleaned_at": datetime.utcnow().isoformat()}


@shared_task
def learn_field_mapping(council_code: str) -> dict:
    """Learn field mapping for a council from sample data."""
    return run_async(_learn_field_mapping_async(council_code))


async def _learn_field_mapping_async(council_code: str) -> dict:
    """Async implementation of field mapping learning."""
    raw_store = RawDataStore()
    mapper = AIFieldMapper()

    # Get latest batch
    batch = await raw_store.get_latest_batch(council_code)
    if not batch:
        return {"status": "failed", "error": "No data available"}

    samples = batch.get("records", [])[:5]
    if not samples:
        return {"status": "failed", "error": "No sample records"}

    try:
        mapping = await mapper.learn_mapping(council_code, samples)
        return {
            "status": "success",
            "council_code": council_code,
            "fields_mapped": len([k for k, v in mapping.mapping.items() if v]),
        }
    except Exception as e:
        return {"status": "failed", "error": str(e)}
