"""Victoria Council Scrapers."""

from .spear import VICSPEARAdapter
from .melbourne import MelbourneCityAdapter


def register_adapters(registry) -> None:
    """Register VIC adapters with the registry."""
    from src.config.councils import PortalType

    # Register SPEAR portal adapter (covers most VIC councils)
    registry.register_portal_type(PortalType.SPEAR_VIC, VICSPEARAdapter)

    # Register Melbourne City specific adapter
    registry.register("MELBOURNE", MelbourneCityAdapter)


__all__ = [
    "VICSPEARAdapter",
    "MelbourneCityAdapter",
    "register_adapters",
]
