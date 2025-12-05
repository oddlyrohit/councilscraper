"""Council endpoints."""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from src.config.councils import ALL_COUNCILS, get_council_by_code, State, PortalType
from src.storage.database import DatabaseManager


router = APIRouter()


class CouncilResponse(BaseModel):
    """Council response model."""
    code: str
    name: str
    state: str
    population: Optional[int] = None
    tier: int
    portal_type: Optional[str] = None
    scraper_status: str = "pending"
    metro_area: Optional[str] = None


class CouncilStatsResponse(BaseModel):
    """Council statistics response."""
    code: str
    name: str
    total_applications: int
    last_30_days: int
    last_scraped: Optional[str] = None
    avg_quality_score: Optional[float] = None
    categories: dict
    statuses: dict


@router.get("/councils")
async def list_councils(
    state: Optional[str] = Query(None, description="Filter by state (NSW, VIC, etc.)"),
    tier: Optional[int] = Query(None, ge=1, le=4, description="Filter by tier (1-4)"),
    portal_type: Optional[str] = Query(None, description="Filter by portal type"),
    has_scraper: Optional[bool] = Query(None, description="Filter by scraper availability"),
):
    """
    List all councils with optional filters.

    Returns council metadata and scraper status.
    """
    councils = ALL_COUNCILS

    if state:
        councils = [c for c in councils if c.state.value == state.upper()]

    if tier:
        councils = [c for c in councils if c.tier == tier]

    if portal_type:
        councils = [c for c in councils if c.portal_type and c.portal_type.value == portal_type]

    data = []
    for council in councils:
        data.append(CouncilResponse(
            code=council.code,
            name=council.name,
            state=council.state.value,
            population=council.population,
            tier=council.tier,
            portal_type=council.portal_type.value if council.portal_type else None,
            scraper_status=council.scraper_status.value,
            metro_area=council.metro_area,
        ))

    return {
        "data": data,
        "meta": {
            "total": len(data),
            "by_state": _count_by_state(councils),
            "by_tier": _count_by_tier(councils),
        },
    }


@router.get("/councils/{council_code}")
async def get_council(council_code: str):
    """
    Get details for a single council.
    """
    council = get_council_by_code(council_code.upper())
    if not council:
        raise HTTPException(status_code=404, detail="Council not found")

    return {
        "code": council.code,
        "name": council.name,
        "state": council.state.value,
        "population": council.population,
        "tier": council.tier,
        "portal_url": council.portal_url,
        "portal_type": council.portal_type.value if council.portal_type else None,
        "scraper_status": council.scraper_status.value,
        "metro_area": council.metro_area,
        "lga_code": council.lga_code,
        "notes": council.notes,
    }


@router.get("/councils/{council_code}/stats")
async def get_council_stats(council_code: str):
    """
    Get statistics for a council.

    Returns application counts, categories breakdown, and scraper metrics.
    """
    council = get_council_by_code(council_code.upper())
    if not council:
        raise HTTPException(status_code=404, detail="Council not found")

    db = DatabaseManager()
    db_council = await db.get_council_by_code(council_code.upper())

    if not db_council:
        return {
            "code": council.code,
            "name": council.name,
            "total_applications": 0,
            "last_30_days": 0,
            "categories": {},
            "statuses": {},
            "message": "No data available yet",
        }

    # Get application stats from database
    # This is a placeholder - real implementation would query aggregations
    return {
        "code": council.code,
        "name": council.name,
        "total_applications": 0,
        "last_30_days": 0,
        "last_scraped": db_council.last_scraped_at,
        "categories": {},
        "statuses": {},
    }


@router.get("/councils/states/summary")
async def get_states_summary():
    """
    Get summary of councils by state.
    """
    summary = {}

    for state in State:
        councils = [c for c in ALL_COUNCILS if c.state == state]
        if councils:
            summary[state.value] = {
                "council_count": len(councils),
                "total_population": sum(c.population for c in councils if c.population),
                "tier_1_count": len([c for c in councils if c.tier == 1]),
            }

    return summary


@router.get("/councils/portal-types/summary")
async def get_portal_types_summary():
    """
    Get summary of councils by portal type.
    """
    summary = {}

    for pt in PortalType:
        councils = [c for c in ALL_COUNCILS if c.portal_type == pt]
        if councils:
            summary[pt.value] = {
                "council_count": len(councils),
                "states": list(set(c.state.value for c in councils)),
            }

    return summary


def _count_by_state(councils: list) -> dict:
    """Count councils by state."""
    counts = {}
    for council in councils:
        state = council.state.value
        counts[state] = counts.get(state, 0) + 1
    return counts


def _count_by_tier(councils: list) -> dict:
    """Count councils by tier."""
    counts = {}
    for council in councils:
        tier = f"tier_{council.tier}"
        counts[tier] = counts.get(tier, 0) + 1
    return counts
