"""Property data lookup service."""

import logging
import re
from dataclasses import dataclass
from typing import Optional

import httpx


logger = logging.getLogger(__name__)


@dataclass
class PropertyData:
    """Property data from lookup service."""

    lot_plan: Optional[str] = None
    parcel_id: Optional[str] = None
    zoning: Optional[str] = None
    land_area_sqm: Optional[float] = None
    land_use: Optional[str] = None
    legal_description: Optional[str] = None
    lga: Optional[str] = None
    address_formatted: Optional[str] = None
    raw_response: Optional[dict] = None


class PropertyLookup:
    """
    Service for looking up property data by address.

    Supports multiple data sources:
    - NSW Spatial Services
    - VIC Land Registry Services
    - QLD Globe
    - SA Property Location Browser
    """

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=15.0)
        self._state_handlers = {
            "NSW": self._lookup_nsw,
            "VIC": self._lookup_vic,
            "QLD": self._lookup_qld,
            "SA": self._lookup_sa,
            "WA": self._lookup_wa,
            "TAS": self._lookup_tas,
            "NT": self._lookup_nt,
            "ACT": self._lookup_act,
        }

    async def lookup(
        self,
        address: str,
        suburb: Optional[str] = None,
        state: Optional[str] = None,
    ) -> Optional[dict]:
        """
        Lookup property data for an address.

        Returns dict with property information or None if not found.
        """
        if not state:
            state = self._detect_state_from_address(address)

        if not state:
            logger.warning(f"Could not determine state for address: {address}")
            return None

        state = state.upper()
        handler = self._state_handlers.get(state)

        if not handler:
            logger.warning(f"No property lookup handler for state: {state}")
            return None

        try:
            return await handler(address, suburb)
        except Exception as e:
            logger.error(f"Property lookup failed for '{address}': {e}")
            return None

    def _detect_state_from_address(self, address: str) -> Optional[str]:
        """Attempt to detect state from address string."""
        address_upper = address.upper()

        state_patterns = {
            "NSW": [" NSW", " NEW SOUTH WALES", ", NSW"],
            "VIC": [" VIC", " VICTORIA", ", VIC"],
            "QLD": [" QLD", " QUEENSLAND", ", QLD"],
            "SA": [" SA ", " SOUTH AUSTRALIA", ", SA"],
            "WA": [" WA ", " WESTERN AUSTRALIA", ", WA"],
            "TAS": [" TAS", " TASMANIA", ", TAS"],
            "NT": [" NT ", " NORTHERN TERRITORY", ", NT"],
            "ACT": [" ACT", " CANBERRA", ", ACT"],
        }

        for state, patterns in state_patterns.items():
            if any(pattern in address_upper for pattern in patterns):
                return state

        return None

    async def _lookup_nsw(self, address: str, suburb: Optional[str] = None) -> Optional[dict]:
        """Lookup property in NSW Spatial Services."""
        # NSW uses the NSW Spatial Services API
        # This is a placeholder - actual implementation would use the real API
        try:
            # NSW API endpoint (example)
            api_url = "https://maps.six.nsw.gov.au/arcgis/rest/services/sixmaps/Cadastre/MapServer/find"
            params = {
                "searchText": address,
                "contains": "true",
                "layers": "0",
                "returnGeometry": "true",
                "f": "json",
            }

            response = await self.client.get(api_url, params=params)
            response.raise_for_status()
            data = response.json()

            if not data.get("results"):
                return None

            result = data["results"][0]
            attributes = result.get("attributes", {})

            return {
                "lot_plan": f"{attributes.get('lotnumber', '')}//{attributes.get('plannumber', '')}",
                "parcel_id": attributes.get("cadid"),
                "lga": attributes.get("lganame"),
                "land_area_sqm": attributes.get("area"),
                "raw_response": result,
            }

        except Exception as e:
            logger.debug(f"NSW lookup failed: {e}")
            return None

    async def _lookup_vic(self, address: str, suburb: Optional[str] = None) -> Optional[dict]:
        """Lookup property in VIC Land Registry."""
        # Victoria uses the DELWP Spatial Data
        try:
            api_url = "https://services.land.vic.gov.au/catalogue/publicproxy/guest/dv_geoserver/wfs"
            params = {
                "service": "WFS",
                "version": "1.1.0",
                "request": "GetFeature",
                "typeName": "VMLITE_PROPERTY_ADDRESS",
                "outputFormat": "json",
                "CQL_FILTER": f"ADDRESS LIKE '%{address}%'",
                "maxFeatures": "1",
            }

            response = await self.client.get(api_url, params=params)
            response.raise_for_status()
            data = response.json()

            features = data.get("features", [])
            if not features:
                return None

            props = features[0].get("properties", {})

            return {
                "lot_plan": props.get("LOT_SEC_PLAN"),
                "parcel_id": props.get("PROPERTY_NUMBER"),
                "lga": props.get("LGA_NAME"),
                "address_formatted": props.get("ADDRESS"),
                "raw_response": features[0],
            }

        except Exception as e:
            logger.debug(f"VIC lookup failed: {e}")
            return None

    async def _lookup_qld(self, address: str, suburb: Optional[str] = None) -> Optional[dict]:
        """Lookup property in QLD Globe."""
        try:
            api_url = "https://gisservices.information.qld.gov.au/arcgis/rest/services/Basemaps/Property/MapServer/find"
            params = {
                "searchText": address,
                "layers": "0",
                "f": "json",
            }

            response = await self.client.get(api_url, params=params)
            response.raise_for_status()
            data = response.json()

            results = data.get("results", [])
            if not results:
                return None

            attrs = results[0].get("attributes", {})

            return {
                "lot_plan": attrs.get("LOT_PLAN"),
                "parcel_id": attrs.get("PARCEL_ID"),
                "lga": attrs.get("LGA"),
                "land_area_sqm": attrs.get("AREA_M2"),
                "raw_response": results[0],
            }

        except Exception as e:
            logger.debug(f"QLD lookup failed: {e}")
            return None

    async def _lookup_sa(self, address: str, suburb: Optional[str] = None) -> Optional[dict]:
        """Lookup property in SA Location Browser."""
        try:
            api_url = "https://location.sa.gov.au/server/rest/services/property/PropertyAddress/MapServer/find"
            params = {
                "searchText": address,
                "layers": "0",
                "f": "json",
            }

            response = await self.client.get(api_url, params=params)
            response.raise_for_status()
            data = response.json()

            results = data.get("results", [])
            if not results:
                return None

            attrs = results[0].get("attributes", {})

            return {
                "lot_plan": f"D{attrs.get('ALLOTMENT')}/{attrs.get('PLAN_PARCEL')}",
                "parcel_id": attrs.get("PROPERTY_NO"),
                "lga": attrs.get("LGA"),
                "raw_response": results[0],
            }

        except Exception as e:
            logger.debug(f"SA lookup failed: {e}")
            return None

    async def _lookup_wa(self, address: str, suburb: Optional[str] = None) -> Optional[dict]:
        """Lookup property in WA Landgate."""
        # WA uses Landgate's SLIP services
        try:
            api_url = "https://services.slip.wa.gov.au/public/services/SLIP_Public_Services/PropertyStreetAddress/MapServer/find"
            params = {
                "searchText": address,
                "layers": "0",
                "f": "json",
            }

            response = await self.client.get(api_url, params=params)
            response.raise_for_status()
            data = response.json()

            results = data.get("results", [])
            if not results:
                return None

            attrs = results[0].get("attributes", {})

            return {
                "lot_plan": f"Lot {attrs.get('LOT_NO')} on {attrs.get('PLAN_TYPE')}{attrs.get('PLAN_NO')}",
                "parcel_id": attrs.get("CADASTRE_PK"),
                "lga": attrs.get("LGA_NAME"),
                "land_area_sqm": attrs.get("AREA_SQM"),
                "raw_response": results[0],
            }

        except Exception as e:
            logger.debug(f"WA lookup failed: {e}")
            return None

    async def _lookup_tas(self, address: str, suburb: Optional[str] = None) -> Optional[dict]:
        """Lookup property in Tasmania LIST."""
        try:
            api_url = "https://services.thelist.tas.gov.au/arcgis/rest/services/Public/PropertySearchService/MapServer/find"
            params = {
                "searchText": address,
                "layers": "1",
                "f": "json",
            }

            response = await self.client.get(api_url, params=params)
            response.raise_for_status()
            data = response.json()

            results = data.get("results", [])
            if not results:
                return None

            attrs = results[0].get("attributes", {})

            return {
                "parcel_id": attrs.get("PID"),
                "lga": attrs.get("MUNICIPALITY"),
                "land_area_sqm": attrs.get("AREA_HA", 0) * 10000,
                "zoning": attrs.get("ZONE_CODE"),
                "raw_response": results[0],
            }

        except Exception as e:
            logger.debug(f"TAS lookup failed: {e}")
            return None

    async def _lookup_nt(self, address: str, suburb: Optional[str] = None) -> Optional[dict]:
        """Lookup property in NT Land Information."""
        try:
            api_url = "https://nrmaps.nt.gov.au/arcgis/rest/services/Cadastre/CadastreDynamic/MapServer/find"
            params = {
                "searchText": address,
                "layers": "0",
                "f": "json",
            }

            response = await self.client.get(api_url, params=params)
            response.raise_for_status()
            data = response.json()

            results = data.get("results", [])
            if not results:
                return None

            attrs = results[0].get("attributes", {})

            return {
                "lot_plan": f"{attrs.get('LOT')}/{attrs.get('PLAN_NO')}",
                "parcel_id": attrs.get("PARCEL_ID"),
                "land_area_sqm": attrs.get("AREA_SQM"),
                "raw_response": results[0],
            }

        except Exception as e:
            logger.debug(f"NT lookup failed: {e}")
            return None

    async def _lookup_act(self, address: str, suburb: Optional[str] = None) -> Optional[dict]:
        """Lookup property in ACT ACTMAPI."""
        try:
            api_url = "https://actmapi-actgov.opendata.arcgis.com/arcgis/rest/services/Address/MapServer/find"
            params = {
                "searchText": address,
                "layers": "0",
                "f": "json",
            }

            response = await self.client.get(api_url, params=params)
            response.raise_for_status()
            data = response.json()

            results = data.get("results", [])
            if not results:
                return None

            attrs = results[0].get("attributes", {})

            return {
                "lot_plan": f"Block {attrs.get('BLOCK')} Section {attrs.get('SECTION')}",
                "parcel_id": attrs.get("PARCEL_ID"),
                "lga": "ACT",
                "address_formatted": attrs.get("FULL_ADDRESS"),
                "raw_response": results[0],
            }

        except Exception as e:
            logger.debug(f"ACT lookup failed: {e}")
            return None

    async def get_zoning_info(self, lot_plan: str, state: str) -> Optional[dict]:
        """Get zoning information for a lot/plan."""
        # This would integrate with state planning portals
        # Placeholder implementation
        return None

    async def get_overlays(self, latitude: float, longitude: float, state: str) -> list[dict]:
        """Get planning overlays for a location."""
        # This would check for heritage, flood, bushfire, etc. overlays
        # Placeholder implementation
        return []
