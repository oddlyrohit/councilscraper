#!/usr/bin/env python3
"""
Council Scraper Runner with Monitoring
Runs scrapers and sends email alerts on failures.

Usage:
    python run_with_monitoring.py --tier 1
    python run_with_monitoring.py --tier 2 --batch 1
    python run_with_monitoring.py --council sydney_city
    python run_with_monitoring.py --digest  # Send daily digest
"""

import argparse
import asyncio
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv(Path.home() / ".env")

from src.config.councils import ALL_COUNCILS, get_council_by_code
from src.monitoring.alerts import AlertManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(
            Path.home() / "logs" / f"scraper_{datetime.now().strftime('%Y%m%d')}.log"
        )
    ]
)
logger = logging.getLogger(__name__)

# Import tier definitions
from src.config.councils import (
    TIER_1_COUNCILS as T1,
    TIER_2_COUNCILS as T2,
    TIER_3_COUNCILS as T3,
    TIER_4_COUNCILS as T4,
    TIER_5_COUNCILS as T5,
)

# Initialize alert manager
alert_manager = AlertManager()


def get_tier_councils(tier: int, batch: int = None) -> list:
    """Get councils for specified tier, optionally split into batches."""
    if tier == 1:
        councils = [c.code for c in T1]
    elif tier == 2:
        councils = [c.code for c in T2]
        if batch is not None:
            batch_size = len(councils) // 3 + 1
            start = (batch - 1) * batch_size
            end = start + batch_size
            councils = councils[start:end]
    elif tier == 3:
        councils = [c.code for c in T3]
        if batch is not None:
            batch_size = len(councils) // 7 + 1
            start = (batch - 1) * batch_size
            end = start + batch_size
            councils = councils[start:end]
    elif tier == 4:
        councils = [c.code for c in T4]
        if batch is not None:
            batch_size = len(councils) // 7 + 1
            start = (batch - 1) * batch_size
            end = start + batch_size
            councils = councils[start:end]
    elif tier == 5:
        councils = [c.code for c in T5]
        if batch is not None:
            batch_size = len(councils) // 7 + 1
            start = (batch - 1) * batch_size
            end = start + batch_size
            councils = councils[start:end]
    else:
        councils = []

    return councils


def get_council_tier(council_code: str) -> int:
    """Get tier for a council code."""
    for c in T1:
        if c.code == council_code:
            return 1
    for c in T2:
        if c.code == council_code:
            return 2
    for c in T3:
        if c.code == council_code:
            return 3
    for c in T4:
        if c.code == council_code:
            return 4
    for c in T5:
        if c.code == council_code:
            return 5
    return 0


async def run_scraper(council_code: str, semaphore: asyncio.Semaphore) -> dict:
    """Run scraper for a single council with concurrency control."""
    async with semaphore:
        logger.info(f"Starting scraper for {council_code}")
        start_time = datetime.now()

        try:
            from src.scrapers import get_scraper_for_council
            from src.storage.database import DatabaseManager

            scraper = get_scraper_for_council(council_code)
            if not scraper:
                logger.warning(f"No scraper available for {council_code}")
                return {"council": council_code, "status": "no_scraper", "count": 0}

            # Run the scraper
            applications = await scraper.scrape()

            # Save to database
            if applications:
                db = DatabaseManager()
                results = await db.upsert_applications(applications)

                # Log to scrape_logs table
                try:
                    council = await db.get_council_by_code(council_code)
                    if council:
                        await db.log_scrape_run({
                            "council_id": council.id,
                            "started_at": start_time,
                            "completed_at": datetime.now(),
                            "status": "success",
                            "mode": "active",
                            "records_scraped": len(applications),
                            "records_processed": len(applications),
                            "records_new": results["new"],
                            "records_updated": results["updated"],
                            "duration_seconds": (datetime.now() - start_time).seconds,
                        })
                except Exception as log_err:
                    logger.warning(f"Failed to log scrape run: {log_err}")

                logger.info(
                    f"Completed {council_code}: {results['new']} new, "
                    f"{results['updated']} updated, {results['errors']} errors"
                )
                return {
                    "council": council_code,
                    "status": "success",
                    "new": results["new"],
                    "updated": results["updated"],
                    "errors": results["errors"],
                    "duration": (datetime.now() - start_time).seconds
                }
            else:
                logger.info(f"No applications found for {council_code}")
                return {"council": council_code, "status": "empty", "count": 0}

        except Exception as e:
            duration = (datetime.now() - start_time).seconds
            error_msg = str(e)
            logger.error(f"Error scraping {council_code}: {error_msg}")

            # Log failure to database
            try:
                from src.storage.database import DatabaseManager
                db = DatabaseManager()
                council = await db.get_council_by_code(council_code)
                if council:
                    await db.log_scrape_run({
                        "council_id": council.id,
                        "started_at": start_time,
                        "completed_at": datetime.now(),
                        "status": "failed",
                        "mode": "active",
                        "errors": {"message": error_msg},
                        "duration_seconds": duration,
                    })
            except Exception as log_err:
                logger.warning(f"Failed to log scrape failure: {log_err}")

            # Send immediate alert for individual failure
            tier = get_council_tier(council_code)
            alert_manager.send_scraper_failure_alert(
                council_code=council_code,
                error_message=error_msg,
                tier=tier,
                duration=duration,
            )

            return {
                "council": council_code,
                "status": "error",
                "error": error_msg,
                "duration": duration
            }


async def run_scrapers(
    council_codes: list,
    max_concurrent: int = 3,
    tier: int = None,
    batch: int = None,
) -> list:
    """Run multiple scrapers with concurrency limit and monitoring."""
    semaphore = asyncio.Semaphore(max_concurrent)

    logger.info(f"Running {len(council_codes)} scrapers (max {max_concurrent} concurrent)")

    tasks = [run_scraper(code, semaphore) for code in council_codes]
    results = await asyncio.gather(*tasks)

    # Summary
    success = sum(1 for r in results if r["status"] == "success")
    errors = sum(1 for r in results if r["status"] == "error")
    total_new = sum(r.get("new", 0) for r in results)
    total_updated = sum(r.get("updated", 0) for r in results)

    logger.info("=" * 50)
    logger.info(f"SCRAPING COMPLETE")
    logger.info(f"Councils: {success} success, {errors} errors")
    logger.info(f"Applications: {total_new} new, {total_updated} updated")
    logger.info("=" * 50)

    # Send batch summary alert if there were any errors
    if errors > 0 and tier is not None:
        alert_manager.send_batch_summary_alert(
            tier=tier,
            batch=batch,
            results=results,
        )

    return results


async def send_daily_digest():
    """Send daily digest email."""
    try:
        from src.storage.database import get_session
        from src.monitoring.status import ScraperStatus

        async with get_session() as session:
            status = ScraperStatus(session)
            stats = await status.get_overall_stats(hours=24)
            failed_councils = await status.get_failed_councils(hours=24, min_failures=3)

            success = alert_manager.send_daily_digest(stats, failed_councils)

            if success:
                logger.info("Daily digest sent successfully")
            else:
                logger.error("Failed to send daily digest")

    except Exception as e:
        logger.error(f"Error sending daily digest: {e}")


def main():
    parser = argparse.ArgumentParser(description="Run council scrapers with monitoring")
    parser.add_argument("--tier", type=int, choices=[1, 2, 3, 4, 5], help="Run specific tier")
    parser.add_argument("--batch", type=int, help="Batch number for tier 2-5")
    parser.add_argument("--council", type=str, help="Run single council by code")
    parser.add_argument("--all", action="store_true", help="Run all councils")
    parser.add_argument("--concurrent", type=int, default=3, help="Max concurrent scrapers")
    parser.add_argument("--dry-run", action="store_true", help="List councils without running")
    parser.add_argument("--digest", action="store_true", help="Send daily digest email")

    args = parser.parse_args()

    # Handle daily digest
    if args.digest:
        asyncio.run(send_daily_digest())
        return

    # Determine which councils to run
    if args.council:
        councils = [args.council]
        tier = get_council_tier(args.council)
        batch = None
    elif args.tier:
        councils = get_tier_councils(args.tier, args.batch)
        tier = args.tier
        batch = args.batch
    elif args.all:
        councils = [c.code for c in ALL_COUNCILS]
        tier = None
        batch = None
    else:
        parser.print_help()
        return

    if not councils:
        logger.error("No councils to scrape")
        return

    if args.dry_run:
        print(f"Would scrape {len(councils)} councils:")
        for c in councils:
            print(f"  - {c}")
        print(f"\nEmail alerts configured: {alert_manager.is_configured()}")
        print(f"Alert recipient: {alert_manager.to_email}")
        return

    # Run scrapers
    asyncio.run(run_scrapers(councils, args.concurrent, tier, batch))


if __name__ == "__main__":
    main()
