"""Search endpoints."""

from typing import Optional

from fastapi import APIRouter, Query

from src.storage.database import DatabaseManager


router = APIRouter()


@router.get("/search")
async def search_applications(
    q: str = Query(..., min_length=2, description="Search query"),
    council: Optional[str] = Query(None, description="Filter by council code"),
    category: Optional[str] = Query(None, description="Filter by category"),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
):
    """
    Full-text search across applications.

    Searches in description and address fields.
    """
    db = DatabaseManager()

    offset = (page - 1) * limit

    applications, total = await db.search_applications(
        council_code=council,
        category=category,
        search_text=q,
        limit=limit,
        offset=offset,
    )

    data = []
    for app in applications:
        data.append({
            "id": str(app.id),
            "da_number": app.da_number,
            "council_code": app.council.code if app.council else None,
            "address": app.address,
            "suburb": app.suburb,
            "description": app.description,
            "status": app.status,
            "category": app.category,
            "lodged_date": app.lodged_date.isoformat() if app.lodged_date else None,
        })

    return {
        "data": data,
        "meta": {
            "query": q,
            "page": page,
            "limit": limit,
            "total": total,
            "pages": (total + limit - 1) // limit if total > 0 else 0,
        },
    }


@router.get("/search/suggestions")
async def get_search_suggestions(
    q: str = Query(..., min_length=2, description="Partial search query"),
    limit: int = Query(10, ge=1, le=20),
):
    """
    Get search suggestions based on partial query.

    Returns matching suburbs, addresses, and description keywords.
    """
    # Placeholder - would query database for common terms
    return {
        "suggestions": [],
        "query": q,
    }


@router.get("/search/categories")
async def list_categories():
    """
    List all available application categories.
    """
    from src.schemas.enums import ApplicationCategory

    return {
        "categories": [
            {
                "value": cat.value,
                "label": cat.value.replace("_", " ").title(),
            }
            for cat in ApplicationCategory
        ],
    }


@router.get("/search/statuses")
async def list_statuses():
    """
    List all available application statuses.
    """
    from src.schemas.enums import ApplicationStatus

    return {
        "statuses": [
            {
                "value": status.value,
                "label": status.value.replace("_", " ").title(),
            }
            for status in ApplicationStatus
        ],
    }
