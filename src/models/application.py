"""Application database models."""

from datetime import date, datetime
from typing import Optional, TYPE_CHECKING
from uuid import UUID, uuid4

from geoalchemy2 import Geometry
from sqlalchemy import (
    String, Integer, Text, Date, DateTime, Numeric, ForeignKey, Index, func
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .council import Council


class Application(Base, TimestampMixin):
    """Development Application database model."""

    __tablename__ = "applications"

    # Primary key
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )

    # Council reference
    council_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("councils.id"), nullable=False, index=True
    )
    da_number: Mapped[str] = mapped_column(String(100), nullable=False)

    # Property information
    address: Mapped[str] = mapped_column(Text, nullable=False)
    suburb: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    postcode: Mapped[Optional[str]] = mapped_column(String(10), index=True)
    state: Mapped[Optional[str]] = mapped_column(String(3))
    lot_plan: Mapped[Optional[str]] = mapped_column(String(100))
    coordinates: Mapped[Optional[str]] = mapped_column(
        Geometry(geometry_type="POINT", srid=4326)
    )
    land_area_sqm: Mapped[Optional[float]] = mapped_column(Numeric(12, 2))

    # Application details
    application_type: Mapped[Optional[str]] = mapped_column(String(50))
    category: Mapped[Optional[str]] = mapped_column(String(50), index=True)
    subcategory: Mapped[Optional[str]] = mapped_column(String(100))
    description: Mapped[Optional[str]] = mapped_column(Text)

    # Status
    status: Mapped[Optional[str]] = mapped_column(String(50), index=True)
    decision: Mapped[Optional[str]] = mapped_column(String(50))
    decision_date: Mapped[Optional[date]] = mapped_column(Date)
    conditions_count: Mapped[Optional[int]] = mapped_column(Integer)

    # Key dates
    lodged_date: Mapped[Optional[date]] = mapped_column(Date, index=True)
    validated_date: Mapped[Optional[date]] = mapped_column(Date)
    exhibition_start: Mapped[Optional[date]] = mapped_column(Date)
    exhibition_end: Mapped[Optional[date]] = mapped_column(Date)
    determined_date: Mapped[Optional[date]] = mapped_column(Date)

    # Development details
    estimated_cost: Mapped[Optional[float]] = mapped_column(Numeric(15, 2))
    dwelling_count: Mapped[Optional[int]] = mapped_column(Integer)
    lot_count: Mapped[Optional[int]] = mapped_column(Integer)
    floor_area_sqm: Mapped[Optional[float]] = mapped_column(Numeric(12, 2))
    storeys: Mapped[Optional[int]] = mapped_column(Integer)
    car_spaces: Mapped[Optional[int]] = mapped_column(Integer)

    # Applicant
    applicant_name: Mapped[Optional[str]] = mapped_column(String(255))
    applicant_type: Mapped[Optional[str]] = mapped_column(String(50))
    owner_name: Mapped[Optional[str]] = mapped_column(String(255))

    # Metadata
    source_url: Mapped[Optional[str]] = mapped_column(Text)
    scraped_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    data_quality_score: Mapped[Optional[float]] = mapped_column(Numeric(3, 2))
    classification_confidence: Mapped[Optional[float]] = mapped_column(Numeric(3, 2))

    # Relationships
    council: Mapped["Council"] = relationship("Council", back_populates="applications")
    documents: Mapped[list["ApplicationDocument"]] = relationship(
        "ApplicationDocument", back_populates="application", cascade="all, delete-orphan"
    )

    # Indexes
    __table_args__ = (
        Index("idx_applications_council_da", "council_id", "da_number", unique=True),
        Index("idx_applications_lodged_brin", "lodged_date"),
        Index("idx_applications_geo", "coordinates", postgresql_using="gist"),
    )

    def __repr__(self) -> str:
        return f"<Application(da_number={self.da_number}, address={self.address[:50]}...)>"

    def to_dict(self) -> dict:
        """Convert to dictionary for API response."""
        return {
            "id": str(self.id),
            "da_number": self.da_number,
            "council_id": self.council_id,
            "address": self.address,
            "suburb": self.suburb,
            "postcode": self.postcode,
            "state": self.state,
            "lot_plan": self.lot_plan,
            "application_type": self.application_type,
            "category": self.category,
            "subcategory": self.subcategory,
            "description": self.description,
            "status": self.status,
            "decision": self.decision,
            "decision_date": self.decision_date.isoformat() if self.decision_date else None,
            "lodged_date": self.lodged_date.isoformat() if self.lodged_date else None,
            "exhibition_start": self.exhibition_start.isoformat() if self.exhibition_start else None,
            "exhibition_end": self.exhibition_end.isoformat() if self.exhibition_end else None,
            "determined_date": self.determined_date.isoformat() if self.determined_date else None,
            "estimated_cost": float(self.estimated_cost) if self.estimated_cost else None,
            "dwelling_count": self.dwelling_count,
            "lot_count": self.lot_count,
            "floor_area_sqm": float(self.floor_area_sqm) if self.floor_area_sqm else None,
            "storeys": self.storeys,
            "car_spaces": self.car_spaces,
            "applicant_name": self.applicant_name,
            "applicant_type": self.applicant_type,
            "source_url": self.source_url,
            "scraped_at": self.scraped_at.isoformat() if self.scraped_at else None,
            "data_quality_score": float(self.data_quality_score) if self.data_quality_score else None,
        }


class ApplicationDocument(Base, TimestampMixin):
    """Document associated with an application."""

    __tablename__ = "application_documents"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    application_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("applications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    url: Mapped[Optional[str]] = mapped_column(Text)
    doc_type: Mapped[Optional[str]] = mapped_column(String(50))
    uploaded_date: Mapped[Optional[date]] = mapped_column(Date)
    file_size_kb: Mapped[Optional[int]] = mapped_column(Integer)

    # Relationship
    application: Mapped["Application"] = relationship(
        "Application", back_populates="documents"
    )

    def __repr__(self) -> str:
        return f"<ApplicationDocument(name={self.name[:50]}...)>"

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "name": self.name,
            "url": self.url,
            "doc_type": self.doc_type,
            "uploaded_date": self.uploaded_date.isoformat() if self.uploaded_date else None,
        }
