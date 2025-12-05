"""GNAF geocoding via Supabase - queries your existing GNAF dataset."""

import logging
import re
from typing import Optional

import httpx

from src.config.settings import get_settings
from src.services.geocoding.geocoder import GeocodingProvider, GeocodingResult


logger = logging.getLogger(__name__)
settings = get_settings()


class SupabaseGNAFProvider(GeocodingProvider):
    """
    Geocoding provider using GNAF data stored in Supabase.

    GNAF (Geocoded National Address File) is Australia's authoritative
    address database with 15+ million addresses and precise coordinates.

    Your Supabase schema (gnaf.address_principals):
        - address_detail_pid (text, PK)
        - building_name (text)
        - lot_number_prefix, lot_number, lot_number_suffix (text)
        - flat_type_code, flat_number_prefix, flat_number (int), flat_number_suffix
        - level_type_code, level_number_prefix, level_number (int), level_number_suffix
        - number_first_prefix, number_first (int), number_first_suffix
        - number_last_prefix, number_last (int), number_last_suffix
        - street_locality_pid, street_name, street_type_code
        - locality_pid, locality_name (text) - suburb
        - state (text) - NSW, VIC, etc.
        - postcode (text)
        - latitude, longitude (numeric)
        - geocode_type (text)
        - confidence (int) - GNAF confidence 0-2
        - full_address (text) - pre-computed full address string
        - location (geography) - PostGIS point
    """

    name = "gnaf_supabase"

    def __init__(
        self,
        supabase_url: Optional[str] = None,
        supabase_key: Optional[str] = None,
        table_name: str = "address_principals",
        schema: str = "gnaf",
    ):
        self.supabase_url = supabase_url or settings.supabase_url
        self.supabase_key = supabase_key or settings.supabase_anon_key
        self.table_name = table_name
        self.schema = schema

        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Supabase URL and key are required for GNAF geocoding")

        self.client = httpx.AsyncClient(
            timeout=15.0,
            headers={
                "apikey": self.supabase_key,
                "Authorization": f"Bearer {self.supabase_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
        )
        # Use schema-qualified table name
        self.rest_url = f"{self.supabase_url}/rest/v1/{self.table_name}"

    def _parse_address(self, address: str) -> dict:
        """
        Parse address string into components for GNAF matching.

        Examples:
            "123 Main Street, Sydney NSW 2000"
            "Unit 5/42 George St, Parramatta"
            "15A Smith Road, Melbourne VIC"
        """
        parsed = {
            "flat_number": None,
            "street_number": None,
            "street_name": None,
            "street_type": None,
            "suburb": None,
            "state": None,
            "postcode": None,
        }

        # Normalize
        address = address.strip()
        address_upper = address.upper()

        # Extract postcode (4 digits at end)
        postcode_match = re.search(r'\b(\d{4})\b\s*$', address)
        if postcode_match:
            parsed["postcode"] = postcode_match.group(1)
            address = address[:postcode_match.start()].strip()
            address_upper = address.upper()

        # Extract state
        state_pattern = r'\b(NSW|VIC|QLD|SA|WA|TAS|NT|ACT)\b'
        state_match = re.search(state_pattern, address_upper)
        if state_match:
            parsed["state"] = state_match.group(1)
            address = re.sub(state_pattern, '', address, flags=re.I).strip()

        # Split by comma to separate street from suburb
        parts = [p.strip() for p in address.split(',')]

        if len(parts) >= 2:
            street_part = parts[0]
            parsed["suburb"] = parts[-1].strip(' ,').upper()
        else:
            street_part = parts[0]

        # Extract unit/flat number (e.g., "Unit 5/", "5/", "Flat 3/")
        unit_match = re.match(r'^(?:UNIT|FLAT|APT|SUITE|SHOP)?\s*(\d+[A-Z]?)\s*/\s*', street_part, re.I)
        if unit_match:
            parsed["flat_number"] = int(re.match(r'\d+', unit_match.group(1)).group())
            street_part = street_part[unit_match.end():].strip()

        # Extract street number (e.g., "123", "15A", "10-12")
        number_match = re.match(r'^(\d+)([A-Z]?)(?:\s*-\s*(\d+)([A-Z]?))?\s+', street_part, re.I)
        if number_match:
            parsed["street_number"] = int(number_match.group(1))
            street_part = street_part[number_match.end():].strip()

        # Common street type mappings
        street_types = {
            'STREET': 'ST', 'ST': 'ST',
            'ROAD': 'RD', 'RD': 'RD',
            'AVENUE': 'AVE', 'AVE': 'AVE', 'AV': 'AVE',
            'DRIVE': 'DR', 'DR': 'DR', 'DRV': 'DR',
            'PLACE': 'PL', 'PL': 'PL',
            'COURT': 'CT', 'CT': 'CT', 'CRT': 'CT',
            'CRESCENT': 'CR', 'CRES': 'CR', 'CR': 'CR', 'CRS': 'CR',
            'LANE': 'LA', 'LA': 'LA', 'LN': 'LA',
            'WAY': 'WAY', 'WY': 'WAY',
            'PARADE': 'PDE', 'PDE': 'PDE',
            'BOULEVARD': 'BVD', 'BLVD': 'BVD', 'BVD': 'BVD',
            'HIGHWAY': 'HWY', 'HWY': 'HWY',
            'TERRACE': 'TCE', 'TCE': 'TCE', 'TER': 'TCE',
            'CLOSE': 'CL', 'CL': 'CL',
            'CIRCUIT': 'CCT', 'CCT': 'CCT', 'CIR': 'CCT',
            'GROVE': 'GR', 'GR': 'GR', 'GRV': 'GR',
            'SQUARE': 'SQ', 'SQ': 'SQ',
            'RISE': 'RISE',
            'WALK': 'WLK', 'WLK': 'WLK',
            'TRACK': 'TRK', 'TRK': 'TRK',
            'ESPLANADE': 'ESP', 'ESP': 'ESP',
        }

        # Extract street type from end
        words = street_part.upper().split()
        if words:
            last_word = words[-1]
            if last_word in street_types:
                parsed["street_type"] = street_types[last_word]
                parsed["street_name"] = ' '.join(words[:-1])
            else:
                parsed["street_name"] = ' '.join(words)

        return parsed

    async def geocode(self, address: str) -> Optional[GeocodingResult]:
        """
        Geocode address by querying GNAF data in Supabase.

        Strategy:
        1. Full-text search on full_address column (fastest)
        2. Structured search on parsed components
        3. Fuzzy suburb fallback
        """
        try:
            # Strategy 1: Search on pre-computed full_address
            result = await self._fulltext_search(address)
            if result:
                return result

            # Strategy 2: Structured component search
            parsed = self._parse_address(address)
            result = await self._structured_search(parsed)
            if result:
                return result

            # Strategy 3: Suburb centroid fallback
            result = await self._suburb_fallback(parsed)
            return result

        except Exception as e:
            logger.error(f"GNAF Supabase geocoding error for '{address}': {e}")
            return None

    async def _fulltext_search(self, address: str) -> Optional[GeocodingResult]:
        """Search using the full_address column with ilike."""
        # Clean and normalize for search
        search_term = address.upper().strip()
        # Remove extra spaces
        search_term = re.sub(r'\s+', ' ', search_term)

        # Use ilike for flexible matching
        params = {
            "full_address": f"ilike.%{search_term}%",
            "select": "address_detail_pid,full_address,locality_name,state,postcode,latitude,longitude,confidence,street_name,street_type_code,number_first",
            "limit": "1",
        }

        try:
            response = await self.client.get(
                self.rest_url,
                params=params,
                headers={**self.client.headers, "Accept-Profile": self.schema}
            )

            if response.status_code != 200:
                logger.debug(f"GNAF fulltext search failed: {response.status_code}")
                return None

            data = response.json()
            if data:
                return self._build_result(data[0], confidence=0.95)

        except Exception as e:
            logger.debug(f"Fulltext search error: {e}")

        return None

    async def _structured_search(self, parsed: dict) -> Optional[GeocodingResult]:
        """Search using parsed address components."""
        if not parsed.get("street_name"):
            return None

        # Build query parameters
        params = {
            "select": "address_detail_pid,full_address,locality_name,state,postcode,latitude,longitude,confidence,street_name,street_type_code,number_first,flat_number",
            "limit": "5",
        }

        # Add filters
        filters = []

        if parsed["street_name"]:
            params["street_name"] = f"ilike.{parsed['street_name']}%"

        if parsed["street_type"]:
            params["street_type_code"] = f"eq.{parsed['street_type']}"

        if parsed["suburb"]:
            params["locality_name"] = f"ilike.{parsed['suburb']}%"

        if parsed["postcode"]:
            params["postcode"] = f"eq.{parsed['postcode']}"

        if parsed["state"]:
            params["state"] = f"eq.{parsed['state']}"

        if parsed["street_number"]:
            params["number_first"] = f"eq.{parsed['street_number']}"

        if parsed["flat_number"]:
            params["flat_number"] = f"eq.{parsed['flat_number']}"

        try:
            response = await self.client.get(
                self.rest_url,
                params=params,
                headers={**self.client.headers, "Accept-Profile": self.schema}
            )

            if response.status_code != 200:
                logger.debug(f"GNAF structured search failed: {response.status_code}")
                return None

            data = response.json()

            if not data:
                # Try without street number for range matching
                if "number_first" in params:
                    del params["number_first"]
                    params["limit"] = "10"

                    response = await self.client.get(
                        self.rest_url,
                        params=params,
                        headers={**self.client.headers, "Accept-Profile": self.schema}
                    )

                    if response.status_code == 200:
                        data = response.json()
                        # Find closest street number
                        if data and parsed["street_number"]:
                            data.sort(key=lambda x: abs((x.get("number_first") or 0) - parsed["street_number"]))

            if data:
                # Adjust confidence based on match quality
                confidence = 0.90
                if not parsed.get("street_number") or data[0].get("number_first") != parsed["street_number"]:
                    confidence = 0.75
                return self._build_result(data[0], confidence=confidence)

        except Exception as e:
            logger.debug(f"Structured search error: {e}")

        return None

    async def _suburb_fallback(self, parsed: dict) -> Optional[GeocodingResult]:
        """Fall back to suburb centroid when exact address not found."""
        suburb = parsed.get("suburb")
        if not suburb:
            return None

        params = {
            "select": "locality_name,state,postcode,latitude,longitude",
            "locality_name": f"ilike.{suburb}%",
            "limit": "100",
        }

        if parsed.get("postcode"):
            params["postcode"] = f"eq.{parsed['postcode']}"
        elif parsed.get("state"):
            params["state"] = f"eq.{parsed['state']}"

        try:
            response = await self.client.get(
                self.rest_url,
                params=params,
                headers={**self.client.headers, "Accept-Profile": self.schema}
            )

            if response.status_code != 200 or not response.json():
                return None

            data = response.json()

            # Calculate centroid of suburb
            lats = [float(r["latitude"]) for r in data if r.get("latitude")]
            lngs = [float(r["longitude"]) for r in data if r.get("longitude")]

            if not lats or not lngs:
                return None

            return GeocodingResult(
                latitude=sum(lats) / len(lats),
                longitude=sum(lngs) / len(lngs),
                confidence=0.50,  # Low confidence - suburb level only
                formatted_address=f"{data[0].get('locality_name', suburb)}, {data[0].get('state', '')} {data[0].get('postcode', '')}".strip(),
                suburb=data[0].get("locality_name"),
                postcode=data[0].get("postcode"),
                state=data[0].get("state"),
                provider=self.name,
            )

        except Exception as e:
            logger.debug(f"Suburb fallback error: {e}")
            return None

    def _build_result(self, row: dict, confidence: float) -> GeocodingResult:
        """Build GeocodingResult from database row."""
        # Use pre-computed full_address if available
        formatted = row.get("full_address") or self._format_address(row)

        # Adjust confidence based on GNAF confidence level (0-2, where 2 is highest)
        gnaf_confidence = row.get("confidence")
        if gnaf_confidence is not None:
            if gnaf_confidence == 2:
                confidence = min(confidence + 0.05, 1.0)
            elif gnaf_confidence == 0:
                confidence = max(confidence - 0.15, 0.4)

        return GeocodingResult(
            latitude=float(row["latitude"]),
            longitude=float(row["longitude"]),
            confidence=confidence,
            formatted_address=formatted,
            suburb=row.get("locality_name"),
            postcode=row.get("postcode"),
            state=row.get("state"),
            provider=self.name,
            raw_response=row,
        )

    def _format_address(self, row: dict) -> str:
        """Format address from components if full_address not available."""
        parts = []

        if row.get("flat_number"):
            parts.append(f"Unit {row['flat_number']}/")

        if row.get("number_first"):
            num = str(row["number_first"])
            if row.get("number_last"):
                num += f"-{row['number_last']}"
            parts.append(num)

        if row.get("street_name"):
            street = row["street_name"]
            if row.get("street_type_code"):
                street += f" {row['street_type_code']}"
            parts.append(street)

        street_part = " ".join(parts)

        formatted = f"{street_part}, {row.get('locality_name', '')}"
        if row.get("state"):
            formatted += f" {row['state']}"
        if row.get("postcode"):
            formatted += f" {row['postcode']}"

        return formatted.strip()

    async def reverse_geocode(
        self, latitude: float, longitude: float, radius_m: int = 100
    ) -> Optional[GeocodingResult]:
        """
        Reverse geocode: find address for given coordinates.

        Uses PostGIS geography column for efficient spatial queries.
        """
        # Use Supabase RPC for spatial query or direct PostGIS
        # This requires a function in Supabase:
        #
        # CREATE OR REPLACE FUNCTION find_nearest_address(lat float, lng float, radius_m int)
        # RETURNS SETOF gnaf.address_principals AS $$
        #   SELECT * FROM gnaf.address_principals
        #   WHERE ST_DWithin(location, ST_SetSRID(ST_MakePoint(lng, lat), 4326)::geography, radius_m)
        #   ORDER BY location <-> ST_SetSRID(ST_MakePoint(lng, lat), 4326)::geography
        #   LIMIT 1;
        # $$ LANGUAGE sql;

        try:
            response = await self.client.post(
                f"{self.supabase_url}/rest/v1/rpc/find_nearest_address",
                json={"lat": latitude, "lng": longitude, "radius_m": radius_m},
                headers={**self.client.headers, "Accept-Profile": self.schema}
            )

            if response.status_code != 200:
                logger.debug(f"Reverse geocode failed: {response.status_code}")
                return None

            data = response.json()
            if data:
                return self._build_result(data[0], confidence=0.90)

        except Exception as e:
            logger.debug(f"Reverse geocode error: {e}")

        return None

    async def bulk_geocode(
        self, addresses: list[str], batch_size: int = 50
    ) -> list[Optional[GeocodingResult]]:
        """
        Geocode multiple addresses efficiently.

        Processes in batches to avoid overwhelming Supabase.
        """
        results = []

        for i in range(0, len(addresses), batch_size):
            batch = addresses[i:i + batch_size]

            # Process batch concurrently
            import asyncio
            batch_tasks = [self.geocode(addr) for addr in batch]
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)

            for result in batch_results:
                if isinstance(result, Exception):
                    logger.warning(f"Batch geocode error: {result}")
                    results.append(None)
                else:
                    results.append(result)

        return results
