"""
Enumeration types for standardized DA categories and statuses.
"""

from enum import Enum


class ApplicationType(str, Enum):
    """Type of planning application."""

    DEVELOPMENT_APPLICATION = "development_application"
    COMPLYING_DEVELOPMENT = "complying_development"
    CONSTRUCTION_CERTIFICATE = "construction_certificate"
    SUBDIVISION = "subdivision"
    MODIFICATION = "modification"
    REVIEW = "review"
    SECTION_96 = "section_96"  # NSW modification type
    SECTION_4_55 = "section_4_55"  # NSW modification type
    REZONING = "rezoning"
    OTHER = "other"


class ApplicationCategory(str, Enum):
    """Category of development being proposed."""

    # Residential
    RESIDENTIAL_SINGLE = "residential_single"  # Single dwelling house
    RESIDENTIAL_DUAL = "residential_dual"  # Dual occupancy
    RESIDENTIAL_MULTI = "residential_multi"  # Units, apartments, townhouses
    RESIDENTIAL_ALTERATION = "residential_alteration"  # Alterations & additions
    RESIDENTIAL_ANCILLARY = "residential_ancillary"  # Granny flat, shed, pool
    RESIDENTIAL_SUBDIVISION = "residential_subdivision"  # Land division

    # Commercial
    COMMERCIAL_RETAIL = "commercial_retail"  # Shops, restaurants, cafes
    COMMERCIAL_OFFICE = "commercial_office"  # Office buildings
    COMMERCIAL_HOTEL = "commercial_hotel"  # Hotels, motels, serviced apartments

    # Industrial
    INDUSTRIAL_WAREHOUSE = "industrial_warehouse"  # Warehouses, storage
    INDUSTRIAL_MANUFACTURING = "industrial_manufacturing"  # Factories
    INDUSTRIAL_LIGHT = "industrial_light"  # Light industrial

    # Mixed Use
    MIXED_USE = "mixed_use"  # Combined residential/commercial

    # Infrastructure
    INFRASTRUCTURE_ROAD = "infrastructure_road"  # Roads, paths
    INFRASTRUCTURE_UTILITY = "infrastructure_utility"  # Power, water, sewer
    INFRASTRUCTURE_COMMUNITY = "infrastructure_community"  # Schools, hospitals

    # Other
    DEMOLITION = "demolition"
    CHANGE_OF_USE = "change_of_use"
    SIGNAGE = "signage"
    TREE_REMOVAL = "tree_removal"
    STRATA_SUBDIVISION = "strata_subdivision"
    EARTHWORKS = "earthworks"
    TELECOMMUNICATIONS = "telecommunications"
    OTHER = "other"


class ApplicationStatus(str, Enum):
    """Current status of the application."""

    # Pre-decision statuses
    LODGED = "lodged"
    REGISTERED = "registered"
    PENDING = "pending"
    UNDER_ASSESSMENT = "under_assessment"
    ON_EXHIBITION = "on_exhibition"
    PUBLIC_NOTIFICATION = "public_notification"
    ADDITIONAL_INFO_REQUIRED = "additional_info_required"
    REFERRED = "referred"
    AWAITING_DECISION = "awaiting_decision"

    # Decision statuses
    DETERMINED = "determined"
    APPROVED = "approved"
    APPROVED_WITH_CONDITIONS = "approved_with_conditions"
    REFUSED = "refused"
    DEFERRED = "deferred"

    # Post-decision statuses
    WITHDRAWN = "withdrawn"
    LAPSED = "lapsed"
    CANCELLED = "cancelled"
    APPEALED = "appealed"
    APPEAL_IN_PROGRESS = "appeal_in_progress"
    APPEAL_DETERMINED = "appeal_determined"

    # Unknown
    UNKNOWN = "unknown"


class Decision(str, Enum):
    """Final decision on the application."""

    APPROVED = "approved"
    APPROVED_WITH_CONDITIONS = "approved_with_conditions"
    REFUSED = "refused"
    DEFERRED = "deferred"
    WITHDRAWN = "withdrawn"
    NOT_DETERMINED = "not_determined"


# =============================================================================
# Status Mapping Templates for Common Council Systems
# =============================================================================

NSW_EPLANNING_STATUS_MAP = {
    "Lodged": ApplicationStatus.LODGED,
    "Under Assessment": ApplicationStatus.UNDER_ASSESSMENT,
    "On Exhibition": ApplicationStatus.ON_EXHIBITION,
    "Additional Information Required": ApplicationStatus.ADDITIONAL_INFO_REQUIRED,
    "Determined": ApplicationStatus.DETERMINED,
    "Approved": ApplicationStatus.APPROVED,
    "Refused": ApplicationStatus.REFUSED,
    "Withdrawn": ApplicationStatus.WITHDRAWN,
}

VIC_SPEAR_STATUS_MAP = {
    "Registered": ApplicationStatus.REGISTERED,
    "Under Consideration": ApplicationStatus.UNDER_ASSESSMENT,
    "Advertising": ApplicationStatus.ON_EXHIBITION,
    "Further Information": ApplicationStatus.ADDITIONAL_INFO_REQUIRED,
    "Decided": ApplicationStatus.DETERMINED,
    "Permit Issued": ApplicationStatus.APPROVED,
    "Permit Refused": ApplicationStatus.REFUSED,
    "Withdrawn": ApplicationStatus.WITHDRAWN,
    "Lapsed": ApplicationStatus.LAPSED,
}

QLD_DEVELOPMENT_I_STATUS_MAP = {
    "Properly Made": ApplicationStatus.LODGED,
    "In Assessment": ApplicationStatus.UNDER_ASSESSMENT,
    "Information Request": ApplicationStatus.ADDITIONAL_INFO_REQUIRED,
    "Decision Made": ApplicationStatus.DETERMINED,
    "Approved": ApplicationStatus.APPROVED,
    "Refused": ApplicationStatus.REFUSED,
    "Withdrawn": ApplicationStatus.WITHDRAWN,
    "Lapsed": ApplicationStatus.LAPSED,
}

SA_PLAN_STATUS_MAP = {
    "Lodged": ApplicationStatus.LODGED,
    "Assessing": ApplicationStatus.UNDER_ASSESSMENT,
    "On Public Notification": ApplicationStatus.PUBLIC_NOTIFICATION,
    "Decision Pending": ApplicationStatus.AWAITING_DECISION,
    "Approved": ApplicationStatus.APPROVED,
    "Refused": ApplicationStatus.REFUSED,
    "Withdrawn": ApplicationStatus.WITHDRAWN,
}

# Category keywords for AI classification fallback
CATEGORY_KEYWORDS = {
    ApplicationCategory.RESIDENTIAL_SINGLE: [
        "dwelling", "house", "residence", "single storey", "two storey",
        "new dwelling", "dwelling house"
    ],
    ApplicationCategory.RESIDENTIAL_DUAL: [
        "dual occupancy", "duplex", "attached dwelling", "semi-detached"
    ],
    ApplicationCategory.RESIDENTIAL_MULTI: [
        "units", "apartments", "townhouses", "residential flat building",
        "multi-dwelling", "medium density", "high density", "multi unit"
    ],
    ApplicationCategory.RESIDENTIAL_ALTERATION: [
        "alterations", "additions", "extension", "renovation", "refurbishment"
    ],
    ApplicationCategory.RESIDENTIAL_ANCILLARY: [
        "granny flat", "secondary dwelling", "shed", "garage", "carport",
        "swimming pool", "pool", "deck", "pergola", "fence", "retaining wall"
    ],
    ApplicationCategory.RESIDENTIAL_SUBDIVISION: [
        "subdivision", "land division", "lot", "boundary adjustment",
        "torrens title"
    ],
    ApplicationCategory.COMMERCIAL_RETAIL: [
        "shop", "retail", "restaurant", "cafe", "food premises", "takeaway",
        "commercial premises", "shopping"
    ],
    ApplicationCategory.COMMERCIAL_OFFICE: [
        "office", "commercial building", "business premises"
    ],
    ApplicationCategory.COMMERCIAL_HOTEL: [
        "hotel", "motel", "serviced apartment", "tourist accommodation",
        "short term accommodation"
    ],
    ApplicationCategory.INDUSTRIAL_WAREHOUSE: [
        "warehouse", "storage", "distribution", "logistics"
    ],
    ApplicationCategory.INDUSTRIAL_MANUFACTURING: [
        "factory", "manufacturing", "industrial building"
    ],
    ApplicationCategory.MIXED_USE: [
        "mixed use", "mixed-use", "shop top housing", "residential above"
    ],
    ApplicationCategory.DEMOLITION: [
        "demolition", "demolish"
    ],
    ApplicationCategory.CHANGE_OF_USE: [
        "change of use", "use change"
    ],
    ApplicationCategory.SIGNAGE: [
        "sign", "signage", "advertising", "billboard"
    ],
    ApplicationCategory.TREE_REMOVAL: [
        "tree removal", "tree", "vegetation"
    ],
    ApplicationCategory.STRATA_SUBDIVISION: [
        "strata", "strata subdivision", "strata title"
    ],
}
