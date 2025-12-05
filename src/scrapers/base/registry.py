"""
Scraper Registry
Central registry for all council scrapers.
"""

from typing import Optional, Type
import logging
import importlib

from src.config.councils import (
    CouncilConfig,
    PortalType,
    ALL_COUNCILS,
    get_council_by_code,
)
from .adapter import CouncilAdapter


logger = logging.getLogger(__name__)


class ScraperRegistry:
    """
    Central registry that maps councils to their scrapers.
    Handles automatic scraper discovery and instantiation.
    """

    def __init__(self):
        """Initialize the registry."""
        self._adapters: dict[str, Type[CouncilAdapter]] = {}
        self._portal_adapters: dict[PortalType, Type[CouncilAdapter]] = {}
        self._instances: dict[str, CouncilAdapter] = {}

    def register(
        self,
        council_code: str,
        adapter_class: Type[CouncilAdapter],
    ) -> None:
        """
        Register a scraper for a specific council.

        Args:
            council_code: Council code
            adapter_class: Adapter class
        """
        self._adapters[council_code] = adapter_class
        logger.debug(f"Registered adapter for {council_code}: {adapter_class.__name__}")

    def register_portal_type(
        self,
        portal_type: PortalType,
        adapter_class: Type[CouncilAdapter],
    ) -> None:
        """
        Register a scraper for a portal type (handles multiple councils).

        Args:
            portal_type: Portal type enum
            adapter_class: Adapter class
        """
        self._portal_adapters[portal_type] = adapter_class
        logger.debug(f"Registered portal adapter for {portal_type}: {adapter_class.__name__}")

    def get_adapter(self, council_code: str) -> Optional[CouncilAdapter]:
        """
        Get a scraper instance for a council.

        Args:
            council_code: Council code

        Returns:
            Adapter instance or None
        """
        # Return cached instance if exists
        if council_code in self._instances:
            return self._instances[council_code]

        # Get council config
        council_config = get_council_by_code(council_code)
        if not council_config:
            logger.warning(f"Unknown council code: {council_code}")
            return None

        # Try council-specific adapter first
        if council_code in self._adapters:
            adapter_class = self._adapters[council_code]
            instance = adapter_class(council_config)
            self._instances[council_code] = instance
            return instance

        # Try portal type adapter
        if council_config.portal_type and council_config.portal_type in self._portal_adapters:
            adapter_class = self._portal_adapters[council_config.portal_type]
            instance = adapter_class(council_config)
            self._instances[council_code] = instance
            return instance

        logger.warning(f"No adapter found for {council_code}")
        return None

    def get_adapter_class(
        self,
        council_code: str,
    ) -> Optional[Type[CouncilAdapter]]:
        """
        Get the adapter class for a council (without instantiation).

        Args:
            council_code: Council code

        Returns:
            Adapter class or None
        """
        if council_code in self._adapters:
            return self._adapters[council_code]

        council_config = get_council_by_code(council_code)
        if council_config and council_config.portal_type:
            return self._portal_adapters.get(council_config.portal_type)

        return None

    def has_adapter(self, council_code: str) -> bool:
        """Check if an adapter exists for a council."""
        return self.get_adapter_class(council_code) is not None

    def get_all_councils(self) -> list[CouncilConfig]:
        """Get all registered councils."""
        return ALL_COUNCILS

    def get_councils_by_tier(self, tier: int) -> list[CouncilConfig]:
        """Get councils by tier."""
        return [c for c in ALL_COUNCILS if c.tier == tier]

    def get_councils_with_adapters(self) -> list[CouncilConfig]:
        """Get councils that have adapters registered."""
        return [c for c in ALL_COUNCILS if self.has_adapter(c.code)]

    def get_councils_without_adapters(self) -> list[CouncilConfig]:
        """Get councils that don't have adapters yet."""
        return [c for c in ALL_COUNCILS if not self.has_adapter(c.code)]

    def get_portal_stats(self) -> dict:
        """Get statistics about registered adapters."""
        stats = {
            "total_councils": len(ALL_COUNCILS),
            "councils_with_adapters": 0,
            "by_portal_type": {},
        }

        for portal_type in PortalType:
            councils = [c for c in ALL_COUNCILS if c.portal_type == portal_type]
            has_adapter = portal_type in self._portal_adapters
            stats["by_portal_type"][portal_type.value] = {
                "councils": len(councils),
                "has_adapter": has_adapter,
            }
            if has_adapter:
                stats["councils_with_adapters"] += len(councils)

        # Add council-specific adapters
        for code in self._adapters:
            if code not in [c.code for c in self.get_councils_with_adapters()]:
                stats["councils_with_adapters"] += 1

        return stats

    def discover_adapters(self) -> None:
        """
        Automatically discover and register adapters from the scrapers package.
        """
        # Import state-specific modules
        state_modules = [
            "src.scrapers.nsw",
            "src.scrapers.vic",
            "src.scrapers.qld",
            "src.scrapers.sa",
            "src.scrapers.wa",
            "src.scrapers.tas",
            "src.scrapers.nt",
        ]

        for module_name in state_modules:
            try:
                module = importlib.import_module(module_name)

                # Look for register function
                if hasattr(module, "register_adapters"):
                    module.register_adapters(self)
                    logger.info(f"Registered adapters from {module_name}")

            except ImportError as e:
                logger.debug(f"Could not import {module_name}: {e}")
            except Exception as e:
                logger.error(f"Error registering adapters from {module_name}: {e}")


# Global registry instance
_registry: Optional[ScraperRegistry] = None


def get_registry() -> ScraperRegistry:
    """Get the global scraper registry."""
    global _registry
    if _registry is None:
        _registry = ScraperRegistry()
        _registry.discover_adapters()
    return _registry
