"""Queensland Council Scrapers."""

from .development_i import QLDDevelopmentIAdapter
from .brisbane import BrisbaneCityAdapter


def register_adapters(registry) -> None:
    """Register QLD adapters with the registry."""
    from src.config.councils import PortalType

    # Register Development.i portal adapter (covers most QLD councils)
    registry.register_portal_type(PortalType.DEVELOPMENT_I_QLD, QLDDevelopmentIAdapter)

    # Register Brisbane City specific adapter
    registry.register("BRISBANE", BrisbaneCityAdapter)


__all__ = [
    "QLDDevelopmentIAdapter",
    "BrisbaneCityAdapter",
    "register_adapters",
]
