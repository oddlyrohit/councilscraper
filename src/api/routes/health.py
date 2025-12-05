"""Health check endpoints."""

from datetime import datetime

from fastapi import APIRouter

from src.storage.database import DatabaseManager


router = APIRouter()


@router.get("/health")
async def health_check():
    """Basic health check."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check with component status."""
    db = DatabaseManager()

    try:
        council_count = await db.count_active_councils()
        app_count = await db.count_applications()
        db_healthy = True
    except Exception as e:
        db_healthy = False
        council_count = 0
        app_count = 0

    return {
        "status": "healthy" if db_healthy else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {
            "database": {
                "status": "healthy" if db_healthy else "unhealthy",
                "councils": council_count,
                "applications": app_count,
            },
        },
    }
