#!/usr/bin/env python3
"""
Council Scraper Runner
Runs scrapers for specified tier with concurrency control.

Usage:
    python run_scrapers.py --tier 1
    python run_scrapers.py --tier 2 --batch 1
    python run_scrapers.py --council sydney_city
    python run_scrapers.py --all
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

# Use tier definitions from the councils config
from src.config.councils import (
    TIER_1_COUNCILS as T1,
    TIER_2_COUNCILS as T2,
    TIER_3_COUNCILS as T3,
    TIER_4_COUNCILS as T4,
    TIER_5_COUNCILS as T5,
)

def get_tier_councils(tier: int, batch: int = None) -> list:
    """Get councils for specified tier, optionally split into batches."""
    if tier == 1:
        councils = [c.code for c in T1]
    elif tier == 2:
        councils = [c.code for c in T2]
        if batch is not None:
            # Split tier 2 into 3 batches
            batch_size = len(councils) // 3 + 1
            start = (batch - 1) * batch_size
            end = start + batch_size
            councils = councils[start:end]
    elif tier == 3:
        councils = [c.code for c in T3]
        if batch is not None:
            # Split tier 3 into 7 batches (one per day)
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


async def run_scraper(council_code: str, semaphore: asyncio.Semaphore) -> dict:
    """Run scraper for a single council with concurrency control."""
    async with semaphore:
        logger.info(f"Starting scraper for {council_code}")
        start_time = datetime.now()

        try:
            # Import here to avoid loading all scrapers at startup
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
            logger.error(f"Error scraping {council_code}: {e}")
            return {
                "council": council_code,
                "status": "error",
                "error": str(e),
                "duration": (datetime.now() - start_time).seconds
            }


async def run_scrapers(council_codes: list, max_concurrent: int = 3):
    """Run multiple scrapers with concurrency limit."""
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

    return results


def main():
    parser = argparse.ArgumentParser(description="Run council scrapers")
    parser.add_argument("--tier", type=int, choices=[1, 2, 3], help="Run specific tier")
    parser.add_argument("--batch", type=int, help="Batch number for tier 2/3")
    parser.add_argument("--council", type=str, help="Run single council by code")
    parser.add_argument("--all", action="store_true", help="Run all councils")
    parser.add_argument("--concurrent", type=int, default=3, help="Max concurrent scrapers")
    parser.add_argument("--dry-run", action="store_true", help="List councils without running")

    args = parser.parse_args()

    # Determine which councils to run
    if args.council:
        councils = [args.council]
    elif args.tier:
        councils = get_tier_councils(args.tier, args.batch)
    elif args.all:
        councils = [c.code for c in ALL_COUNCILS]
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
        return

    # Run scrapers
    asyncio.run(run_scrapers(councils, args.concurrent))


if __name__ == "__main__":
    main()
