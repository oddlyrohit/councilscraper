"""
Master Schema Definitions for Development Applications.
These are the unified data models that all council data maps to.
"""

from datetime import date, datetime
from typing import Optional, Any
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, field_validator

from .enums import ApplicationType, ApplicationCategory, ApplicationStatus, Decision


class CouncilInfo(BaseModel):
    """Council/LGA information."""

    code: str = Field(..., description="Unique council identifier (e.g., 'BRISBANE')")
    name: str = Field(..., description="Full council name")
    state: str = Field(..., description="State abbreviation (e.g., 'QLD')")
    lga_code: Optional[str] = Field(None, description="ABS LGA code")
    portal_url: Optional[str] = Field(None, description="Planning portal URL")
    portal_type: Optional[str] = Field(None, description="Portal system type")


class PropertyInfo(BaseModel):
    """Property/site information."""

    address: str = Field(..., description="Full street address")
    suburb: Optional[str] = Field(None, description="Suburb name")
    postcode: Optional[str] = Field(None, description="4-digit postcode")
    state: Optional[str] = Field(None, description="State abbreviation")
    lot_plan: Optional[str] = Field(None, description="Lot/Plan reference")
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    land_area_sqm: Optional[float] = Field(None, ge=0)

    @field_validator("postcode")
    @classmethod
    def validate_postcode(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if v and len(v) != 4:
                return None
        return v


class ApplicationDates(BaseModel):
    """Key dates in the application lifecycle."""

    lodged: Optional[date] = Field(None, description="Date application was lodged")
    validated: Optional[date] = Field(None, description="Date application was validated")
    exhibition_start: Optional[date] = Field(None, description="Public exhibition start")
    exhibition_end: Optional[date] = Field(None, description="Public exhibition end")
    determined: Optional[date] = Field(None, description="Date of determination")
    approved: Optional[date] = Field(None, description="Date of approval (if approved)")
    commenced: Optional[date] = Field(None, description="Date work commenced")
    completed: Optional[date] = Field(None, description="Date work completed")


class ApplicantInfo(BaseModel):
    """Applicant/owner details."""

    applicant_name: Optional[str] = Field(None, description="Name of applicant")
    applicant_type: Optional[str] = Field(
        None, description="Type: individual, company, government"
    )
    owner_name: Optional[str] = Field(None, description="Property owner name")
    architect: Optional[str] = Field(None, description="Architect/designer")
    builder: Optional[str] = Field(None, description="Builder")
    consultant: Optional[str] = Field(None, description="Planning consultant")


class DevelopmentDetails(BaseModel):
    """Details of proposed development."""

    estimated_cost: Optional[float] = Field(None, ge=0, description="Estimated cost in AUD")
    dwelling_count: Optional[int] = Field(None, ge=0, description="Number of dwellings")
    lot_count: Optional[int] = Field(None, ge=0, description="Number of lots (subdivisions)")
    floor_area_sqm: Optional[float] = Field(None, ge=0, description="Total floor area")
    storeys: Optional[int] = Field(None, ge=0, description="Number of storeys")
    car_spaces: Optional[int] = Field(None, ge=0, description="Parking spaces")
    bedrooms: Optional[int] = Field(None, ge=0, description="Total bedrooms")


class Document(BaseModel):
    """Associated document."""

    name: str = Field(..., description="Document name/title")
    url: Optional[str] = Field(None, description="Document URL")
    doc_type: Optional[str] = Field(None, description="Document type (plans, statement, etc.)")
    uploaded_date: Optional[date] = Field(None, description="Date uploaded")
    file_size_kb: Optional[int] = Field(None, description="File size in KB")


class DevelopmentApplication(BaseModel):
    """
    Unified Development Application record.
    This is the master schema that all council data maps to.
    """

    # Identifiers
    id: UUID = Field(default_factory=uuid4, description="Internal UUID")
    da_number: str = Field(..., description="Council's DA reference number")
    council: CouncilInfo

    # Property
    property: PropertyInfo

    # Application details
    application_type: ApplicationType = Field(default=ApplicationType.OTHER)
    category: ApplicationCategory = Field(default=ApplicationCategory.OTHER)
    subcategory: Optional[str] = Field(None, description="More specific category")
    description: str = Field(..., description="Full description of proposed works")

    # Status
    status: ApplicationStatus = Field(default=ApplicationStatus.UNKNOWN)
    decision: Optional[Decision] = Field(None, description="Final decision")
    decision_date: Optional[date] = Field(None)
    conditions_count: Optional[int] = Field(None, ge=0)

    # Dates
    dates: ApplicationDates = Field(default_factory=ApplicationDates)

    # Parties
    applicant: ApplicantInfo = Field(default_factory=ApplicantInfo)

    # Development details
    details: DevelopmentDetails = Field(default_factory=DevelopmentDetails)

    # Documents
    documents: list[Document] = Field(default_factory=list)

    # Metadata
    source_url: Optional[str] = Field(None, description="URL where data was scraped")
    scraped_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    data_quality_score: float = Field(default=0.0, ge=0.0, le=1.0)
    classification_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)

    def to_api_dict(self) -> dict:
        """Convert to API response format."""
        return {
            "id": str(self.id),
            "da_number": self.da_number,
            "council": {
                "code": self.council.code,
                "name": self.council.name,
                "state": self.council.state,
            },
            "property": {
                "address": self.property.address,
                "suburb": self.property.suburb,
                "postcode": self.property.postcode,
                "state": self.property.state,
                "lot_plan": self.property.lot_plan,
                "coordinates": (
                    {"lat": self.property.latitude, "lng": self.property.longitude}
                    if self.property.latitude
                    else None
                ),
                "land_area_sqm": self.property.land_area_sqm,
            },
            "application": {
                "type": self.application_type.value,
                "category": self.category.value,
                "subcategory": self.subcategory,
                "description": self.description,
            },
            "status": self.status.value,
            "decision": self.decision.value if self.decision else None,
            "dates": {
                "lodged": self.dates.lodged.isoformat() if self.dates.lodged else None,
                "exhibition_start": (
                    self.dates.exhibition_start.isoformat()
                    if self.dates.exhibition_start
                    else None
                ),
                "exhibition_end": (
                    self.dates.exhibition_end.isoformat() if self.dates.exhibition_end else None
                ),
                "determined": self.dates.determined.isoformat() if self.dates.determined else None,
            },
            "applicant": {
                "name": self.applicant.applicant_name,
                "type": self.applicant.applicant_type,
            },
            "details": {
                "estimated_cost": self.details.estimated_cost,
                "dwelling_count": self.details.dwelling_count,
                "lot_count": self.details.lot_count,
                "floor_area_sqm": self.details.floor_area_sqm,
                "storeys": self.details.storeys,
                "car_spaces": self.details.car_spaces,
            },
            "documents": [
                {"name": d.name, "url": d.url, "type": d.doc_type} for d in self.documents
            ],
            "metadata": {
                "source_url": self.source_url,
                "scraped_at": self.scraped_at.isoformat(),
                "updated_at": self.updated_at.isoformat(),
                "data_quality_score": self.data_quality_score,
            },
        }


class RawDARecord(BaseModel):
    """
    Raw DA record as scraped from a council portal.
    Contains unprocessed data before field mapping.
    """

    council_code: str = Field(..., description="Council identifier")
    raw_data: dict[str, Any] = Field(..., description="Raw scraped data")
    source_url: str = Field(..., description="URL scraped from")
    scraped_at: datetime = Field(default_factory=datetime.utcnow)

    # Optional pre-parsed fields (if scraper can extract them directly)
    da_number: Optional[str] = None
    address: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    lodged_date: Optional[str] = None
    estimated_cost: Optional[str] = None

    class Config:
        extra = "allow"


class ClassificationResult(BaseModel):
    """Result from AI category classification."""

    category: ApplicationCategory
    subcategory: Optional[str] = None
    application_type: Optional[ApplicationType] = None
    dwelling_count: Optional[int] = None
    lot_count: Optional[int] = None
    storeys: Optional[int] = None
    is_new_build: Optional[bool] = None
    involves_demolition: Optional[bool] = None
    confidence: float = Field(ge=0.0, le=1.0)


class FieldMapping(BaseModel):
    """Learned field mapping for a council."""

    council_code: str
    mapping: dict[str, Optional[str]]  # master_field -> council_field
    status_values: dict[str, str]  # council_status -> normalized_status
    learned_at: datetime = Field(default_factory=datetime.utcnow)
    sample_count: int = 0
    confidence: float = 0.0


class ScrapeResult(BaseModel):
    """Result of a scraping operation."""

    council_code: str
    mode: str = Field(description="'active' or 'historical'")
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: str = "pending"  # pending, success, failed
    records_scraped: int = 0
    records_processed: int = 0
    errors: list[str] = Field(default_factory=list)
    batch_id: Optional[str] = None
