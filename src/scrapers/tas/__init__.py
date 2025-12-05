"""Tasmania Council Scrapers."""

from .epathway import TASEPathwayAdapter


def register_adapters(registry) -> None:
    """Register TAS adapters with the registry."""
    from src.config.councils import PortalType

    registry.register_portal_type(PortalType.EPATHWAY, TASEPathwayAdapter)


__all__ = ["TASEPathwayAdapter", "register_adapters"]
