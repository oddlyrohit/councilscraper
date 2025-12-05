"""Northern Territory Council Scrapers."""

from .nt_planning import NTPlanningAdapter


def register_adapters(registry) -> None:
    """Register NT adapters with the registry."""
    # Register NT councils individually since they have custom portals
    registry.register("DARWIN", NTPlanningAdapter)
    registry.register("PALMERSTON", NTPlanningAdapter)
    registry.register("LITCHFIELD", NTPlanningAdapter)
    registry.register("ALICE_SPRINGS", NTPlanningAdapter)


__all__ = ["NTPlanningAdapter", "register_adapters"]
