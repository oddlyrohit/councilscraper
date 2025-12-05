"""
Data Normalizer
Cleans and normalizes scraped data into consistent formats.
"""

import re
from datetime import date, datetime
from typing import Optional, Any
from decimal import Decimal, InvalidOperation


class DataNormalizer:
    """
    Normalizes raw scraped data into consistent formats.
    Handles dates, currency, addresses, and other common fields.
    """

    # Australian state abbreviations
    STATES = {"NSW", "VIC", "QLD", "SA", "WA", "TAS", "NT", "ACT"}

    # Common date formats used by Australian councils
    DATE_FORMATS = [
        "%d/%m/%Y",      # 25/12/2025
        "%d-%m-%Y",      # 25-12-2025
        "%Y-%m-%d",      # 2025-12-25
        "%d %b %Y",      # 25 Dec 2025
        "%d %B %Y",      # 25 December 2025
        "%Y/%m/%d",      # 2025/12/25
        "%d.%m.%Y",      # 25.12.2025
        "%d %b, %Y",     # 25 Dec, 2025
        "%B %d, %Y",     # December 25, 2025
    ]

    def normalize_date(self, value: Any) -> Optional[date]:
        """
        Normalize various date formats to date object.

        Args:
            value: Date string or datetime object

        Returns:
            date object or None if parsing fails
        """
        if value is None:
            return None

        if isinstance(value, date):
            return value

        if isinstance(value, datetime):
            return value.date()

        if not isinstance(value, str):
            return None

        value = value.strip()
        if not value:
            return None

        # Try ISO format first
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
        except ValueError:
            pass

        # Try common formats
        for fmt in self.DATE_FORMATS:
            try:
                return datetime.strptime(value, fmt).date()
            except ValueError:
                continue

        # Try to extract date from longer string
        date_patterns = [
            r"(\d{1,2})[/-](\d{1,2})[/-](\d{4})",  # dd/mm/yyyy or dd-mm-yyyy
            r"(\d{4})[/-](\d{1,2})[/-](\d{1,2})",  # yyyy/mm/dd or yyyy-mm-dd
        ]

        for pattern in date_patterns:
            match = re.search(pattern, value)
            if match:
                groups = match.groups()
                try:
                    if len(groups[0]) == 4:  # yyyy-mm-dd
                        return date(int(groups[0]), int(groups[1]), int(groups[2]))
                    else:  # dd-mm-yyyy
                        return date(int(groups[2]), int(groups[1]), int(groups[0]))
                except ValueError:
                    continue

        return None

    def normalize_currency(self, value: Any) -> Optional[float]:
        """
        Normalize currency values to float.

        Args:
            value: Currency string (e.g., "$1,500,000", "1.5M", "1500000")

        Returns:
            Float value or None if parsing fails
        """
        if value is None:
            return None

        if isinstance(value, (int, float)):
            return float(value)

        if not isinstance(value, str):
            return None

        value = value.strip()
        if not value:
            return None

        # Remove currency symbols and common prefixes
        value = re.sub(r"[$AUD\s]", "", value, flags=re.IGNORECASE)

        # Remove commas
        value = value.replace(",", "")

        # Handle multiplier suffixes
        multiplier = 1
        if value.upper().endswith("K"):
            multiplier = 1_000
            value = value[:-1]
        elif value.upper().endswith("M"):
            multiplier = 1_000_000
            value = value[:-1]
        elif value.upper().endswith("B"):
            multiplier = 1_000_000_000
            value = value[:-1]

        try:
            result = float(Decimal(value)) * multiplier
            # Sanity check - DA costs should be reasonable
            if 0 <= result <= 10_000_000_000:  # Up to $10B
                return result
        except (ValueError, InvalidOperation):
            pass

        return None

    def normalize_address(self, address: str) -> dict:
        """
        Parse and normalize an Australian address.

        Args:
            address: Full address string

        Returns:
            Dict with parsed components
        """
        result = {
            "full_address": address,
            "street_address": None,
            "suburb": None,
            "state": None,
            "postcode": None,
        }

        if not address:
            return result

        address = address.strip()
        result["full_address"] = address

        # Try to extract postcode (4 digits at end)
        postcode_match = re.search(r"\b(\d{4})\s*$", address)
        if postcode_match:
            result["postcode"] = postcode_match.group(1)
            address = address[:postcode_match.start()].strip()

        # Try to extract state
        for state in self.STATES:
            pattern = rf"\b{state}\b"
            if re.search(pattern, address, re.IGNORECASE):
                result["state"] = state
                address = re.sub(pattern, "", address, flags=re.IGNORECASE).strip()
                break

        # Clean up trailing comma
        address = address.rstrip(",").strip()

        # Try to extract suburb (typically last part before state/postcode)
        parts = [p.strip() for p in address.split(",")]
        if len(parts) >= 2:
            result["suburb"] = parts[-1].title()
            result["street_address"] = ", ".join(parts[:-1])
        else:
            # Try space-separated parts
            words = address.split()
            if len(words) >= 3:
                # Assume last 1-2 words are suburb
                # Look for common patterns
                for i in range(len(words) - 1, 0, -1):
                    potential_suburb = " ".join(words[i:])
                    # If it looks like a suburb (proper noun, not number)
                    if potential_suburb[0].isupper() and not potential_suburb[0].isdigit():
                        result["suburb"] = potential_suburb
                        result["street_address"] = " ".join(words[:i])
                        break

            if not result["street_address"]:
                result["street_address"] = address

        return result

    def normalize_postcode(self, value: Any) -> Optional[str]:
        """Normalize Australian postcode."""
        if value is None:
            return None

        if isinstance(value, int):
            value = str(value).zfill(4)
        elif isinstance(value, float):
            value = str(int(value)).zfill(4)
        elif isinstance(value, str):
            value = value.strip()
            # Extract 4-digit number
            match = re.search(r"\b(\d{4})\b", value)
            if match:
                value = match.group(1)
            else:
                return None
        else:
            return None

        # Validate Australian postcode ranges
        try:
            pc = int(value)
            if 200 <= pc <= 9999:  # Valid Australian postcode range
                return value.zfill(4)
        except ValueError:
            pass

        return None

    def normalize_state(self, value: Any) -> Optional[str]:
        """Normalize Australian state abbreviation."""
        if value is None:
            return None

        if not isinstance(value, str):
            value = str(value)

        value = value.strip().upper()

        # Direct match
        if value in self.STATES:
            return value

        # Common variations
        state_map = {
            "NEW SOUTH WALES": "NSW",
            "VICTORIA": "VIC",
            "QUEENSLAND": "QLD",
            "SOUTH AUSTRALIA": "SA",
            "WESTERN AUSTRALIA": "WA",
            "TASMANIA": "TAS",
            "NORTHERN TERRITORY": "NT",
            "AUSTRALIAN CAPITAL TERRITORY": "ACT",
        }

        return state_map.get(value)

    def normalize_da_number(self, value: Any) -> Optional[str]:
        """Normalize DA number format."""
        if value is None:
            return None

        if not isinstance(value, str):
            value = str(value)

        value = value.strip()
        if not value:
            return None

        # Remove common prefixes/suffixes but keep the core reference
        value = re.sub(r"^\s*(DA|CDC|CC|MOD|REV)\s*[-:]?\s*", "", value, flags=re.IGNORECASE)

        # Clean up whitespace
        value = " ".join(value.split())

        return value if value else None

    def normalize_description(self, value: Any) -> Optional[str]:
        """Normalize description text."""
        if value is None:
            return None

        if not isinstance(value, str):
            value = str(value)

        # Clean up whitespace
        value = " ".join(value.split())

        # Remove excessive punctuation
        value = re.sub(r"\.{2,}", ".", value)
        value = re.sub(r"-{2,}", "-", value)

        # Capitalize first letter
        if value:
            value = value[0].upper() + value[1:]

        return value.strip() if value else None

    def normalize_integer(self, value: Any, min_val: int = 0, max_val: int = 10000) -> Optional[int]:
        """Normalize to integer within range."""
        if value is None:
            return None

        try:
            if isinstance(value, str):
                # Extract first number from string
                match = re.search(r"(\d+)", value)
                if match:
                    value = int(match.group(1))
                else:
                    return None
            else:
                value = int(value)

            if min_val <= value <= max_val:
                return value
        except (ValueError, TypeError):
            pass

        return None

    def normalize_float(self, value: Any, min_val: float = 0, max_val: float = float("inf")) -> Optional[float]:
        """Normalize to float within range."""
        if value is None:
            return None

        try:
            if isinstance(value, str):
                # Remove non-numeric except decimal point
                value = re.sub(r"[^\d.]", "", value)
                value = float(value)
            else:
                value = float(value)

            if min_val <= value <= max_val:
                return value
        except (ValueError, TypeError):
            pass

        return None

    def normalize_record(self, record: dict) -> dict:
        """
        Normalize all fields in a record.

        Args:
            record: Raw record with mapped field names

        Returns:
            Normalized record
        """
        normalized = {}

        # String fields
        for field in ["da_number"]:
            if field in record:
                normalized[field] = self.normalize_da_number(record[field])

        for field in ["description", "applicant_name", "owner_name", "architect", "builder"]:
            if field in record:
                normalized[field] = self.normalize_description(record[field])

        # Address parsing
        if "address" in record:
            addr_parts = self.normalize_address(record["address"])
            normalized["address"] = addr_parts["full_address"]
            if not record.get("suburb"):
                normalized["suburb"] = addr_parts["suburb"]
            if not record.get("postcode"):
                normalized["postcode"] = addr_parts["postcode"]
            if not record.get("state"):
                normalized["state"] = addr_parts["state"]

        # Postcode and state
        if "postcode" in record and "postcode" not in normalized:
            normalized["postcode"] = self.normalize_postcode(record["postcode"])
        if "state" in record and "state" not in normalized:
            normalized["state"] = self.normalize_state(record["state"])
        if "suburb" in record and "suburb" not in normalized:
            normalized["suburb"] = record["suburb"]

        # Date fields
        for field in ["lodged_date", "exhibition_start", "exhibition_end", "determined_date", "decision_date"]:
            if field in record:
                normalized[field] = self.normalize_date(record[field])

        # Currency
        if "estimated_cost" in record:
            normalized["estimated_cost"] = self.normalize_currency(record["estimated_cost"])

        # Integer fields
        for field in ["dwelling_count", "lot_count", "storeys", "car_spaces"]:
            if field in record:
                normalized[field] = self.normalize_integer(record[field])

        # Float fields
        if "floor_area_sqm" in record:
            normalized["floor_area_sqm"] = self.normalize_float(record["floor_area_sqm"])
        if "land_area_sqm" in record:
            normalized["land_area_sqm"] = self.normalize_float(record["land_area_sqm"])

        # Pass through other fields
        for key, value in record.items():
            if key not in normalized:
                normalized[key] = value

        return normalized
