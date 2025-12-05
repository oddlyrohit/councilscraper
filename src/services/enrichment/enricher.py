"""Data enrichment service for development applications."""

import asyncio
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from src.services.geocoding import Geocoder, GeocodingResult
from src.services.enrichment.property_lookup import PropertyLookup
from src.storage.database import DatabaseManager


logger = logging.getLogger(__name__)


@dataclass
class EnrichmentResult:
    """Result of enrichment operation."""

    application_id: UUID
    geocoding: Optional[GeocodingResult] = None
    property_data: Optional[dict] = None
    derived_fields: dict = field(default_factory=dict)
    quality_score: float = 0.0
    errors: list[str] = field(default_factory=list)


@dataclass
class DataQualityMetrics:
    """Metrics for data quality assessment."""

    has_address: bool = False
    has_suburb: bool = False
    has_postcode: bool = False
    has_coordinates: bool = False
    has_description: bool = False
    has_lodged_date: bool = False
    has_status: bool = False
    has_category: bool = False
    has_cost_estimate: bool = False
    has_documents: bool = False
    address_quality: float = 0.0  # 0.0 to 1.0
    description_quality: float = 0.0  # 0.0 to 1.0

    @property
    def overall_score(self) -> float:
        """Calculate overall quality score (0.0 to 1.0)."""
        weights = {
            "has_address": 0.15,
            "has_suburb": 0.05,
            "has_postcode": 0.05,
            "has_coordinates": 0.10,
            "has_description": 0.15,
            "has_lodged_date": 0.10,
            "has_status": 0.10,
            "has_category": 0.10,
            "has_cost_estimate": 0.05,
            "has_documents": 0.05,
            "address_quality": 0.05,
            "description_quality": 0.05,
        }

        score = 0.0
        for field_name, weight in weights.items():
            value = getattr(self, field_name)
            if isinstance(value, bool):
                score += weight * (1.0 if value else 0.0)
            else:
                score += weight * value

        return score


class DataEnricher:
    """
    Service for enriching development application data.

    Enrichment includes:
    - Geocoding addresses to coordinates
    - Property data lookup (lot/plan, zoning)
    - Derived field extraction (dwelling count, storeys, etc.)
    - Data quality scoring
    """

    def __init__(
        self,
        geocoder: Optional[Geocoder] = None,
        property_lookup: Optional[PropertyLookup] = None,
        db: Optional[DatabaseManager] = None,
    ):
        self.geocoder = geocoder or Geocoder()
        self.property_lookup = property_lookup or PropertyLookup()
        self.db = db or DatabaseManager()

    async def enrich_application(
        self,
        application_id: UUID,
        geocode: bool = True,
        lookup_property: bool = True,
        extract_derived: bool = True,
    ) -> EnrichmentResult:
        """
        Enrich a single application with additional data.

        Args:
            application_id: Application UUID
            geocode: Whether to geocode the address
            lookup_property: Whether to lookup property data
            extract_derived: Whether to extract derived fields

        Returns:
            EnrichmentResult with enriched data
        """
        result = EnrichmentResult(application_id=application_id)

        # Get application from database
        app = await self.db.get_application_by_id(application_id)
        if not app:
            result.errors.append("Application not found")
            return result

        # Run enrichment tasks concurrently
        tasks = []

        if geocode and app.address:
            tasks.append(self._geocode_application(app, result))

        if lookup_property and app.address:
            tasks.append(self._lookup_property(app, result))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

        # Extract derived fields (synchronous)
        if extract_derived:
            result.derived_fields = self._extract_derived_fields(app)

        # Calculate quality score
        result.quality_score = self._calculate_quality_score(app, result)

        # Update application in database
        await self._update_application(app, result)

        return result

    async def _geocode_application(self, app: Any, result: EnrichmentResult) -> None:
        """Geocode application address."""
        try:
            geocoding = await self.geocoder.geocode(
                address=app.address,
                suburb=app.suburb,
                postcode=app.postcode,
                state=app.state,
            )
            result.geocoding = geocoding
        except Exception as e:
            result.errors.append(f"Geocoding failed: {e}")
            logger.error(f"Geocoding failed for {app.id}: {e}")

    async def _lookup_property(self, app: Any, result: EnrichmentResult) -> None:
        """Lookup property data."""
        try:
            property_data = await self.property_lookup.lookup(
                address=app.address,
                suburb=app.suburb,
                state=app.state,
            )
            result.property_data = property_data
        except Exception as e:
            result.errors.append(f"Property lookup failed: {e}")
            logger.error(f"Property lookup failed for {app.id}: {e}")

    def _extract_derived_fields(self, app: Any) -> dict:
        """Extract derived fields from application description."""
        derived = {}
        description = (app.description or "").lower()

        # Extract dwelling count
        dwelling_patterns = [
            r"(\d+)\s*(?:unit|apartment|dwelling|residence|lot|townhouse)s?",
            r"(\d+)\s*x\s*(?:unit|apartment|dwelling|residence|lot|townhouse)s?",
            r"construction of\s*(\d+)",
        ]
        for pattern in dwelling_patterns:
            match = re.search(pattern, description)
            if match:
                derived["dwelling_count"] = int(match.group(1))
                break

        # Extract storey count
        storey_patterns = [
            r"(\d+)\s*(?:storey|story|level)s?",
            r"(\d+)\s*storeys?",
        ]
        for pattern in storey_patterns:
            match = re.search(pattern, description)
            if match:
                derived["storeys"] = int(match.group(1))
                break

        # Extract car spaces
        car_patterns = [
            r"(\d+)\s*(?:car\s*)?(?:space|park|garage)s?",
            r"(\d+)\s*basement\s*(?:car\s*)?(?:space|park)s?",
        ]
        for pattern in car_patterns:
            match = re.search(pattern, description)
            if match:
                derived["car_spaces"] = int(match.group(1))
                break

        # Detect demolition
        if any(word in description for word in ["demolition", "demolish", "remove existing"]):
            derived["includes_demolition"] = True

        # Detect subdivision
        if any(word in description for word in ["subdivision", "subdivide", "torrens title"]):
            derived["is_subdivision"] = True

        # Extract lot count for subdivisions
        if derived.get("is_subdivision"):
            lot_patterns = [
                r"(\d+)\s*(?:lot|allotment)s?",
                r"into\s*(\d+)\s*lots?",
            ]
            for pattern in lot_patterns:
                match = re.search(pattern, description)
                if match:
                    derived["lot_count"] = int(match.group(1))
                    break

        # Detect pool
        if any(word in description for word in ["pool", "swimming"]):
            derived["has_pool"] = True

        return derived

    def _calculate_quality_score(self, app: Any, result: EnrichmentResult) -> float:
        """Calculate data quality score for application."""
        metrics = DataQualityMetrics()

        # Check field presence
        metrics.has_address = bool(app.address)
        metrics.has_suburb = bool(app.suburb)
        metrics.has_postcode = bool(app.postcode)
        metrics.has_coordinates = bool(
            result.geocoding or (hasattr(app, 'latitude') and app.latitude)
        )
        metrics.has_description = bool(app.description)
        metrics.has_lodged_date = bool(app.lodged_date)
        metrics.has_status = bool(app.status)
        metrics.has_category = bool(app.category)
        metrics.has_cost_estimate = bool(app.estimated_cost)
        metrics.has_documents = bool(app.documents)

        # Assess address quality
        if app.address:
            address_parts = len(app.address.split())
            if address_parts >= 4:
                metrics.address_quality = 1.0
            elif address_parts >= 3:
                metrics.address_quality = 0.7
            elif address_parts >= 2:
                metrics.address_quality = 0.4
            else:
                metrics.address_quality = 0.2

        # Assess description quality
        if app.description:
            desc_len = len(app.description)
            if desc_len >= 100:
                metrics.description_quality = 1.0
            elif desc_len >= 50:
                metrics.description_quality = 0.7
            elif desc_len >= 20:
                metrics.description_quality = 0.4
            else:
                metrics.description_quality = 0.2

        return metrics.overall_score

    async def _update_application(self, app: Any, result: EnrichmentResult) -> None:
        """Update application with enrichment results."""
        updates = {}

        # Geocoding updates
        if result.geocoding:
            updates["latitude"] = result.geocoding.latitude
            updates["longitude"] = result.geocoding.longitude
            updates["geocoding_confidence"] = result.geocoding.confidence

            # Update location fields if improved
            if result.geocoding.suburb and not app.suburb:
                updates["suburb"] = result.geocoding.suburb
            if result.geocoding.postcode and not app.postcode:
                updates["postcode"] = result.geocoding.postcode

        # Property data updates
        if result.property_data:
            if result.property_data.get("lot_plan") and not app.lot_plan:
                updates["lot_plan"] = result.property_data["lot_plan"]
            if result.property_data.get("zoning"):
                updates["zoning"] = result.property_data["zoning"]

        # Derived field updates
        for field_name in ["dwelling_count", "storeys", "car_spaces", "lot_count"]:
            if field_name in result.derived_fields and not getattr(app, field_name, None):
                updates[field_name] = result.derived_fields[field_name]

        # Quality score
        updates["data_quality_score"] = result.quality_score
        updates["enriched_at"] = datetime.utcnow()

        if updates:
            await self.db.update_application(app.id, updates)

    async def enrich_batch(
        self,
        council_code: Optional[str] = None,
        limit: int = 100,
        concurrency: int = 5,
    ) -> dict:
        """
        Enrich a batch of applications.

        Returns summary statistics.
        """
        # Get applications needing enrichment
        applications = await self.db.get_applications_needing_enrichment(
            council_code=council_code,
            limit=limit,
        )

        stats = {
            "total": len(applications),
            "successful": 0,
            "failed": 0,
            "geocoded": 0,
            "property_enriched": 0,
            "average_quality_score": 0.0,
        }

        if not applications:
            return stats

        semaphore = asyncio.Semaphore(concurrency)
        quality_scores = []

        async def process_one(app):
            async with semaphore:
                return await self.enrich_application(app.id)

        # Process concurrently
        tasks = [process_one(app) for app in applications]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, Exception):
                stats["failed"] += 1
                logger.error(f"Batch enrichment error: {result}")
            elif isinstance(result, EnrichmentResult):
                if result.errors:
                    stats["failed"] += 1
                else:
                    stats["successful"] += 1

                if result.geocoding:
                    stats["geocoded"] += 1
                if result.property_data:
                    stats["property_enriched"] += 1

                quality_scores.append(result.quality_score)

        if quality_scores:
            stats["average_quality_score"] = sum(quality_scores) / len(quality_scores)

        return stats
