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

    Expected Supabase table structure (adjust to match your schema):

    Table: gnaf_addresses (or similar)
    Columns:
        - address_detail_pid (text, primary key)
        - flat_number (text)
        - number_first (int)
        - number_last (int)
        - street_name (text)
        - street_type (text)  -- ST, RD, AVE, etc.
        - locality_name (text)  -- suburb
        - state_abbreviation (text)  -- NSW, VIC, etc.
        - postcode (text)
        - latitude (float)
        - longitude (float)
        - lga_name (text)  -- local government area
        - mb_2021_code (text)  -- mesh block
        - confidence (int)  -- GNAF confidence level 0-2
    """

    name = "gnaf_supabase"

    def __init__(
        self,
        supabase_url: Optional[str] = None,
        supabase_key: Optional[str] = None,
        table_name: str = "gnaf_addresses",
    ):
        self.supabase_url = supabase_url or settings.supabase_url
        self.supabase_key = supabase_key or settings.supabase_anon_key
        self.table_name = table_name

        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Supabase URL and key are required for GNAF geocoding")

        self.client = httpx.AsyncClient(
            timeout=10.0,
            headers={
                "apikey": self.supabase_key,
                "Authorization": f"Bearer {self.supabase_key}",
                "Content-Type": "application/json",
            }
        )
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
        address = address.strip().upper()

        # Extract postcode (4 digits at end)
        postcode_match = re.search(r'\b(\d{4})\b\s*$', address)
        if postcode_match:
            parsed["postcode"] = postcode_match.group(1)
            address = address[:postcode_match.start()].strip()

        # Extract state
        state_pattern = r'\b(NSW|VIC|QLD|SA|WA|TAS|NT|ACT)\b'
        state_match = re.search(state_pattern, address)
        if state_match:
            parsed["state"] = state_match.group(1)
            address = re.sub(state_pattern, '', address).strip()

        # Split by comma to separate street from suburb
        parts = [p.strip() for p in address.split(',')]

        if len(parts) >= 2:
            street_part = parts[0]
            parsed["suburb"] = parts[-1].strip(' ,')
        else:
            street_part = parts[0]

        # Extract unit/flat number
        unit_match = re.match(r'^(UNIT|FLAT|APT|SUITE|SHOP)?\s*(\d+[A-Z]?)\s*/\s*', street_part, re.I)
        if unit_match:
            parsed["flat_number"] = unit_match.group(2)
            street_part = street_part[unit_match.end():].strip()

        # Extract street number
        number_match = re.match(r'^(\d+[A-Z]?(?:-\d+[A-Z]?)?)\s+', street_part)
        if number_match:
            parsed["street_number"] = number_match.group(1)
            street_part = street_part[number_match.end():].strip()

        # Common street type abbreviations
        street_types = {
            'STREET': 'ST', 'ST': 'ST',
            'ROAD': 'RD', 'RD': 'RD',
            'AVENUE': 'AVE', 'AVE': 'AVE', 'AV': 'AVE',
            'DRIVE': 'DR', 'DR': 'DR',
            'PLACE': 'PL', 'PL': 'PL',
            'COURT': 'CT', 'CT': 'CT',
            'CRESCENT': 'CR', 'CRES': 'CR', 'CR': 'CR',
            'LANE': 'LA', 'LA': 'LA', 'LN': 'LA',
            'WAY': 'WAY',
            'PARADE': 'PDE', 'PDE': 'PDE',
            'BOULEVARD': 'BVD', 'BLVD': 'BVD', 'BVD': 'BVD',
            'HIGHWAY': 'HWY', 'HWY': 'HWY',
            'TERRACE': 'TCE', 'TCE': 'TCE', 'TER': 'TCE',
            'CLOSE': 'CL', 'CL': 'CL',
            'CIRCUIT': 'CCT', 'CCT': 'CCT',
            'GROVE': 'GR', 'GR': 'GR',
        }

        # Extract street type from end of street part
        words = street_part.split()
        if words:
            last_word = words[-1]
            if last_word in street_types:
                parsed["street_type"] = street_types[last_word]
                parsed["street_name"] = ' '.join(words[:-1])
            else:
                parsed["street_name"] = street_part

        return parsed

    async def geocode(self, address: str) -> Optional[GeocodingResult]:
        """
        Geocode address by querying GNAF data in Supabase.

        Uses a tiered matching approach:
        1. Exact match on all components
        2. Fuzzy match on street name + suburb
        3. Match on suburb + postcode only
        """
        try:
            parsed = self._parse_address(address)

            # Build query - try exact match first
            result = await self._exact_match(parsed)

            if not result:
                # Try fuzzy street name match
                result = await self._fuzzy_match(parsed)

            if not result:
                # Fall back to suburb centroid
                result = await self._suburb_match(parsed)

            return result

        except Exception as e:
            logger.error(f"GNAF Supabase geocoding error for '{address}': {e}")
            return None

    async def _exact_match(self, parsed: dict) -> Optional[GeocodingResult]:
        """Try exact match on address components."""
        filters = []

        if parsed["street_name"]:
            filters.append(f"street_name=ilike.{parsed['street_name']}*")

        if parsed["street_number"]:
            # Handle number ranges like "15A" or "15-17"
            num = re.match(r'(\d+)', parsed["street_number"])
            if num:
                filters.append(f"number_first=eq.{num.group(1)}")

        if parsed["suburb"]:
            filters.append(f"locality_name=ilike.{parsed['suburb']}*")

        if parsed["postcode"]:
            filters.append(f"postcode=eq.{parsed['postcode']}")

        if parsed["state"]:
            filters.append(f"state_abbreviation=eq.{parsed['state']}")

        if len(filters) < 2:
            return None

        query_params = "&".join(filters) + "&limit=1"

        response = await self.client.get(f"{self.rest_url}?{query_params}")

        if response.status_code != 200:
            logger.warning(f"GNAF query failed: {response.status_code}")
            return None

        data = response.json()

        if not data:
            return None

        return self._build_result(data[0], confidence=0.95)

    async def _fuzzy_match(self, parsed: dict) -> Optional[GeocodingResult]:
        """Try fuzzy match using Supabase text search."""
        if not parsed["street_name"] or not parsed["suburb"]:
            return None

        # Use ilike for fuzzy matching
        street_pattern = parsed["street_name"].replace(' ', '%')

        query = (
            f"street_name=ilike.%{street_pattern}%"
            f"&locality_name=ilike.{parsed['suburb']}%"
            f"&limit=5"
        )

        if parsed["postcode"]:
            query += f"&postcode=eq.{parsed['postcode']}"

        response = await self.client.get(f"{self.rest_url}?{query}")

        if response.status_code != 200 or not response.json():
            return None

        data = response.json()

        # If we have a street number, try to find closest match
        if parsed["street_number"] and len(data) > 1:
            target_num = int(re.match(r'(\d+)', parsed["street_number"]).group(1))
            data.sort(key=lambda x: abs((x.get("number_first") or 0) - target_num))

        return self._build_result(data[0], confidence=0.80)

    async def _suburb_match(self, parsed: dict) -> Optional[GeocodingResult]:
        """Fall back to suburb centroid."""
        if not parsed["suburb"]:
            return None

        # Query for suburb centroid (average of all addresses in suburb)
        # This requires a Supabase function or we calculate from sample
        query = f"locality_name=ilike.{parsed['suburb']}%&limit=100"

        if parsed["postcode"]:
            query += f"&postcode=eq.{parsed['postcode']}"
        elif parsed["state"]:
            query += f"&state_abbreviation=eq.{parsed['state']}"

        response = await self.client.get(
            f"{self.rest_url}?{query}&select=latitude,longitude,locality_name,postcode,state_abbreviation"
        )

        if response.status_code != 200 or not response.json():
            return None

        data = response.json()

        if not data:
            return None

        # Calculate centroid
        lats = [r["latitude"] for r in data if r.get("latitude")]
        lngs = [r["longitude"] for r in data if r.get("longitude")]

        if not lats or not lngs:
            return None

        return GeocodingResult(
            latitude=sum(lats) / len(lats),
            longitude=sum(lngs) / len(lngs),
            confidence=0.50,  # Low confidence - suburb level only
            formatted_address=f"{parsed['suburb']}, {data[0].get('state_abbreviation', '')} {data[0].get('postcode', '')}",
            suburb=data[0].get("locality_name"),
            postcode=data[0].get("postcode"),
            state=data[0].get("state_abbreviation"),
            provider=self.name,
        )

    def _build_result(self, row: dict, confidence: float) -> GeocodingResult:
        """Build GeocodingResult from database row."""
        # Construct formatted address
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
            if row.get("street_type"):
                street += f" {row['street_type']}"
            parts.append(street)

        street_part = " ".join(parts)

        formatted = f"{street_part}, {row.get('locality_name', '')}"
        if row.get("state_abbreviation"):
            formatted += f" {row['state_abbreviation']}"
        if row.get("postcode"):
            formatted += f" {row['postcode']}"

        # Adjust confidence based on GNAF confidence level
        gnaf_confidence = row.get("confidence", 0)
        if gnaf_confidence == 2:  # Highest GNAF confidence
            confidence = min(confidence + 0.05, 1.0)
        elif gnaf_confidence == 0:  # Lowest
            confidence = max(confidence - 0.1, 0.5)

        return GeocodingResult(
            latitude=row["latitude"],
            longitude=row["longitude"],
            confidence=confidence,
            formatted_address=formatted.strip(),
            suburb=row.get("locality_name"),
            postcode=row.get("postcode"),
            state=row.get("state_abbreviation"),
            lga=row.get("lga_name"),
            provider=self.name,
            raw_response=row,
        )

    async def bulk_geocode(self, addresses: list[str]) -> list[Optional[GeocodingResult]]:
        """
        Geocode multiple addresses efficiently.

        For large batches, this is more efficient than individual calls
        as we can batch queries to Supabase.
        """
        results = []

        # Process in batches of 50
        batch_size = 50
        for i in range(0, len(addresses), batch_size):
            batch = addresses[i:i + batch_size]
            batch_results = await self._geocode_batch(batch)
            results.extend(batch_results)

        return results

    async def _geocode_batch(self, addresses: list[str]) -> list[Optional[GeocodingResult]]:
        """Geocode a batch of addresses."""
        # For now, process individually
        # Could be optimized with a single query using OR conditions
        return [await self.geocode(addr) for addr in addresses]


class SupabaseGNAFWithRPC(SupabaseGNAFProvider):
    """
    Enhanced GNAF provider using Supabase RPC functions for better matching.

    Requires these functions in your Supabase database:

    CREATE OR REPLACE FUNCTION geocode_address(
        p_street_number TEXT,
        p_street_name TEXT,
        p_suburb TEXT,
        p_postcode TEXT DEFAULT NULL,
        p_state TEXT DEFAULT NULL
    ) RETURNS TABLE (
        address_detail_pid TEXT,
        latitude FLOAT,
        longitude FLOAT,
        formatted_address TEXT,
        confidence FLOAT,
        match_type TEXT
    ) AS $$
    BEGIN
        -- Implementation with fuzzy matching
    END;
    $$ LANGUAGE plpgsql;
    """

    async def geocode(self, address: str) -> Optional[GeocodingResult]:
        """Geocode using Supabase RPC function."""
        try:
            parsed = self._parse_address(address)

            # Call RPC function
            response = await self.client.post(
                f"{self.supabase_url}/rest/v1/rpc/geocode_address",
                json={
                    "p_street_number": parsed.get("street_number"),
                    "p_street_name": parsed.get("street_name"),
                    "p_suburb": parsed.get("suburb"),
                    "p_postcode": parsed.get("postcode"),
                    "p_state": parsed.get("state"),
                }
            )

            if response.status_code != 200:
                # Fall back to parent implementation
                return await super().geocode(address)

            data = response.json()

            if not data:
                return await super().geocode(address)

            result = data[0]

            return GeocodingResult(
                latitude=result["latitude"],
                longitude=result["longitude"],
                confidence=result.get("confidence", 0.9),
                formatted_address=result.get("formatted_address"),
                provider=f"{self.name}_rpc",
                raw_response=result,
            )

        except Exception as e:
            logger.warning(f"RPC geocoding failed, falling back: {e}")
            return await super().geocode(address)
