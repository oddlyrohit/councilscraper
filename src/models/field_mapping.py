"""Field mapping database model."""

from datetime import datetime
from typing import Optional

from sqlalchemy import String, Integer, DateTime, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class FieldMappingModel(Base):
    """AI-learned field mappings for councils."""

    __tablename__ = "field_mappings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    council_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("councils.id"), unique=True, nullable=False
    )
    mapping: Mapped[dict] = mapped_column(JSONB, nullable=False)
    status_values: Mapped[Optional[dict]] = mapped_column(JSONB)
    sample_count: Mapped[int] = mapped_column(Integer, default=0)
    confidence: Mapped[Optional[float]] = mapped_column(Numeric(3, 2))
    learned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    def __repr__(self) -> str:
        return f"<FieldMappingModel(council_id={self.council_id})>"

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "council_id": self.council_id,
            "mapping": self.mapping,
            "status_values": self.status_values,
            "sample_count": self.sample_count,
            "confidence": float(self.confidence) if self.confidence else None,
            "learned_at": self.learned_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
