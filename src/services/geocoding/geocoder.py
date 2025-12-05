"""Geocoding service with multiple provider support."""

import asyncio
import hashlib
import json
import logging
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional

import httpx

from src.config.settings import get_settings


logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class GeocodingResult:
    """Result from geocoding an address."""

    latitude: float
    longitude: float
    confidence: float  # 0.0 to 1.0
    formatted_address: Optional[str] = None
    suburb: Optional[str] = None
    postcode: Optional[str] = None
    state: Optional[str] = None
    lga: Optional[str] = None
    provider: str = "unknown"
    raw_response: Optional[dict] = None


@dataclass
class GeocodingCache:
    """In-memory cache for geocoding results."""

    _cache: dict = field(default_factory=dict)
    _timestamps: dict = field(default_factory=dict)
    _ttl_hours: int = 168  # 1 week

    def _hash_address(self, address: str) -> str:
        """Create consistent hash for address."""
        normalized = address.lower().strip()
        normalized = re.sub(r'\s+', ' ', normalized)
        return hashlib.md5(normalized.encode()).hexdigest()

    def get(self, address: str) -> Optional[GeocodingResult]:
        """Get cached result if not expired."""
        key = self._hash_address(address)
        if key in self._cache:
            timestamp = self._timestamps.get(key)
            if timestamp and datetime.utcnow() - timestamp < timedelta(hours=self._ttl_hours):
                return self._cache[key]
            else:
                del self._cache[key]
                del self._timestamps[key]
        return None

    def set(self, address: str, result: GeocodingResult) -> None:
        """Cache a geocoding result."""
        key = self._hash_address(address)
        self._cache[key] = result
        self._timestamps[key] = datetime.utcnow()


class GeocodingProvider(ABC):
    """Abstract base class for geocoding providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name."""
        pass

    @abstractmethod
    async def geocode(self, address: str) -> Optional[GeocodingResult]:
        """Geocode an address."""
        pass


class GoogleGeocodingProvider(GeocodingProvider):
    """Google Maps Geocoding API provider."""

    name = "google"
    BASE_URL = "https://maps.googleapis.com/maps/api/geocode/json"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = httpx.AsyncClient(timeout=10.0)

    async def geocode(self, address: str) -> Optional[GeocodingResult]:
        """Geocode using Google Maps API."""
        try:
            # Ensure Australian context
            full_address = address
            if "australia" not in address.lower():
                full_address = f"{address}, Australia"

            params = {
                "address": full_address,
                "key": self.api_key,
                "region": "au",
                "components": "country:AU",
            }

            response = await self.client.get(self.BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()

            if data["status"] != "OK" or not data["results"]:
                return None

            result = data["results"][0]
            location = result["geometry"]["location"]

            # Extract address components
            components = {c["types"][0]: c for c in result["address_components"]}

            # Determine confidence based on location type
            confidence_map = {
                "ROOFTOP": 1.0,
                "RANGE_INTERPOLATED": 0.8,
                "GEOMETRIC_CENTER": 0.6,
                "APPROXIMATE": 0.4,
            }
            location_type = result["geometry"].get("location_type", "APPROXIMATE")
            confidence = confidence_map.get(location_type, 0.4)

            return GeocodingResult(
                latitude=location["lat"],
                longitude=location["lng"],
                confidence=confidence,
                formatted_address=result.get("formatted_address"),
                suburb=components.get("locality", {}).get("long_name"),
                postcode=components.get("postal_code", {}).get("long_name"),
                state=components.get("administrative_area_level_1", {}).get("short_name"),
                lga=components.get("administrative_area_level_2", {}).get("long_name"),
                provider=self.name,
                raw_response=result,
            )

        except Exception as e:
            logger.error(f"Google geocoding error for '{address}': {e}")
            return None


class NominatimGeocodingProvider(GeocodingProvider):
    """OpenStreetMap Nominatim geocoding provider (free, rate-limited)."""

    name = "nominatim"
    BASE_URL = "https://nominatim.openstreetmap.org/search"

    def __init__(self, user_agent: str = "CouncilDataScraper/1.0"):
        self.user_agent = user_agent
        self.client = httpx.AsyncClient(
            timeout=10.0,
            headers={"User-Agent": user_agent}
        )
        self._last_request = datetime.min
        self._rate_limit_delay = 1.0  # 1 second between requests

    async def geocode(self, address: str) -> Optional[GeocodingResult]:
        """Geocode using Nominatim API."""
        try:
            # Rate limiting
            elapsed = (datetime.utcnow() - self._last_request).total_seconds()
            if elapsed < self._rate_limit_delay:
                await asyncio.sleep(self._rate_limit_delay - elapsed)

            # Ensure Australian context
            full_address = address
            if "australia" not in address.lower():
                full_address = f"{address}, Australia"

            params = {
                "q": full_address,
                "format": "json",
                "countrycodes": "au",
                "addressdetails": 1,
                "limit": 1,
            }

            response = await self.client.get(self.BASE_URL, params=params)
            self._last_request = datetime.utcnow()
            response.raise_for_status()
            data = response.json()

            if not data:
                return None

            result = data[0]
            address_parts = result.get("address", {})

            # Determine confidence based on result type
            result_type = result.get("type", "")
            if result_type in ["house", "building"]:
                confidence = 0.9
            elif result_type in ["street", "road"]:
                confidence = 0.7
            elif result_type in ["suburb", "city"]:
                confidence = 0.5
            else:
                confidence = 0.4

            return GeocodingResult(
                latitude=float(result["lat"]),
                longitude=float(result["lon"]),
                confidence=confidence,
                formatted_address=result.get("display_name"),
                suburb=address_parts.get("suburb") or address_parts.get("city"),
                postcode=address_parts.get("postcode"),
                state=address_parts.get("state"),
                lga=address_parts.get("county"),
                provider=self.name,
                raw_response=result,
            )

        except Exception as e:
            logger.error(f"Nominatim geocoding error for '{address}': {e}")
            return None


class GNAFGeocodingProvider(GeocodingProvider):
    """GNAF (Geocoded National Address File) provider for high-accuracy AU addresses."""

    name = "gnaf"
    # This would typically use a GNAF API or local database
    BASE_URL = "https://api.psma.com.au/v1/addresses"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.client = httpx.AsyncClient(timeout=10.0)

    async def geocode(self, address: str) -> Optional[GeocodingResult]:
        """Geocode using GNAF API."""
        if not self.api_key:
            logger.debug("GNAF API key not configured, skipping")
            return None

        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            params = {"address": address}

            response = await self.client.get(
                f"{self.BASE_URL}/search",
                headers=headers,
                params=params
            )
            response.raise_for_status()
            data = response.json()

            if not data.get("results"):
                return None

            result = data["results"][0]

            return GeocodingResult(
                latitude=result["latitude"],
                longitude=result["longitude"],
                confidence=result.get("confidence", 0.95),
                formatted_address=result.get("formattedAddress"),
                suburb=result.get("suburb"),
                postcode=result.get("postcode"),
                state=result.get("state"),
                lga=result.get("lga"),
                provider=self.name,
                raw_response=result,
            )

        except Exception as e:
            logger.error(f"GNAF geocoding error for '{address}': {e}")
            return None


class Geocoder:
    """
    Main geocoding service with provider fallback and caching.

    Uses multiple providers in order of preference:
    1. GNAF (highest accuracy for Australian addresses)
    2. Google Maps (high accuracy, paid)
    3. Nominatim (free, rate-limited)
    """

    def __init__(
        self,
        google_api_key: Optional[str] = None,
        gnaf_api_key: Optional[str] = None,
        enable_cache: bool = True,
    ):
        self.providers: list[GeocodingProvider] = []
        self.cache = GeocodingCache() if enable_cache else None

        # Initialize providers in order of preference
        if gnaf_api_key:
            self.providers.append(GNAFGeocodingProvider(gnaf_api_key))

        if google_api_key:
            self.providers.append(GoogleGeocodingProvider(google_api_key))

        # Always include free Nominatim as fallback
        self.providers.append(NominatimGeocodingProvider())

        logger.info(f"Geocoder initialized with providers: {[p.name for p in self.providers]}")

    def _normalize_address(self, address: str, suburb: Optional[str] = None,
                          postcode: Optional[str] = None, state: Optional[str] = None) -> str:
        """Build a complete address string for geocoding."""
        parts = [address]

        if suburb and suburb.lower() not in address.lower():
            parts.append(suburb)

        if state and state.upper() not in address.upper():
            parts.append(state)

        if postcode and postcode not in address:
            parts.append(postcode)

        return ", ".join(parts)

    async def geocode(
        self,
        address: str,
        suburb: Optional[str] = None,
        postcode: Optional[str] = None,
        state: Optional[str] = None,
        min_confidence: float = 0.5,
    ) -> Optional[GeocodingResult]:
        """
        Geocode an address using available providers.

        Args:
            address: Street address
            suburb: Suburb/locality name
            postcode: Postal code
            state: State abbreviation (NSW, VIC, etc.)
            min_confidence: Minimum confidence threshold

        Returns:
            GeocodingResult if successful and above threshold, None otherwise
        """
        full_address = self._normalize_address(address, suburb, postcode, state)

        # Check cache first
        if self.cache:
            cached = self.cache.get(full_address)
            if cached:
                logger.debug(f"Cache hit for '{full_address}'")
                return cached

        # Try each provider in order
        for provider in self.providers:
            try:
                result = await provider.geocode(full_address)

                if result and result.confidence >= min_confidence:
                    # Cache successful result
                    if self.cache:
                        self.cache.set(full_address, result)

                    logger.info(
                        f"Geocoded '{full_address}' via {provider.name} "
                        f"(confidence: {result.confidence:.2f})"
                    )
                    return result

            except Exception as e:
                logger.warning(f"Provider {provider.name} failed: {e}")
                continue

        logger.warning(f"Failed to geocode '{full_address}' with any provider")
        return None

    async def reverse_geocode(
        self, latitude: float, longitude: float
    ) -> Optional[GeocodingResult]:
        """Reverse geocode coordinates to an address."""
        # Implementation would depend on provider support
        # For now, return None as placeholder
        return None
