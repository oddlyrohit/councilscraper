"""Western Australia Council Scrapers."""

from .plan_wa import WAPlanWAAdapter


def register_adapters(registry) -> None:
    """Register WA adapters with the registry."""
    from src.config.councils import PortalType

    registry.register_portal_type(PortalType.PLAN_WA, WAPlanWAAdapter)


__all__ = ["WAPlanWAAdapter", "register_adapters"]
