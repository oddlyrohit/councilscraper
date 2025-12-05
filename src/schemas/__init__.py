"""Schema definitions for the Council DA Scraper."""

from .enums import (
    ApplicationType,
    ApplicationCategory,
    ApplicationStatus,
    Decision,
)
from .master import (
    CouncilInfo,
    PropertyInfo,
    ApplicationDates,
    ApplicantInfo,
    DevelopmentDetails,
    Document,
    DevelopmentApplication,
    RawDARecord,
)

__all__ = [
    "ApplicationType",
    "ApplicationCategory",
    "ApplicationStatus",
    "Decision",
    "CouncilInfo",
    "PropertyInfo",
    "ApplicationDates",
    "ApplicantInfo",
    "DevelopmentDetails",
    "Document",
    "DevelopmentApplication",
    "RawDARecord",
]
