"""
AI-Powered Field Mapper
Uses Claude to intelligently map council-specific field names to the master schema.
"""

import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional, Any

from anthropic import Anthropic

from src.config import settings
from src.schemas.master import FieldMapping


# Master schema field definitions for the LLM
SCHEMA_DEFINITIONS = """
MASTER SCHEMA FIELDS:

IDENTIFIERS:
- da_number: Unique application identifier (e.g., "DA-2025-1234", "2025/0456", "A006234567")

PROPERTY FIELDS:
- address: Full property street address
- suburb: Suburb/locality name
- postcode: 4-digit Australian postcode
- state: State abbreviation (NSW, VIC, QLD, SA, WA, TAS, NT, ACT)
- lot_plan: Lot/Plan or Title reference (e.g., "Lot 1 DP123456", "1/SP12345")

APPLICATION TYPE (pick one):
- development_application
- complying_development
- construction_certificate
- subdivision
- modification
- review
- other

CATEGORY (pick one):
- residential_single (single house)
- residential_dual (dual occupancy, duplex)
- residential_multi (units, apartments, townhouses)
- residential_alteration (alterations & additions)
- residential_ancillary (granny flat, shed, pool, deck)
- residential_subdivision (land division)
- commercial_retail (shops, restaurants)
- commercial_office (office buildings)
- industrial_warehouse (warehouses, storage)
- industrial_manufacturing (factories)
- mixed_use (combined residential/commercial)
- demolition
- change_of_use
- signage
- tree_removal
- other

STATUS (pick one):
- lodged
- registered
- under_assessment
- on_exhibition
- additional_info_required
- referred
- determined
- approved
- approved_with_conditions
- refused
- withdrawn
- lapsed
- appealed
- unknown

DECISION (pick one):
- approved
- approved_with_conditions
- refused
- deferred
- withdrawn
- not_determined

DATE FIELDS (expect various date formats):
- lodged_date: Date application was submitted
- exhibition_start: Start of public notification period
- exhibition_end: End of public notification period
- determined_date: Date decision was made

NUMERIC FIELDS:
- estimated_cost: Dollar value of proposed works (may include $ symbol, commas)
- dwelling_count: Number of dwellings in proposal
- lot_count: Number of lots (for subdivisions)
- storeys: Number of storeys/floors
- floor_area_sqm: Floor area in square meters
- car_spaces: Number of parking spaces

PARTY FIELDS:
- applicant_name: Name of applicant
- owner_name: Name of property owner
- architect: Architect/designer name
- builder: Builder name

OTHER:
- description: Full text description of proposed works
- source_url: URL of the application page
"""


class FieldMappingCache:
    """
    Cache field mappings to avoid repeated LLM calls for the same council.
    Once a council's mapping is learned, it's stored and reused.
    """

    def __init__(self, cache_path: Optional[str] = None):
        self.cache_path = Path(cache_path or settings.mappings_cache_path)
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self.mappings: dict[str, FieldMapping] = self._load_cache()

    def _load_cache(self) -> dict[str, FieldMapping]:
        """Load cached mappings from file."""
        if self.cache_path.exists():
            try:
                with open(self.cache_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return {
                        k: FieldMapping(**v) for k, v in data.items()
                    }
            except (json.JSONDecodeError, Exception):
                return {}
        return {}

    def save_cache(self) -> None:
        """Save mappings to file."""
        with open(self.cache_path, "w", encoding="utf-8") as f:
            json.dump(
                {k: v.model_dump() for k, v in self.mappings.items()},
                f,
                indent=2,
                default=str,
            )

    def get_mapping(self, council_code: str) -> Optional[FieldMapping]:
        """Get cached mapping for a council."""
        return self.mappings.get(council_code)

    def set_mapping(self, council_code: str, mapping: FieldMapping) -> None:
        """Cache a mapping for a council."""
        self.mappings[council_code] = mapping
        self.save_cache()

    def has_mapping(self, council_code: str) -> bool:
        """Check if mapping exists for a council."""
        return council_code in self.mappings


class AIFieldMapper:
    """
    Uses Claude to intelligently map council-specific field names
    to the master schema.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.client = Anthropic(api_key=api_key or settings.anthropic_api_key)
        self.model = settings.anthropic_model
        self.cache = FieldMappingCache()

    async def learn_mapping(
        self,
        council_code: str,
        sample_data: list[dict],
        force_refresh: bool = False,
    ) -> FieldMapping:
        """
        Learn the field mapping for a new council by analyzing sample data.

        Args:
            council_code: Unique council identifier
            sample_data: List of 3-5 sample records from the council
            force_refresh: Force re-learning even if cached

        Returns:
            FieldMapping object
        """
        # Check cache first
        if not force_refresh:
            cached = self.cache.get_mapping(council_code)
            if cached:
                return cached

        # Prepare sample for LLM
        samples = sample_data[:5]  # Limit to 5 samples

        prompt = f"""
Analyze these sample records from {council_code} council's planning portal and create a field mapping to our master schema.

SAMPLE DATA:
{json.dumps(samples, indent=2, default=str)}

{SCHEMA_DEFINITIONS}

Create a mapping from the council's field names to our master schema fields.
For each master schema field, identify which council field(s) contain that data.

IMPORTANT RULES:
1. Use null if a field doesn't exist in the council data
2. For compound fields (e.g., address contains suburb), use "field1+field2" syntax
3. Include status_values mapping for status field translations
4. Match field names case-insensitively
5. Look for partial matches (e.g., "Lodgement Date" → "lodged_date")

Return ONLY a valid JSON object in this exact format (no markdown, no explanation):
{{
    "da_number": "council_field_name_or_null",
    "address": "council_field_name_or_null",
    "suburb": "council_field_name_or_null",
    "postcode": "council_field_name_or_null",
    "state": "council_field_name_or_null",
    "lot_plan": "council_field_name_or_null",
    "application_type": "council_field_name_or_null",
    "description": "council_field_name_or_null",
    "status": "council_field_name_or_null",
    "decision": "council_field_name_or_null",
    "lodged_date": "council_field_name_or_null",
    "exhibition_start": "council_field_name_or_null",
    "exhibition_end": "council_field_name_or_null",
    "determined_date": "council_field_name_or_null",
    "estimated_cost": "council_field_name_or_null",
    "dwelling_count": "council_field_name_or_null",
    "lot_count": "council_field_name_or_null",
    "storeys": "council_field_name_or_null",
    "floor_area_sqm": "council_field_name_or_null",
    "car_spaces": "council_field_name_or_null",
    "applicant_name": "council_field_name_or_null",
    "owner_name": "council_field_name_or_null",
    "status_values": {{
        "council_status_1": "normalized_status",
        "council_status_2": "normalized_status"
    }}
}}
"""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
        )

        response_text = response.content[0].text

        # Parse response
        try:
            # Handle markdown code blocks
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                json_str = response_text.split("```")[1].split("```")[0]
            else:
                json_str = response_text

            mapping_data = json.loads(json_str.strip())

            # Extract status_values separately
            status_values = mapping_data.pop("status_values", {})

            # Create FieldMapping object
            field_mapping = FieldMapping(
                council_code=council_code,
                mapping=mapping_data,
                status_values=status_values,
                learned_at=datetime.utcnow(),
                sample_count=len(samples),
                confidence=0.8,  # Base confidence for AI-generated mappings
            )

            # Cache the mapping
            self.cache.set_mapping(council_code, field_mapping)

            return field_mapping

        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse mapping response: {e}\nResponse: {response_text}")

    def apply_mapping(
        self,
        council_code: str,
        raw_record: dict,
    ) -> dict:
        """
        Apply a learned mapping to transform a raw council record
        to the master schema format.

        Args:
            council_code: Council identifier
            raw_record: Raw data from council scraper

        Returns:
            Normalized record in master schema format
        """
        mapping = self.cache.get_mapping(council_code)
        if not mapping:
            raise ValueError(
                f"No mapping found for {council_code}. Call learn_mapping first."
            )

        normalized = {}

        for master_field, council_field in mapping.mapping.items():
            if council_field is None:
                normalized[master_field] = None
                continue

            # Handle compound fields (field1+field2)
            if "+" in str(council_field):
                fields = council_field.split("+")
                values = []
                for f in fields:
                    val = self._get_field_value(raw_record, f.strip())
                    if val:
                        values.append(str(val))
                normalized[master_field] = " ".join(values) if values else None
            else:
                normalized[master_field] = self._get_field_value(raw_record, council_field)

        # Apply status mapping if present
        if mapping.status_values and normalized.get("status"):
            raw_status = str(normalized["status"]).strip()
            # Try exact match first, then case-insensitive
            if raw_status in mapping.status_values:
                normalized["status"] = mapping.status_values[raw_status]
            else:
                lower_status = raw_status.lower()
                for key, value in mapping.status_values.items():
                    if key.lower() == lower_status:
                        normalized["status"] = value
                        break

        return normalized

    def _get_field_value(self, record: dict, field_name: str) -> Any:
        """Get field value from record, handling case-insensitive matching."""
        # Try exact match first
        if field_name in record:
            return record[field_name]

        # Try case-insensitive match
        lower_field = field_name.lower()
        for key, value in record.items():
            if key.lower() == lower_field:
                return value

        # Try with underscores replaced by spaces and vice versa
        for key, value in record.items():
            normalized_key = key.lower().replace(" ", "_").replace("-", "_")
            normalized_field = lower_field.replace(" ", "_").replace("-", "_")
            if normalized_key == normalized_field:
                return value

        return None

    async def validate_mapping(
        self,
        council_code: str,
        test_records: list[dict],
    ) -> dict:
        """
        Validate a mapping against test records.

        Args:
            council_code: Council identifier
            test_records: Records to validate against

        Returns:
            Validation results with scores
        """
        mapping = self.cache.get_mapping(council_code)
        if not mapping:
            return {"valid": False, "error": "No mapping found"}

        results = {
            "council_code": council_code,
            "records_tested": len(test_records),
            "fields_mapped": 0,
            "fields_with_data": 0,
            "field_coverage": {},
        }

        essential_fields = ["da_number", "address", "description"]
        optional_fields = [
            "suburb", "postcode", "status", "lodged_date",
            "estimated_cost", "category"
        ]

        for record in test_records:
            normalized = self.apply_mapping(council_code, record)

            for field in essential_fields + optional_fields:
                if field not in results["field_coverage"]:
                    results["field_coverage"][field] = {"mapped": 0, "has_data": 0}

                if mapping.mapping.get(field):
                    results["field_coverage"][field]["mapped"] += 1
                    if normalized.get(field):
                        results["field_coverage"][field]["has_data"] += 1

        # Calculate overall scores
        total_mapped = sum(
            1 for f in essential_fields + optional_fields
            if mapping.mapping.get(f)
        )
        total_with_data = sum(
            fc["has_data"] for fc in results["field_coverage"].values()
        )

        results["fields_mapped"] = total_mapped
        results["fields_with_data"] = total_with_data
        results["coverage_score"] = total_mapped / len(essential_fields + optional_fields)
        results["data_score"] = (
            total_with_data / (len(test_records) * total_mapped)
            if total_mapped > 0 else 0
        )

        return results
