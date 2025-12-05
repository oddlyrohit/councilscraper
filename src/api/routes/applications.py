"""Application endpoints."""

from datetime import date, datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from src.storage.database import DatabaseManager


router = APIRouter()


class ApplicationResponse(BaseModel):
    """Application response model."""
    id: str
    da_number: str
    council_code: Optional[str] = None
    council_name: Optional[str] = None
    address: str
    suburb: Optional[str] = None
    postcode: Optional[str] = None
    state: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    status: Optional[str] = None
    decision: Optional[str] = None
    lodged_date: Optional[str] = None
    determined_date: Optional[str] = None
    estimated_cost: Optional[float] = None
    dwelling_count: Optional[int] = None
    storeys: Optional[int] = None
    coordinates: Optional[dict] = None
    source_url: Optional[str] = None
    data_quality_score: Optional[float] = None


class PaginationMeta(BaseModel):
    """Pagination metadata."""
    page: int
    limit: int
    total: int
    pages: int


class ApplicationListResponse(BaseModel):
    """Paginated list of applications."""
    data: list[ApplicationResponse]
    meta: PaginationMeta


@router.get("/applications", response_model=ApplicationListResponse)
async def list_applications(
    council: Optional[str] = Query(None, description="Filter by council code"),
    status: Optional[str] = Query(None, description="Filter by status"),
    category: Optional[str] = Query(None, description="Filter by category"),
    suburb: Optional[str] = Query(None, description="Filter by suburb"),
    postcode: Optional[str] = Query(None, description="Filter by postcode"),
    lodged_after: Optional[date] = Query(None, description="Filter by lodged date"),
    lodged_before: Optional[date] = Query(None, description="Filter by lodged date"),
    min_cost: Optional[float] = Query(None, description="Minimum estimated cost"),
    max_cost: Optional[float] = Query(None, description="Maximum estimated cost"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=200, description="Items per page"),
):
    """
    Search and list development applications.

    Supports filtering by council, status, category, location, date range, and cost.
    Results are paginated and sorted by lodged date (newest first).
    """
    db = DatabaseManager()

    offset = (page - 1) * limit

    applications, total = await db.search_applications(
        council_code=council,
        status=status,
        category=category,
        suburb=suburb,
        postcode=postcode,
        lodged_after=datetime.combine(lodged_after, datetime.min.time()) if lodged_after else None,
        lodged_before=datetime.combine(lodged_before, datetime.max.time()) if lodged_before else None,
        min_cost=min_cost,
        max_cost=max_cost,
        limit=limit,
        offset=offset,
    )

    data = []
    for app in applications:
        data.append(ApplicationResponse(
            id=str(app.id),
            da_number=app.da_number,
            council_code=app.council.code if app.council else None,
            council_name=app.council.name if app.council else None,
            address=app.address,
            suburb=app.suburb,
            postcode=app.postcode,
            state=app.state,
            description=app.description,
            category=app.category,
            status=app.status,
            decision=app.decision,
            lodged_date=app.lodged_date.isoformat() if app.lodged_date else None,
            determined_date=app.determined_date.isoformat() if app.determined_date else None,
            estimated_cost=float(app.estimated_cost) if app.estimated_cost else None,
            dwelling_count=app.dwelling_count,
            storeys=app.storeys,
            source_url=app.source_url,
            data_quality_score=float(app.data_quality_score) if app.data_quality_score else None,
        ))

    pages = (total + limit - 1) // limit if total > 0 else 0

    return ApplicationListResponse(
        data=data,
        meta=PaginationMeta(
            page=page,
            limit=limit,
            total=total,
            pages=pages,
        ),
    )


@router.get("/applications/near")
async def get_applications_near(
    lat: float = Query(..., description="Latitude"),
    lng: float = Query(..., description="Longitude"),
    radius_km: float = Query(5.0, ge=0.1, le=50, description="Radius in kilometers"),
    limit: int = Query(50, ge=1, le=200, description="Maximum results"),
):
    """
    Find development applications near a location.

    Returns applications within the specified radius, sorted by distance.
    """
    db = DatabaseManager()

    applications = await db.get_applications_near(
        lat=lat,
        lng=lng,
        radius_km=radius_km,
        limit=limit,
    )

    data = []
    for app in applications:
        data.append({
            "id": str(app.id),
            "da_number": app.da_number,
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
            "center": {"lat": lat, "lng": lng},
            "radius_km": radius_km,
            "count": len(data),
        },
    }


@router.get("/applications/{application_id}")
async def get_application(application_id: UUID):
    """
    Get a single application by ID.

    Returns full details including documents.
    """
    db = DatabaseManager()

    app = await db.get_application_by_id(application_id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    return {
        "id": str(app.id),
        "da_number": app.da_number,
        "council": {
            "code": app.council.code if app.council else None,
            "name": app.council.name if app.council else None,
            "state": app.council.state if app.council else None,
        },
        "property": {
            "address": app.address,
            "suburb": app.suburb,
            "postcode": app.postcode,
            "state": app.state,
            "lot_plan": app.lot_plan,
        },
        "application": {
            "type": app.application_type,
            "category": app.category,
            "subcategory": app.subcategory,
            "description": app.description,
        },
        "status": app.status,
        "decision": app.decision,
        "dates": {
            "lodged": app.lodged_date.isoformat() if app.lodged_date else None,
            "exhibition_start": app.exhibition_start.isoformat() if app.exhibition_start else None,
            "exhibition_end": app.exhibition_end.isoformat() if app.exhibition_end else None,
            "determined": app.determined_date.isoformat() if app.determined_date else None,
        },
        "details": {
            "estimated_cost": float(app.estimated_cost) if app.estimated_cost else None,
            "dwelling_count": app.dwelling_count,
            "lot_count": app.lot_count,
            "storeys": app.storeys,
            "car_spaces": app.car_spaces,
        },
        "applicant": {
            "name": app.applicant_name,
            "type": app.applicant_type,
        },
        "documents": [
            {
                "name": doc.name,
                "url": doc.url,
                "type": doc.doc_type,
            }
            for doc in app.documents
        ],
        "metadata": {
            "source_url": app.source_url,
            "scraped_at": app.scraped_at.isoformat() if app.scraped_at else None,
            "data_quality_score": float(app.data_quality_score) if app.data_quality_score else None,
        },
    }
