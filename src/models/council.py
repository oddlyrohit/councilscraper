"""Council database model."""

from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .application import Application
    from .scrape_log import ScrapeLog


class Council(Base, TimestampMixin):
    """Council/LGA database model."""

    __tablename__ = "councils"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    state: Mapped[str] = mapped_column(String(3), nullable=False, index=True)
    lga_code: Mapped[Optional[str]] = mapped_column(String(10))
    population: Mapped[Optional[int]] = mapped_column(Integer)
    tier: Mapped[int] = mapped_column(Integer, default=4, index=True)
    portal_url: Mapped[Optional[str]] = mapped_column(Text)
    portal_type: Mapped[Optional[str]] = mapped_column(String(50))
    scraper_class: Mapped[Optional[str]] = mapped_column(String(100))
    scraper_status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    last_scraped_at: Mapped[Optional[str]] = mapped_column(String(50))
    metro_area: Mapped[Optional[str]] = mapped_column(String(100))
    notes: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    applications: Mapped[list["Application"]] = relationship(
        "Application", back_populates="council", lazy="dynamic"
    )
    scrape_logs: Mapped[list["ScrapeLog"]] = relationship(
        "ScrapeLog", back_populates="council", lazy="dynamic"
    )

    def __repr__(self) -> str:
        return f"<Council(code={self.code}, name={self.name}, state={self.state})>"

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "state": self.state,
            "lga_code": self.lga_code,
            "population": self.population,
            "tier": self.tier,
            "portal_url": self.portal_url,
            "portal_type": self.portal_type,
            "scraper_status": self.scraper_status,
            "metro_area": self.metro_area,
        }
