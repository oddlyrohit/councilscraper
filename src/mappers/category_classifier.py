"""
AI-Powered Category Classifier
Uses Claude to classify DA descriptions into standardized categories.
"""

import json
import hashlib
import re
from typing import Optional

from anthropic import Anthropic

from src.config import settings
from src.schemas.enums import ApplicationCategory, ApplicationType, CATEGORY_KEYWORDS
from src.schemas.master import ClassificationResult


class CategoryClassifier:
    """
    Uses LLM to classify DA descriptions into standardized categories.
    Includes a local keyword-based fallback for cost efficiency.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.client = Anthropic(api_key=api_key or settings.anthropic_api_key)
        self.model = settings.anthropic_model
        self._classification_cache: dict[str, ClassificationResult] = {}

    def _get_cache_key(self, description: str) -> str:
        """Generate cache key from description."""
        normalized = description.lower().strip()
        return hashlib.md5(normalized.encode()).hexdigest()[:16]

    def classify_with_keywords(self, description: str) -> Optional[ClassificationResult]:
        """
        Fast keyword-based classification.
        Returns None if no confident match found.
        """
        desc_lower = description.lower()

        # Track matches
        matches: dict[ApplicationCategory, int] = {}

        for category, keywords in CATEGORY_KEYWORDS.items():
            score = 0
            for keyword in keywords:
                if keyword in desc_lower:
                    score += 1
            if score > 0:
                matches[category] = score

        if not matches:
            return None

        # Get best match
        best_category = max(matches, key=matches.get)
        best_score = matches[best_category]

        # Only return if confident (at least 2 keyword matches or 1 strong match)
        if best_score >= 2 or (best_score == 1 and len(CATEGORY_KEYWORDS.get(best_category, [])) <= 3):
            # Extract additional details using regex
            dwelling_count = self._extract_dwelling_count(description)
            lot_count = self._extract_lot_count(description)
            storeys = self._extract_storeys(description)

            return ClassificationResult(
                category=best_category,
                subcategory=None,
                application_type=self._infer_application_type(description),
                dwelling_count=dwelling_count,
                lot_count=lot_count,
                storeys=storeys,
                is_new_build="new" in desc_lower or "construct" in desc_lower,
                involves_demolition="demolition" in desc_lower or "demolish" in desc_lower,
                confidence=min(0.7, 0.3 + (best_score * 0.2)),  # Cap at 0.7 for keyword-based
            )

        return None

    async def classify(
        self,
        description: str,
        use_ai: bool = True,
    ) -> ClassificationResult:
        """
        Classify a DA description into category and extract details.

        Args:
            description: Free-text description of proposed works
            use_ai: Whether to use AI for classification (otherwise keywords only)

        Returns:
            ClassificationResult with category, details, and confidence
        """
        if not description or not description.strip():
            return ClassificationResult(
                category=ApplicationCategory.OTHER,
                confidence=0.0,
            )

        # Check cache
        cache_key = self._get_cache_key(description)
        if cache_key in self._classification_cache:
            return self._classification_cache[cache_key]

        # Try keyword-based first (fast and free)
        keyword_result = self.classify_with_keywords(description)
        if keyword_result and keyword_result.confidence >= 0.6:
            self._classification_cache[cache_key] = keyword_result
            return keyword_result

        # Use AI if enabled and keywords weren't confident
        if use_ai:
            ai_result = await self._classify_with_ai(description)
            self._classification_cache[cache_key] = ai_result
            return ai_result

        # Fallback to keyword result or OTHER
        if keyword_result:
            self._classification_cache[cache_key] = keyword_result
            return keyword_result

        default_result = ClassificationResult(
            category=ApplicationCategory.OTHER,
            confidence=0.1,
        )
        self._classification_cache[cache_key] = default_result
        return default_result

    async def _classify_with_ai(self, description: str) -> ClassificationResult:
        """Classify using Claude AI."""
        categories_list = "\n".join(f"- {c.value}" for c in ApplicationCategory)

        prompt = f"""
Classify this development application description and extract key details.

DESCRIPTION:
"{description}"

AVAILABLE CATEGORIES:
{categories_list}

Analyze the description and return ONLY a valid JSON object (no markdown, no explanation):
{{
    "category": "one of the categories above",
    "subcategory": "more specific description if applicable, else null",
    "application_type": "development_application|complying_development|construction_certificate|subdivision|modification|other",
    "dwelling_count": number or null,
    "lot_count": number or null (for subdivisions),
    "storeys": number or null,
    "floor_area_sqm": number or null,
    "is_new_build": true/false,
    "involves_demolition": true/false,
    "confidence": 0.0-1.0
}}

RULES:
1. dwelling_count: Count actual dwellings (houses, units, apartments)
2. lot_count: Only for subdivisions, count of new lots
3. Be specific with subcategory (e.g., "3-storey apartment building", "dual occupancy with garage")
4. confidence should reflect how certain you are of the classification
"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}],
            )

            response_text = response.content[0].text

            # Parse JSON response
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                json_str = response_text.split("```")[1].split("```")[0]
            else:
                json_str = response_text

            result_data = json.loads(json_str.strip())

            # Map to enum
            category_str = result_data.get("category", "other")
            try:
                category = ApplicationCategory(category_str)
            except ValueError:
                category = ApplicationCategory.OTHER

            app_type_str = result_data.get("application_type", "other")
            try:
                app_type = ApplicationType(app_type_str)
            except ValueError:
                app_type = ApplicationType.OTHER

            return ClassificationResult(
                category=category,
                subcategory=result_data.get("subcategory"),
                application_type=app_type,
                dwelling_count=result_data.get("dwelling_count"),
                lot_count=result_data.get("lot_count"),
                storeys=result_data.get("storeys"),
                is_new_build=result_data.get("is_new_build"),
                involves_demolition=result_data.get("involves_demolition"),
                confidence=result_data.get("confidence", 0.8),
            )

        except (json.JSONDecodeError, Exception) as e:
            # Fallback to keyword-based
            keyword_result = self.classify_with_keywords(description)
            if keyword_result:
                return keyword_result

            return ClassificationResult(
                category=ApplicationCategory.OTHER,
                confidence=0.1,
            )

    def _extract_dwelling_count(self, description: str) -> Optional[int]:
        """Extract dwelling count from description."""
        patterns = [
            r"(\d+)\s*(?:unit|dwelling|apartment|residence|townhouse)s?",
            r"(\d+)\s*(?:lot|storey)\s+(?:unit|dwelling|apartment|residence)",
            r"(?:construction of|erect|build)\s*(\d+)\s*(?:unit|dwelling)",
        ]

        for pattern in patterns:
            match = re.search(pattern, description.lower())
            if match:
                try:
                    count = int(match.group(1))
                    if 1 <= count <= 1000:  # Sanity check
                        return count
                except ValueError:
                    pass

        # Check for "dual occupancy" = 2 dwellings
        if "dual occupancy" in description.lower():
            return 2

        return None

    def _extract_lot_count(self, description: str) -> Optional[int]:
        """Extract lot count from description."""
        patterns = [
            r"(\d+)\s*(?:lot|allotment)s?",
            r"subdivision\s+(?:into|of|creating)\s+(\d+)",
            r"create\s+(\d+)\s+(?:lot|allotment)",
        ]

        for pattern in patterns:
            match = re.search(pattern, description.lower())
            if match:
                try:
                    count = int(match.group(1))
                    if 2 <= count <= 500:  # Subdivisions need at least 2 lots
                        return count
                except ValueError:
                    pass

        return None

    def _extract_storeys(self, description: str) -> Optional[int]:
        """Extract number of storeys from description."""
        patterns = [
            r"(\d+)\s*(?:storey|story|level)s?",
            r"(\d+)\s*(?:-|–)\s*(?:storey|story|level)",
        ]

        for pattern in patterns:
            match = re.search(pattern, description.lower())
            if match:
                try:
                    count = int(match.group(1))
                    if 1 <= count <= 100:  # Sanity check
                        return count
                except ValueError:
                    pass

        # Common terms
        if "single storey" in description.lower():
            return 1
        if "two storey" in description.lower() or "double storey" in description.lower():
            return 2
        if "three storey" in description.lower():
            return 3

        return None

    def _infer_application_type(self, description: str) -> Optional[ApplicationType]:
        """Infer application type from description."""
        desc_lower = description.lower()

        if any(kw in desc_lower for kw in ["modification", "s96", "section 96", "s4.55", "section 4.55"]):
            return ApplicationType.MODIFICATION
        if any(kw in desc_lower for kw in ["subdivision", "subdivide", "land division"]):
            return ApplicationType.SUBDIVISION
        if any(kw in desc_lower for kw in ["complying development", "cdc"]):
            return ApplicationType.COMPLYING_DEVELOPMENT
        if any(kw in desc_lower for kw in ["construction certificate", "cc"]):
            return ApplicationType.CONSTRUCTION_CERTIFICATE

        return ApplicationType.DEVELOPMENT_APPLICATION

    async def classify_batch(
        self,
        descriptions: list[str],
        use_ai: bool = True,
    ) -> list[ClassificationResult]:
        """Classify multiple descriptions."""
        results = []
        for desc in descriptions:
            result = await self.classify(desc, use_ai=use_ai)
            results.append(result)
        return results
