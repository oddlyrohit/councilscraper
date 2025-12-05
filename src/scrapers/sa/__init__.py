"""South Australia Council Scrapers."""

from .plan_sa import SAPlanSAAdapter


def register_adapters(registry) -> None:
    """Register SA adapters with the registry."""
    from src.config.councils import PortalType

    # Register PlanSA portal adapter (covers all SA councils)
    registry.register_portal_type(PortalType.PLAN_SA, SAPlanSAAdapter)


__all__ = [
    "SAPlanSAAdapter",
    "register_adapters",
]
