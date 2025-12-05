"""Database connection and session management."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional
from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import select, func, and_, or_, text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


# Lazy imports to avoid circular dependencies and connection at import time
_Base = None
_models_imported = False


def _import_models():
    """Import models lazily to avoid import-time database connection."""
    global _Base, _models_imported
    if not _models_imported:
        from src.models import (
            Base,
            Council,
            Application,
            ApplicationDocument,
            ScrapeLog,
            FieldMappingModel,
        )
        _Base = Base
        _models_imported = True
    return _Base


def get_async_database_url(url: str) -> str:
    """Convert database URL to async format for SQLAlchemy.

    Supabase provides: postgresql://user:pass@host:5432/db
    SQLAlchemy async needs: postgresql+asyncpg://user:pass@host:5432/db
    """
    if not url:
        # Return None to indicate no database configured
        return None
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+asyncpg://", 1)
    return url


# Lazy engine creation
_engine = None
_async_session_factory = None


def get_engine():
    """Get or create the database engine (lazy initialization)."""
    global _engine
    if _engine is None:
        from src.config import settings
        db_url = get_async_database_url(settings.database_url)
        if db_url is None:
            raise RuntimeError(
                "DATABASE_URL environment variable is not set. "
                "Please configure it in Render → Environment settings with your Supabase connection string."
            )
        _engine = create_async_engine(
            db_url,
            pool_size=settings.db_pool_size,
            max_overflow=settings.db_max_overflow,
            echo=settings.api_debug,
            pool_pre_ping=True,
        )
    return _engine


def get_session_factory():
    """Get or create the session factory (lazy initialization)."""
    global _async_session_factory
    if _async_session_factory is None:
        _async_session_factory = async_sessionmaker(
            get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _async_session_factory


async def init_db() -> None:
    """Initialize database tables."""
    Base = _import_models()
    async with get_engine().begin() as conn:
        # Enable PostGIS extension
        await conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))
        await conn.execute(text('CREATE EXTENSION IF NOT EXISTS "postgis"'))
        await conn.execute(text('CREATE EXTENSION IF NOT EXISTS "pg_trgm"'))
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session for dependency injection."""
    async with get_session_factory()() as session:
        try:
            yield session
        finally:
            await session.close()


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Context manager for database sessions."""
    async with get_session_factory()() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


class DatabaseManager:
    """Database operations manager."""

    def __init__(self, session: Optional[AsyncSession] = None):
        self._session = session
        self._models = None

    def _get_models(self):
        """Lazy import models."""
        if self._models is None:
            from src.models import (
                Council,
                Application,
                ApplicationDocument,
                ScrapeLog,
                FieldMappingModel,
            )
            self._models = {
                'Council': Council,
                'Application': Application,
                'ApplicationDocument': ApplicationDocument,
                'ScrapeLog': ScrapeLog,
                'FieldMappingModel': FieldMappingModel,
            }
        return self._models

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get a session, either injected or new."""
        if self._session:
            yield self._session
        else:
            async with get_session() as session:
                yield session

    # -------------------------------------------------------------------------
    # Council Operations
    # -------------------------------------------------------------------------

    async def get_council_by_code(self, code: str):
        """Get council by code."""
        models = self._get_models()
        Council = models['Council']
        async with self.session() as session:
            result = await session.execute(
                select(Council).where(Council.code == code)
            )
            return result.scalar_one_or_none()

    async def get_all_councils(self):
        """Get all councils."""
        models = self._get_models()
        Council = models['Council']
        async with self.session() as session:
            result = await session.execute(
                select(Council).order_by(Council.tier, Council.name)
            )
            return list(result.scalars().all())

    async def get_councils_by_tier(self, tier: int):
        """Get councils by tier."""
        models = self._get_models()
        Council = models['Council']
        async with self.session() as session:
            result = await session.execute(
                select(Council).where(Council.tier == tier).order_by(Council.name)
            )
            return list(result.scalars().all())

    async def upsert_council(self, council_data: dict):
        """Insert or update a council."""
        models = self._get_models()
        Council = models['Council']
        async with self.session() as session:
            existing = await session.execute(
                select(Council).where(Council.code == council_data["code"])
            )
            council = existing.scalar_one_or_none()

            if council:
                for key, value in council_data.items():
                    if hasattr(council, key):
                        setattr(council, key, value)
            else:
                council = Council(**council_data)
                session.add(council)

            await session.flush()
            return council

    async def count_active_councils(self) -> int:
        """Count councils with active scrapers."""
        models = self._get_models()
        Council = models['Council']
        async with self.session() as session:
            result = await session.execute(
                select(func.count(Council.id)).where(Council.scraper_status == "active")
            )
            return result.scalar() or 0

    # -------------------------------------------------------------------------
    # Application Operations
    # -------------------------------------------------------------------------

    async def get_application_by_id(self, app_id: UUID):
        """Get application by ID."""
        models = self._get_models()
        Application = models['Application']
        async with self.session() as session:
            result = await session.execute(
                select(Application).where(Application.id == app_id)
            )
            return result.scalar_one_or_none()

    async def get_application_by_da_number(self, council_id: int, da_number: str):
        """Get application by council and DA number."""
        models = self._get_models()
        Application = models['Application']
        async with self.session() as session:
            result = await session.execute(
                select(Application).where(
                    and_(
                        Application.council_id == council_id,
                        Application.da_number == da_number,
                    )
                )
            )
            return result.scalar_one_or_none()

    async def search_applications(
        self,
        council_code: Optional[str] = None,
        status: Optional[str] = None,
        category: Optional[str] = None,
        suburb: Optional[str] = None,
        postcode: Optional[str] = None,
        lodged_after: Optional[datetime] = None,
        lodged_before: Optional[datetime] = None,
        min_cost: Optional[float] = None,
        max_cost: Optional[float] = None,
        search_text: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list, int]:
        """Search applications with filters."""
        models = self._get_models()
        Application = models['Application']
        Council = models['Council']

        async with self.session() as session:
            query = select(Application).join(Council)
            count_query = select(func.count(Application.id)).join(Council)

            conditions = []

            if council_code:
                conditions.append(Council.code == council_code)
            if status:
                conditions.append(Application.status == status)
            if category:
                conditions.append(Application.category == category)
            if suburb:
                conditions.append(Application.suburb.ilike(f"%{suburb}%"))
            if postcode:
                conditions.append(Application.postcode == postcode)
            if lodged_after:
                conditions.append(Application.lodged_date >= lodged_after)
            if lodged_before:
                conditions.append(Application.lodged_date <= lodged_before)
            if min_cost:
                conditions.append(Application.estimated_cost >= min_cost)
            if max_cost:
                conditions.append(Application.estimated_cost <= max_cost)
            if search_text:
                conditions.append(
                    or_(
                        Application.description.ilike(f"%{search_text}%"),
                        Application.address.ilike(f"%{search_text}%"),
                    )
                )

            if conditions:
                query = query.where(and_(*conditions))
                count_query = count_query.where(and_(*conditions))

            # Get total count
            count_result = await session.execute(count_query)
            total = count_result.scalar() or 0

            # Get paginated results
            query = query.order_by(Application.lodged_date.desc())
            query = query.offset(offset).limit(limit)

            result = await session.execute(query)
            applications = list(result.scalars().all())

            return applications, total

    async def upsert_application(self, app_data: dict) -> tuple:
        """Insert or update an application. Returns (application, is_new)."""
        models = self._get_models()
        Application = models['Application']

        async with self.session() as session:
            existing = await session.execute(
                select(Application).where(
                    and_(
                        Application.council_id == app_data["council_id"],
                        Application.da_number == app_data["da_number"],
                    )
                )
            )
            application = existing.scalar_one_or_none()
            is_new = application is None

            if application:
                for key, value in app_data.items():
                    if hasattr(application, key) and key not in ("id", "council_id", "da_number"):
                        setattr(application, key, value)
                application.updated_at = datetime.utcnow()
            else:
                application = Application(**app_data)
                session.add(application)

            await session.flush()
            return application, is_new

    async def upsert_applications(self, applications: list[dict]) -> dict:
        """Bulk upsert applications."""
        results = {"new": 0, "updated": 0, "errors": 0}

        for app_data in applications:
            try:
                _, is_new = await self.upsert_application(app_data)
                if is_new:
                    results["new"] += 1
                else:
                    results["updated"] += 1
            except Exception:
                results["errors"] += 1

        return results

    async def count_applications(self) -> int:
        """Count total applications."""
        models = self._get_models()
        Application = models['Application']

        async with self.session() as session:
            result = await session.execute(select(func.count(Application.id)))
            return result.scalar() or 0

    async def get_applications_near(
        self,
        lat: float,
        lng: float,
        radius_km: float = 5.0,
        limit: int = 50,
    ):
        """Get applications within radius of a point."""
        models = self._get_models()
        Application = models['Application']

        async with self.session() as session:
            point = func.ST_SetSRID(func.ST_MakePoint(lng, lat), 4326)
            distance_meters = radius_km * 1000

            result = await session.execute(
                select(Application)
                .where(
                    func.ST_DWithin(
                        Application.coordinates,
                        func.ST_Transform(point, 4326),
                        distance_meters,
                    )
                )
                .order_by(func.ST_Distance(Application.coordinates, point))
                .limit(limit)
            )
            return list(result.scalars().all())

    # -------------------------------------------------------------------------
    # Scrape Log Operations
    # -------------------------------------------------------------------------

    async def log_scrape_run(self, log_data: dict):
        """Log a scrape run."""
        models = self._get_models()
        ScrapeLog = models['ScrapeLog']

        async with self.session() as session:
            log = ScrapeLog(**log_data)
            session.add(log)
            await session.flush()
            return log

    async def count_recent_scrapes(self, hours: int = 24) -> int:
        """Count scrapes in last N hours."""
        models = self._get_models()
        ScrapeLog = models['ScrapeLog']

        async with self.session() as session:
            cutoff = datetime.utcnow() - timedelta(hours=hours)
            result = await session.execute(
                select(func.count(ScrapeLog.id)).where(ScrapeLog.started_at >= cutoff)
            )
            return result.scalar() or 0

    async def get_failed_scrapers(self, hours: int = 24, min_failures: int = 3) -> list[str]:
        """Get council codes with repeated failures."""
        models = self._get_models()
        Council = models['Council']
        ScrapeLog = models['ScrapeLog']

        async with self.session() as session:
            cutoff = datetime.utcnow() - timedelta(hours=hours)
            result = await session.execute(
                select(Council.code)
                .join(ScrapeLog)
                .where(
                    and_(
                        ScrapeLog.status == "failed",
                        ScrapeLog.started_at >= cutoff,
                    )
                )
                .group_by(Council.code)
                .having(func.count(ScrapeLog.id) >= min_failures)
            )
            return [row[0] for row in result.all()]

    # -------------------------------------------------------------------------
    # Field Mapping Operations
    # -------------------------------------------------------------------------

    async def get_field_mapping(self, council_id: int):
        """Get field mapping for a council."""
        models = self._get_models()
        FieldMappingModel = models['FieldMappingModel']

        async with self.session() as session:
            result = await session.execute(
                select(FieldMappingModel).where(FieldMappingModel.council_id == council_id)
            )
            return result.scalar_one_or_none()

    async def save_field_mapping(self, council_id: int, mapping_data: dict):
        """Save field mapping for a council."""
        models = self._get_models()
        FieldMappingModel = models['FieldMappingModel']

        async with self.session() as session:
            existing = await session.execute(
                select(FieldMappingModel).where(FieldMappingModel.council_id == council_id)
            )
            mapping = existing.scalar_one_or_none()

            now = datetime.utcnow()
            if mapping:
                mapping.mapping = mapping_data.get("mapping", {})
                mapping.status_values = mapping_data.get("status_values", {})
                mapping.sample_count = mapping_data.get("sample_count", 0)
                mapping.confidence = mapping_data.get("confidence", 0.0)
                mapping.updated_at = now
            else:
                mapping = FieldMappingModel(
                    council_id=council_id,
                    mapping=mapping_data.get("mapping", {}),
                    status_values=mapping_data.get("status_values", {}),
                    sample_count=mapping_data.get("sample_count", 0),
                    confidence=mapping_data.get("confidence", 0.0),
                    learned_at=now,
                    updated_at=now,
                )
                session.add(mapping)

            await session.flush()
            return mapping
