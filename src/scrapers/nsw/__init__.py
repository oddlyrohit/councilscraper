"""NSW Council Scrapers."""

from .eplanning import NSWEPlanningAdapter
from .sydney import SydneyCityAdapter

# List of NSW councils using ePlanning portal
EPLANNING_COUNCILS = [
    "BLACKTOWN", "CANTERBURY_BANKSTOWN", "CENTRAL_COAST", "PARRAMATTA",
    "NORTHERN_BEACHES", "CUMBERLAND", "SUTHERLAND", "LIVERPOOL", "PENRITH",
    "FAIRFIELD", "WOLLONGONG", "LAKE_MACQUARIE", "INNER_WEST", "THE_HILLS",
    "CAMPBELLTOWN_NSW", "BAYSIDE_NSW", "NEWCASTLE", "GEORGES_RIVER", "HORNSBY",
    "RANDWICK", "CAMDEN", "KU_RING_GAI", "SHOALHAVEN", "TWEED", "MAITLAND",
    "PORT_MACQUARIE", "BLUE_MOUNTAINS", "COFFS_HARBOUR", "SHELLHARBOUR",
    "WAGGA_WAGGA", "HAWKESBURY", "TAMWORTH", "QUEANBEYAN_PALERANG", "CESSNOCK",
    "PORT_STEPHENS", "DUBBO", "WOLLONDILLY", "WINGECARRIBEE", "ALBURY",
    "CLARENCE_VALLEY", "LISMORE", "BALLINA", "ORANGE", "BATHURST", "EUROBODALLA",
    "BYRON", "BEGA_VALLEY", "GOULBURN", "GRIFFITH", "SINGLETON", "RICHMOND_VALLEY",
    "KIAMA", "SNOWY_MONARO",
]


def register_adapters(registry) -> None:
    """Register NSW adapters with the registry."""
    from src.config.councils import PortalType

    # Register ePlanning portal adapter
    registry.register_portal_type(PortalType.EPLANNING_NSW, NSWEPlanningAdapter)

    # Register Sydney City specific adapter
    registry.register("SYDNEY", SydneyCityAdapter)


__all__ = [
    "NSWEPlanningAdapter",
    "SydneyCityAdapter",
    "EPLANNING_COUNCILS",
    "register_adapters",
]
