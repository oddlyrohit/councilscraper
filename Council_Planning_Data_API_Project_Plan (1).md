# Council Planning Data Aggregation API
## Project Plan & Technical Specification

**Version:** 1.0  
**Date:** December 2025  
**Author:** Rohit  

---

## Executive Summary

This document outlines the plan to build a comprehensive API that aggregates Development Application (DA) data from Australian local councils into a single, unified, commercially licensable dataset.

**Key Metrics:**
- Target: 200 councils covering ~90% of Australian population
- Estimated records: 2-5 million DAs

---

## Table of Contents

1. [Top 200 Australian Councils by Population](#1-top-200-australian-councils-by-population)
2. [Field Mapper Implementation](#2-field-mapper-implementation)
3. [Orchestrator Architecture](#3-orchestrator-architecture)
4. [AI-Assisted Scraper Generation](#4-ai-assisted-scraper-generation)
5. [Database Schema](#5-database-schema)
6. [API Specification](#6-api-specification)
7. [Development Roadmap](#7-development-roadmap)
8. [Cost Estimates](#8-cost-estimates)
9. [Revenue Model](#9-revenue-model)
10. [Risk Assessment](#10-risk-assessment)

---

## 1. Top 200 Australian Councils by Population

### Population Coverage Analysis

| Tier | Councils | Population Covered | Cumulative % |
|------|----------|-------------------|--------------|
| Top 50 | 50 | ~16.5M | ~61% |
| Top 100 | 100 | ~21M | ~77% |
| Top 150 | 150 | ~23.5M | ~87% |
| Top 200 | 200 | ~24.5M | ~90% |

### Complete Council List (Ranked by Population - June 2024)

#### Tier 1: Major Metro Councils (1-50) - Priority 1

| Rank | Council Name | State | Population | Metro Area |
|------|--------------|-------|------------|------------|
| 1 | Brisbane City Council | QLD | 1,350,000 | Brisbane |
| 2 | Gold Coast City Council | QLD | 640,000 | Gold Coast |
| 3 | Blacktown City Council | NSW | 415,000 | Sydney |
| 4 | Moreton Bay Regional Council | QLD | 510,000 | Brisbane |
| 5 | Canterbury-Bankstown Council | NSW | 380,000 | Sydney |
| 6 | City of Casey | VIC | 380,000 | Melbourne |
| 7 | Central Coast Council | NSW | 350,000 | Central Coast |
| 8 | Wyndham City Council | VIC | 320,000 | Melbourne |
| 9 | Logan City Council | QLD | 360,000 | Brisbane |
| 10 | Sunshine Coast Council | QLD | 360,000 | Sunshine Coast |
| 11 | City of Parramatta | NSW | 270,000 | Sydney |
| 12 | Penrith City Council | NSW | 230,000 | Sydney |
| 13 | City of Sydney | NSW | 220,000 | Sydney |
| 14 | Liverpool City Council | NSW | 240,000 | Sydney |
| 15 | Fairfield City Council | NSW | 220,000 | Sydney |
| 16 | City of Greater Geelong | VIC | 280,000 | Geelong |
| 17 | Inner West Council | NSW | 200,000 | Sydney |
| 18 | The Hills Shire Council | NSW | 200,000 | Sydney |
| 19 | Cumberland City Council | NSW | 250,000 | Sydney |
| 20 | Northern Beaches Council | NSW | 275,000 | Sydney |
| 21 | City of Stirling | WA | 240,000 | Perth |
| 22 | City of Wanneroo | WA | 250,000 | Perth |
| 23 | Ipswich City Council | QLD | 250,000 | Brisbane |
| 24 | City of Hume | VIC | 250,000 | Melbourne |
| 25 | City of Whittlesea | VIC | 250,000 | Melbourne |
| 26 | Sutherland Shire Council | NSW | 240,000 | Sydney |
| 27 | Randwick City Council | NSW | 160,000 | Sydney |
| 28 | City of Brimbank | VIC | 220,000 | Melbourne |
| 29 | Lake Macquarie City Council | NSW | 215,000 | Newcastle |
| 30 | City of Monash | VIC | 210,000 | Melbourne |
| 31 | City of Greater Dandenong | VIC | 180,000 | Melbourne |
| 32 | Campbelltown City Council | NSW | 185,000 | Sydney |
| 33 | City of Joondalup | WA | 165,000 | Perth |
| 34 | Hornsby Shire Council | NSW | 160,000 | Sydney |
| 35 | City of Melton | VIC | 200,000 | Melbourne |
| 36 | Camden Council | NSW | 135,000 | Sydney |
| 37 | City of Knox | VIC | 170,000 | Melbourne |
| 38 | City of Rockingham | WA | 145,000 | Perth |
| 39 | City of Boroondara | VIC | 185,000 | Melbourne |
| 40 | City of Darebin | VIC | 170,000 | Melbourne |
| 41 | Newcastle City Council | NSW | 170,000 | Newcastle |
| 42 | Georges River Council | NSW | 160,000 | Sydney |
| 43 | City of Cockburn | WA | 125,000 | Perth |
| 44 | City of Moreland (Merri-bek) | VIC | 185,000 | Melbourne |
| 45 | Redland City Council | QLD | 165,000 | Brisbane |
| 46 | Townsville City Council | QLD | 200,000 | Townsville |
| 47 | City of Gosnells | WA | 130,000 | Perth |
| 48 | City of Moonee Valley | VIC | 135,000 | Melbourne |
| 49 | Wollongong City Council | NSW | 220,000 | Wollongong |
| 50 | Bayside Council | NSW | 180,000 | Sydney |

#### Tier 2: Secondary Metro & Regional Cities (51-100) - Priority 2

| Rank | Council Name | State | Population | Metro Area |
|------|--------------|-------|------------|------------|
| 51 | City of Ballarat | VIC | 120,000 | Ballarat |
| 52 | City of Bendigo | VIC | 120,000 | Bendigo |
| 53 | City of Canning | WA | 105,000 | Perth |
| 54 | City of Frankston | VIC | 145,000 | Melbourne |
| 55 | Cairns Regional Council | QLD | 170,000 | Cairns |
| 56 | Toowoomba Regional Council | QLD | 180,000 | Toowoomba |
| 57 | Ku-ring-gai Council | NSW | 130,000 | Sydney |
| 58 | City of Adelaide | SA | 26,000 | Adelaide |
| 59 | City of Charles Sturt | SA | 120,000 | Adelaide |
| 60 | City of Onkaparinga | SA | 175,000 | Adelaide |
| 61 | City of Salisbury | SA | 145,000 | Adelaide |
| 62 | City of Tea Tree Gully | SA | 105,000 | Adelaide |
| 63 | City of Port Adelaide Enfield | SA | 130,000 | Adelaide |
| 64 | City of Marion | SA | 95,000 | Adelaide |
| 65 | City of Holdfast Bay | SA | 40,000 | Adelaide |
| 66 | City of Mitcham | SA | 70,000 | Adelaide |
| 67 | Bundaberg Regional Council | QLD | 100,000 | Bundaberg |
| 68 | Mackay Regional Council | QLD | 125,000 | Mackay |
| 69 | Rockhampton Regional Council | QLD | 90,000 | Rockhampton |
| 70 | Gladstone Regional Council | QLD | 65,000 | Gladstone |
| 71 | Fraser Coast Regional Council | QLD | 110,000 | Hervey Bay |
| 72 | City of Hobart | TAS | 57,000 | Hobart |
| 73 | City of Launceston | TAS | 70,000 | Launceston |
| 74 | Clarence City Council | TAS | 60,000 | Hobart |
| 75 | Glenorchy City Council | TAS | 50,000 | Hobart |
| 76 | Kingborough Council | TAS | 42,000 | Hobart |
| 77 | City of Darwin | NT | 90,000 | Darwin |
| 78 | Palmerston City Council | NT | 40,000 | Darwin |
| 79 | Litchfield Council | NT | 25,000 | Darwin |
| 80 | Alice Springs Town Council | NT | 25,000 | Alice Springs |
| 81 | City of Swan | WA | 165,000 | Perth |
| 82 | City of Belmont | WA | 45,000 | Perth |
| 83 | City of Melville | WA | 105,000 | Perth |
| 84 | City of Bayswater | WA | 70,000 | Perth |
| 85 | City of South Perth | WA | 48,000 | Perth |
| 86 | City of Vincent | WA | 38,000 | Perth |
| 87 | City of Fremantle | WA | 32,000 | Perth |
| 88 | Town of Victoria Park | WA | 40,000 | Perth |
| 89 | City of Armadale | WA | 105,000 | Perth |
| 90 | City of Mandurah | WA | 95,000 | Perth |
| 91 | City of Bunbury | WA | 35,000 | Bunbury |
| 92 | City of Greater Geraldton | WA | 42,000 | Geraldton |
| 93 | City of Kalgoorlie-Boulder | WA | 32,000 | Kalgoorlie |
| 94 | City of Albany | WA | 40,000 | Albany |
| 95 | Albury City Council | NSW | 55,000 | Albury-Wodonga |
| 96 | City of Wodonga | VIC | 45,000 | Albury-Wodonga |
| 97 | City of Shepparton | VIC | 70,000 | Shepparton |
| 98 | City of Mildura | VIC | 58,000 | Mildura |
| 99 | City of Warrnambool | VIC | 36,000 | Warrnambool |
| 100 | City of Horsham | VIC | 20,000 | Horsham |

#### Tier 3: Regional & Outer Metro (101-150) - Priority 3

| Rank | Council Name | State | Population |
|------|--------------|-------|------------|
| 101 | Wagga Wagga City Council | NSW | 70,000 |
| 102 | Tamworth Regional Council | NSW | 65,000 |
| 103 | Orange City Council | NSW | 45,000 |
| 104 | Dubbo Regional Council | NSW | 55,000 |
| 105 | Bathurst Regional Council | NSW | 45,000 |
| 106 | Port Macquarie-Hastings Council | NSW | 90,000 |
| 107 | Coffs Harbour City Council | NSW | 80,000 |
| 108 | Lismore City Council | NSW | 45,000 |
| 109 | Tweed Shire Council | NSW | 100,000 |
| 110 | Byron Shire Council | NSW | 37,000 |
| 111 | Ballina Shire Council | NSW | 45,000 |
| 112 | Richmond Valley Council | NSW | 25,000 |
| 113 | Clarence Valley Council | NSW | 55,000 |
| 114 | Shoalhaven City Council | NSW | 110,000 |
| 115 | Shellharbour City Council | NSW | 80,000 |
| 116 | Kiama Municipal Council | NSW | 25,000 |
| 117 | Wingecarribee Shire Council | NSW | 55,000 |
| 118 | Wollondilly Shire Council | NSW | 55,000 |
| 119 | Blue Mountains City Council | NSW | 80,000 |
| 120 | Hawkesbury City Council | NSW | 70,000 |
| 121 | Maitland City Council | NSW | 95,000 |
| 122 | Cessnock City Council | NSW | 60,000 |
| 123 | Port Stephens Council | NSW | 75,000 |
| 124 | Singleton Council | NSW | 25,000 |
| 125 | Muswellbrook Shire Council | NSW | 18,000 |
| 126 | Upper Hunter Shire Council | NSW | 15,000 |
| 127 | Queanbeyan-Palerang Regional Council | NSW | 65,000 |
| 128 | Yass Valley Council | NSW | 18,000 |
| 129 | Goulburn Mulwaree Council | NSW | 32,000 |
| 130 | Snowy Monaro Regional Council | NSW | 22,000 |
| 131 | Bega Valley Shire Council | NSW | 35,000 |
| 132 | Eurobodalla Shire Council | NSW | 40,000 |
| 133 | Griffith City Council | NSW | 27,000 |
| 134 | Leeton Shire Council | NSW | 12,000 |
| 135 | Narrandera Shire Council | NSW | 6,500 |
| 136 | City of Latrobe | VIC | 80,000 |
| 137 | Bass Coast Shire Council | VIC | 40,000 |
| 138 | Baw Baw Shire Council | VIC | 58,000 |
| 139 | South Gippsland Shire Council | VIC | 30,000 |
| 140 | East Gippsland Shire Council | VIC | 48,000 |
| 141 | Wellington Shire Council | VIC | 45,000 |
| 142 | Surf Coast Shire Council | VIC | 38,000 |
| 143 | Colac Otway Shire Council | VIC | 22,000 |
| 144 | Corangamite Shire Council | VIC | 16,000 |
| 145 | Moyne Shire Council | VIC | 17,000 |
| 146 | Glenelg Shire Council | VIC | 20,000 |
| 147 | Southern Grampians Shire Council | VIC | 17,000 |
| 148 | Ararat Rural City Council | VIC | 12,000 |
| 149 | Pyrenees Shire Council | VIC | 7,500 |
| 150 | Hepburn Shire Council | VIC | 16,000 |

#### Tier 4: Additional Regional (151-200) - Priority 4

| Rank | Council Name | State | Population |
|------|--------------|-------|------------|
| 151 | Macedon Ranges Shire Council | VIC | 55,000 |
| 152 | Mount Alexander Shire Council | VIC | 20,000 |
| 153 | Central Goldfields Shire Council | VIC | 14,000 |
| 154 | Loddon Shire Council | VIC | 8,000 |
| 155 | Campaspe Shire Council | VIC | 38,000 |
| 156 | Moira Shire Council | VIC | 30,000 |
| 157 | Benalla Rural City Council | VIC | 15,000 |
| 158 | Wangaratta Rural City Council | VIC | 30,000 |
| 159 | Indigo Shire Council | VIC | 18,000 |
| 160 | Alpine Shire Council | VIC | 13,000 |
| 161 | Mansfield Shire Council | VIC | 10,000 |
| 162 | Murrindindi Shire Council | VIC | 15,000 |
| 163 | Mitchell Shire Council | VIC | 55,000 |
| 164 | Strathbogie Shire Council | VIC | 11,000 |
| 165 | City of Playford | SA | 100,000 |
| 166 | City of Campbelltown (SA) | SA | 55,000 |
| 167 | City of Norwood Payneham St Peters | SA | 38,000 |
| 168 | City of Burnside | SA | 47,000 |
| 169 | City of Unley | SA | 40,000 |
| 170 | City of Prospect | SA | 22,000 |
| 171 | City of West Torrens | SA | 62,000 |
| 172 | Mount Barker District Council | SA | 42,000 |
| 173 | Adelaide Hills Council | SA | 42,000 |
| 174 | City of Victor Harbor | SA | 17,000 |
| 175 | Alexandrina Council | SA | 30,000 |
| 176 | Murray Bridge Council | SA | 24,000 |
| 177 | Barossa Council | SA | 27,000 |
| 178 | Light Regional Council | SA | 17,000 |
| 179 | Town of Gawler | SA | 27,000 |
| 180 | City of Port Lincoln | SA | 16,000 |
| 181 | City of Whyalla | SA | 22,000 |
| 182 | City of Mount Gambier | SA | 28,000 |
| 183 | Scenic Rim Regional Council | QLD | 45,000 |
| 184 | Lockyer Valley Regional Council | QLD | 45,000 |
| 185 | Somerset Regional Council | QLD | 28,000 |
| 186 | South Burnett Regional Council | QLD | 32,000 |
| 187 | Gympie Regional Council | QLD | 55,000 |
| 188 | Noosa Shire Council | QLD | 60,000 |
| 189 | Douglas Shire Council | QLD | 12,000 |
| 190 | Tablelands Regional Council | QLD | 27,000 |
| 191 | Cassowary Coast Regional Council | QLD | 30,000 |
| 192 | Hinchinbrook Shire Council | QLD | 12,000 |
| 193 | Burdekin Shire Council | QLD | 18,000 |
| 194 | Charters Towers Regional Council | QLD | 13,000 |
| 195 | Isaac Regional Council | QLD | 22,000 |
| 196 | Central Highlands Regional Council | QLD | 30,000 |
| 197 | Banana Shire Council | QLD | 15,000 |
| 198 | Livingstone Shire Council | QLD | 40,000 |
| 199 | Central Queensland Regional Council | QLD | 12,000 |
| 200 | Western Downs Regional Council | QLD | 35,000 |

### State Summary

| State | Councils in Top 200 | Population Covered |
|-------|--------------------|--------------------|
| NSW | 65 | ~8.2M |
| VIC | 55 | ~6.5M |
| QLD | 35 | ~5.2M |
| WA | 22 | ~2.4M |
| SA | 20 | ~1.7M |
| TAS | 5 | ~280K |
| NT | 4 | ~180K |
| **Total** | **200** | **~24.5M (~90%)** |

---

## 2. Field Mapper Implementation

### Master Schema Definition

```python
# ============================================================================
# FILE: schemas/master_schema.py
# PURPOSE: Define the unified data schema for all council DAs
# ============================================================================

from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime, date
from enum import Enum

# ----------------------------------------------------------------------------
# ENUMS - Standardized Categories
# ----------------------------------------------------------------------------

class ApplicationType(Enum):
    DEVELOPMENT_APPLICATION = "development_application"
    COMPLYING_DEVELOPMENT = "complying_development"
    CONSTRUCTION_CERTIFICATE = "construction_certificate"
    SUBDIVISION = "subdivision"
    MODIFICATION = "modification"
    REVIEW = "review"
    OTHER = "other"

class ApplicationCategory(Enum):
    RESIDENTIAL_SINGLE = "residential_single"
    RESIDENTIAL_MULTI = "residential_multi"
    RESIDENTIAL_SUBDIVISION = "residential_subdivision"
    COMMERCIAL_RETAIL = "commercial_retail"
    COMMERCIAL_OFFICE = "commercial_office"
    INDUSTRIAL = "industrial"
    MIXED_USE = "mixed_use"
    INFRASTRUCTURE = "infrastructure"
    DEMOLITION = "demolition"
    CHANGE_OF_USE = "change_of_use"
    SIGNAGE = "signage"
    TREE_REMOVAL = "tree_removal"
    OTHER = "other"

class ApplicationStatus(Enum):
    LODGED = "lodged"
    UNDER_ASSESSMENT = "under_assessment"
    ON_EXHIBITION = "on_exhibition"
    ADDITIONAL_INFO_REQUIRED = "additional_info_required"
    REFERRED = "referred"
    DETERMINED = "determined"
    APPROVED = "approved"
    REFUSED = "refused"
    WITHDRAWN = "withdrawn"
    LAPSED = "lapsed"
    APPEALED = "appealed"

class Decision(Enum):
    APPROVED = "approved"
    APPROVED_WITH_CONDITIONS = "approved_with_conditions"
    REFUSED = "refused"
    DEFERRED = "deferred"
    WITHDRAWN = "withdrawn"
    NOT_DETERMINED = "not_determined"

# ----------------------------------------------------------------------------
# CORE DATA CLASSES
# ----------------------------------------------------------------------------

@dataclass
class CouncilInfo:
    """Council/LGA information"""
    code: str                    # e.g., "BRISBANE", "SYDNEY"
    name: str                    # e.g., "Brisbane City Council"
    state: str                   # e.g., "QLD", "NSW"
    lga_code: str               # ABS LGA code
    portal_url: str             # Planning portal URL
    portal_type: str            # e.g., "eplanning", "masterview", "custom"

@dataclass
class PropertyInfo:
    """Property/site information"""
    address: str                 # Full street address
    suburb: str                  # Suburb name
    postcode: str               # Postcode
    state: str                  # State abbreviation
    lot_plan: Optional[str]     # Lot/Plan reference
    latitude: Optional[float]   # Geocoded latitude
    longitude: Optional[float]  # Geocoded longitude
    land_area_sqm: Optional[float]  # Site area

@dataclass
class ApplicationDates:
    """Key dates in the application lifecycle"""
    lodged: Optional[date]
    validated: Optional[date]
    exhibition_start: Optional[date]
    exhibition_end: Optional[date]
    determined: Optional[date]
    approved: Optional[date]
    commenced: Optional[date]
    completed: Optional[date]

@dataclass
class ApplicantInfo:
    """Applicant/owner details"""
    applicant_name: Optional[str]
    applicant_type: Optional[str]  # "individual", "company", "government"
    owner_name: Optional[str]
    architect: Optional[str]
    builder: Optional[str]

@dataclass
class DevelopmentDetails:
    """Details of proposed development"""
    estimated_cost: Optional[float]
    dwelling_count: Optional[int]
    lot_count: Optional[int]        # For subdivisions
    floor_area_sqm: Optional[float]
    storeys: Optional[int]
    car_spaces: Optional[int]
    
@dataclass
class Document:
    """Associated document"""
    name: str
    url: str
    doc_type: str               # "plans", "statement", "report", etc.
    uploaded_date: Optional[date]

# ----------------------------------------------------------------------------
# MAIN DA RECORD
# ----------------------------------------------------------------------------

@dataclass
class DevelopmentApplication:
    """
    Unified Development Application record.
    This is the master schema that all council data maps to.
    """
    # Identifiers
    id: str                      # Our internal ID (UUID)
    da_number: str               # Council's DA reference number
    council: CouncilInfo
    
    # Property
    property: PropertyInfo
    
    # Application details
    application_type: ApplicationType
    category: ApplicationCategory
    subcategory: Optional[str]
    description: str             # Full description of proposed works
    
    # Status
    status: ApplicationStatus
    decision: Optional[Decision]
    decision_date: Optional[date]
    conditions_count: Optional[int]
    
    # Dates
    dates: ApplicationDates
    
    # Parties
    applicant: ApplicantInfo
    
    # Development details
    details: DevelopmentDetails
    
    # Documents
    documents: List[Document]
    
    # Metadata
    source_url: str              # URL where data was scraped from
    scraped_at: datetime
    updated_at: datetime
    data_quality_score: float    # 0.0-1.0 confidence in data
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "da_number": self.da_number,
            "council": {
                "code": self.council.code,
                "name": self.council.name,
                "state": self.council.state
            },
            "property": {
                "address": self.property.address,
                "suburb": self.property.suburb,
                "postcode": self.property.postcode,
                "state": self.property.state,
                "lot_plan": self.property.lot_plan,
                "coordinates": {
                    "lat": self.property.latitude,
                    "lng": self.property.longitude
                } if self.property.latitude else None,
                "land_area_sqm": self.property.land_area_sqm
            },
            "application": {
                "type": self.application_type.value,
                "category": self.category.value,
                "subcategory": self.subcategory,
                "description": self.description
            },
            "status": self.status.value,
            "decision": self.decision.value if self.decision else None,
            "dates": {
                "lodged": self.dates.lodged.isoformat() if self.dates.lodged else None,
                "exhibition_start": self.dates.exhibition_start.isoformat() if self.dates.exhibition_start else None,
                "exhibition_end": self.dates.exhibition_end.isoformat() if self.dates.exhibition_end else None,
                "determined": self.dates.determined.isoformat() if self.dates.determined else None
            },
            "applicant": {
                "name": self.applicant.applicant_name,
                "type": self.applicant.applicant_type
            },
            "details": {
                "estimated_cost": self.details.estimated_cost,
                "dwelling_count": self.details.dwelling_count,
                "lot_count": self.details.lot_count,
                "floor_area_sqm": self.details.floor_area_sqm,
                "storeys": self.details.storeys,
                "car_spaces": self.details.car_spaces
            },
            "documents": [
                {"name": d.name, "url": d.url, "type": d.doc_type}
                for d in self.documents
            ],
            "metadata": {
                "source_url": self.source_url,
                "scraped_at": self.scraped_at.isoformat(),
                "updated_at": self.updated_at.isoformat(),
                "data_quality_score": self.data_quality_score
            }
        }
```

### AI-Powered Field Mapper

```python
# ============================================================================
# FILE: mappers/ai_field_mapper.py
# PURPOSE: Use LLM to map council-specific fields to master schema
# ============================================================================

import json
import hashlib
from typing import Dict, Any, Optional, List
from anthropic import Anthropic
from schemas.master_schema import (
    DevelopmentApplication, ApplicationType, ApplicationCategory,
    ApplicationStatus, Decision
)

# ----------------------------------------------------------------------------
# CONFIGURATION
# ----------------------------------------------------------------------------

ANTHROPIC_MODEL = "claude-sonnet-4-20250514"

# ----------------------------------------------------------------------------
# FIELD MAPPING CACHE
# ----------------------------------------------------------------------------

class FieldMappingCache:
    """
    Cache field mappings to avoid repeated LLM calls for same council.
    Once a council's mapping is learned, it's stored and reused.
    """
    
    def __init__(self, cache_path: str = "mappings_cache.json"):
        self.cache_path = cache_path
        self.mappings: Dict[str, Dict] = self._load_cache()
    
    def _load_cache(self) -> Dict:
        try:
            with open(self.cache_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    def save_cache(self):
        with open(self.cache_path, 'w') as f:
            json.dump(self.mappings, f, indent=2)
    
    def get_mapping(self, council_code: str) -> Optional[Dict]:
        return self.mappings.get(council_code)
    
    def set_mapping(self, council_code: str, mapping: Dict):
        self.mappings[council_code] = mapping
        self.save_cache()

# ----------------------------------------------------------------------------
# AI FIELD MAPPER
# ----------------------------------------------------------------------------

class AIFieldMapper:
    """
    Uses Claude to intelligently map council-specific field names
    to the master schema.
    """
    
    def __init__(self):
        self.client = Anthropic()
        self.cache = FieldMappingCache()
        
        # Master schema field definitions for the LLM
        self.schema_definitions = """
        MASTER SCHEMA FIELDS:
        
        da_number: Unique application identifier (e.g., "DA-2025-1234", "2025/0456")
        address: Full property street address
        suburb: Suburb/locality name
        postcode: 4-digit postcode
        lot_plan: Lot/Plan or Title reference (e.g., "Lot 1 DP123456")
        
        application_type: One of:
            - development_application
            - complying_development  
            - construction_certificate
            - subdivision
            - modification
            - review
            - other
            
        category: One of:
            - residential_single (single house)
            - residential_multi (units, apartments, townhouses)
            - residential_subdivision (land division)
            - commercial_retail (shops, restaurants)
            - commercial_office (office buildings)
            - industrial (warehouses, factories)
            - mixed_use (combined residential/commercial)
            - infrastructure (roads, utilities)
            - demolition
            - change_of_use
            - signage
            - tree_removal
            - other
            
        description: Full text description of proposed works
        
        status: One of:
            - lodged
            - under_assessment
            - on_exhibition
            - additional_info_required
            - referred
            - determined
            - approved
            - refused
            - withdrawn
            - lapsed
            - appealed
            
        decision: One of:
            - approved
            - approved_with_conditions
            - refused
            - deferred
            - withdrawn
            - not_determined
            
        lodged_date: Date application was submitted
        exhibition_start: Start of public notification period
        exhibition_end: End of public notification period
        determined_date: Date decision was made
        
        estimated_cost: Dollar value of proposed works
        dwelling_count: Number of dwellings in proposal
        lot_count: Number of lots (for subdivisions)
        storeys: Number of storeys/floors
        
        applicant_name: Name of applicant
        owner_name: Name of property owner
        """
    
    def learn_mapping(self, council_code: str, sample_data: List[Dict]) -> Dict:
        """
        Learn the field mapping for a new council by analyzing sample data.
        
        Args:
            council_code: Unique council identifier
            sample_data: List of 3-5 sample records from the council
            
        Returns:
            Field mapping dictionary
        """
        
        # Check cache first
        cached = self.cache.get_mapping(council_code)
        if cached:
            return cached
        
        prompt = f"""
        Analyze these sample records from {council_code} council and create a field mapping
        to our master schema.
        
        SAMPLE DATA:
        {json.dumps(sample_data[:5], indent=2)}
        
        {self.schema_definitions}
        
        Create a mapping from the council's field names to our master schema fields.
        For each master schema field, identify which council field(s) contain that data.
        
        Return ONLY a JSON object in this exact format:
        {{
            "da_number": "council_field_name_or_null",
            "address": "council_field_name_or_null",
            "suburb": "council_field_name_or_null",
            "postcode": "council_field_name_or_null",
            "lot_plan": "council_field_name_or_null",
            "application_type": "council_field_name_or_null",
            "description": "council_field_name_or_null",
            "status": "council_field_name_or_null",
            "lodged_date": "council_field_name_or_null",
            "exhibition_start": "council_field_name_or_null",
            "exhibition_end": "council_field_name_or_null",
            "determined_date": "council_field_name_or_null",
            "estimated_cost": "council_field_name_or_null",
            "dwelling_count": "council_field_name_or_null",
            "applicant_name": "council_field_name_or_null",
            "status_values": {{
                "council_status_1": "our_status",
                "council_status_2": "our_status"
            }}
        }}
        
        Notes:
        - Use null if field doesn't exist in council data
        - For compound fields (e.g., address contains suburb), note with "address+suburb"
        - Include status_values mapping for status field translations
        """
        
        response = self.client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        # Parse response
        response_text = response.content[0].text
        
        # Extract JSON from response
        try:
            # Handle markdown code blocks
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                json_str = response_text.split("```")[1].split("```")[0]
            else:
                json_str = response_text
                
            mapping = json.loads(json_str.strip())
            
            # Cache the mapping
            self.cache.set_mapping(council_code, mapping)
            
            return mapping
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse mapping response: {e}")
    
    def apply_mapping(self, council_code: str, raw_record: Dict) -> Dict:
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
            raise ValueError(f"No mapping found for {council_code}. Call learn_mapping first.")
        
        normalized = {}
        
        for master_field, council_field in mapping.items():
            if council_field is None:
                normalized[master_field] = None
                continue
                
            if master_field == "status_values":
                # Skip - this is metadata, not a field
                continue
                
            # Handle compound fields
            if "+" in str(council_field):
                fields = council_field.split("+")
                values = [raw_record.get(f, "") for f in fields]
                normalized[master_field] = " ".join(filter(None, values))
            else:
                normalized[master_field] = raw_record.get(council_field)
        
        # Apply status mapping if present
        if "status_values" in mapping and normalized.get("status"):
            status_map = mapping["status_values"]
            raw_status = normalized["status"]
            normalized["status"] = status_map.get(raw_status, raw_status)
        
        return normalized

# ----------------------------------------------------------------------------
# CATEGORY CLASSIFIER
# ----------------------------------------------------------------------------

class CategoryClassifier:
    """
    Uses LLM to classify DA descriptions into standardized categories.
    """
    
    def __init__(self):
        self.client = Anthropic()
        self.classification_cache: Dict[str, Dict] = {}
    
    def _get_cache_key(self, description: str) -> str:
        """Generate cache key from description"""
        return hashlib.md5(description.lower().strip().encode()).hexdigest()[:16]
    
    def classify(self, description: str) -> Dict:
        """
        Classify a DA description into category and extract details.
        
        Args:
            description: Free-text description of proposed works
            
        Returns:
            Dictionary with category, subcategory, dwelling_count, etc.
        """
        
        # Check cache
        cache_key = self._get_cache_key(description)
        if cache_key in self.classification_cache:
            return self.classification_cache[cache_key]
        
        prompt = f"""
        Classify this development application description:
        
        "{description}"
        
        Return JSON with:
        {{
            "category": "one of: residential_single, residential_multi, residential_subdivision, commercial_retail, commercial_office, industrial, mixed_use, infrastructure, demolition, change_of_use, signage, tree_removal, other",
            "subcategory": "more specific description if applicable, else null",
            "dwelling_count": number or null,
            "lot_count": number or null (for subdivisions),
            "storeys": number or null,
            "is_new_build": true/false,
            "involves_demolition": true/false,
            "confidence": 0.0-1.0
        }}
        
        Return ONLY the JSON, no other text.
        """
        
        response = self.client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )
        
        try:
            result = json.loads(response.content[0].text.strip())
            self.classification_cache[cache_key] = result
            return result
        except json.JSONDecodeError:
            return {
                "category": "other",
                "subcategory": None,
                "dwelling_count": None,
                "lot_count": None,
                "storeys": None,
                "is_new_build": None,
                "involves_demolition": None,
                "confidence": 0.0
            }

# ----------------------------------------------------------------------------
# USAGE EXAMPLE
# ----------------------------------------------------------------------------

if __name__ == "__main__":
    # Example usage
    mapper = AIFieldMapper()
    classifier = CategoryClassifier()
    
    # Sample data from a council
    sample_brisbane = [
        {
            "ApplicationNumber": "A006234567",
            "PropertyAddress": "123 Queen Street, BRISBANE CITY QLD 4000",
            "ProposalDescription": "Material change of use for 45 unit residential development",
            "ApplicationStatus": "Decision Made",
            "LodgementDate": "2025-01-15",
            "DecisionDate": "2025-03-20",
            "EstCost": "$15,000,000"
        }
    ]
    
    # Learn the mapping
    mapping = mapper.learn_mapping("BRISBANE", sample_brisbane)
    print("Learned mapping:", json.dumps(mapping, indent=2))
    
    # Apply mapping to transform data
    normalized = mapper.apply_mapping("BRISBANE", sample_brisbane[0])
    print("Normalized record:", json.dumps(normalized, indent=2))
    
    # Classify the description
    classification = classifier.classify(
        "Material change of use for 45 unit residential development"
    )
    print("Classification:", json.dumps(classification, indent=2))
```

---

## 3. Orchestrator Architecture

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           ORCHESTRATOR LAYER                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    SCHEDULER (Celery + Redis)                        │   │
│  │                                                                       │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                  │   │
│  │  │ Daily Jobs  │  │ Hourly Jobs │  │ On-Demand   │                  │   │
│  │  │ (Full sync) │  │ (Hot areas) │  │ (API calls) │                  │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘                  │   │
│  │                                                                       │   │
│  └───────────────────────────┬───────────────────────────────────────────┘   │
│                              │                                              │
│                              ▼                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    SCRAPER MANAGER                                   │   │
│  │                                                                       │   │
│  │  ┌──────────────────────────────────────────────────────────────┐   │   │
│  │  │                   ADAPTER REGISTRY                            │   │   │
│  │  │                                                                │   │   │
│  │  │  councils/                                                     │   │   │
│  │  │  ├── nsw/                                                      │   │   │
│  │  │  │   ├── sydney.py                                            │   │   │
│  │  │  │   ├── blacktown.py                                         │   │   │
│  │  │  │   └── ...                                                  │   │   │
│  │  │  ├── vic/                                                      │   │   │
│  │  │  │   ├── melbourne.py                                         │   │   │
│  │  │  │   └── ...                                                  │   │   │
│  │  │  ├── qld/                                                      │   │   │
│  │  │  │   ├── brisbane.py                                          │   │   │
│  │  │  │   └── ...                                                  │   │   │
│  │  │  └── ...                                                       │   │   │
│  │  │                                                                │   │   │
│  │  │  Each adapter implements: CouncilAdapter interface             │   │   │
│  │  │  - scrape_active() → List[RawDA]                              │   │   │
│  │  │  - scrape_historical(start, end) → List[RawDA]                │   │   │
│  │  │  - get_portal_status() → PortalHealth                         │   │   │
│  │  └──────────────────────────────────────────────────────────────┘   │   │
│  │                                                                       │   │
│  │  ┌──────────────────────────────────────────────────────────────┐   │   │
│  │  │                   PROXY MANAGER                               │   │   │
│  │  │                                                                │   │   │
│  │  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │   │   │
│  │  │  │ Datacenter  │  │ Residential │  │ BrightData  │          │   │   │
│  │  │  │ Proxies     │  │ Proxies     │  │ (Fallback)  │          │   │   │
│  │  │  │ (Default)   │  │ (Protected) │  │ (Anti-bot)  │          │   │   │
│  │  │  └─────────────┘  └─────────────┘  └─────────────┘          │   │   │
│  │  │                                                                │   │   │
│  │  │  Auto-escalates: Datacenter → Residential → BrightData        │   │   │
│  │  └──────────────────────────────────────────────────────────────┘   │   │
│  │                                                                       │   │
│  └───────────────────────────┬───────────────────────────────────────────┘   │
│                              │                                              │
└──────────────────────────────┼──────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          PROCESSING LAYER                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐            │
│  │   RAW STORE     │  │   NORMALIZER    │  │   ENRICHMENT    │            │
│  │                 │  │                 │  │                 │            │
│  │  S3 Bucket      │  │  AI Field       │  │  - Geocoding    │            │
│  │  raw/{council}/ │──│  Mapper         │──│  - Category     │            │
│  │  {date}/        │  │  + Category     │  │  - Dedup        │            │
│  │  {batch}.json   │  │  Classifier     │  │  - Validation   │            │
│  │                 │  │                 │  │                 │            │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘            │
│                                                    │                       │
│                              ┌─────────────────────┘                       │
│                              ▼                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    DATA QUALITY LAYER                                │   │
│  │                                                                       │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                  │   │
│  │  │ Anomaly     │  │ Completeness│  │ Freshness   │                  │   │
│  │  │ Detection   │  │ Scoring     │  │ Tracking    │                  │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘                  │   │
│  │                                                                       │   │
│  │  AI-powered validation:                                              │   │
│  │  - Detects scraper breakage                                          │   │
│  │  - Flags suspicious data                                             │   │
│  │  - Triggers alerts                                                   │   │
│  │                                                                       │   │
│  └───────────────────────────┬───────────────────────────────────────────┘   │
│                              │                                              │
└──────────────────────────────┼──────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            DATA LAYER                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                PostgreSQL + PostGIS                                  │   │
│  │                                                                       │   │
│  │  Tables:                                                             │   │
│  │  ├── councils (200 rows)                                            │   │
│  │  ├── applications (2-5M rows)                                       │   │
│  │  ├── documents (10-20M rows)                                        │   │
│  │  ├── scrape_logs (audit trail)                                      │   │
│  │  └── field_mappings (AI learned)                                    │   │
│  │                                                                       │   │
│  │  Indexes:                                                            │   │
│  │  ├── GIST on coordinates (spatial queries)                          │   │
│  │  ├── GIN on description (full-text search)                          │   │
│  │  ├── B-tree on da_number, council_code, status                      │   │
│  │  └── BRIN on lodged_date (time-range queries)                       │   │
│  │                                                                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        Redis                                         │   │
│  │                                                                       │   │
│  │  ├── Rate limit counters per council                                │   │
│  │  ├── Scraper health metrics                                         │   │
│  │  ├── API response cache                                             │   │
│  │  └── Celery task queue                                              │   │
│  │                                                                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                             API LAYER                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    FastAPI Application                               │   │
│  │                                                                       │   │
│  │  REST Endpoints:                                                     │   │
│  │  ├── GET  /api/v1/applications                                      │   │
│  │  ├── GET  /api/v1/applications/{id}                                 │   │
│  │  ├── GET  /api/v1/applications/near                                 │   │
│  │  ├── GET  /api/v1/councils                                          │   │
│  │  ├── GET  /api/v1/councils/{code}/stats                             │   │
│  │  ├── GET  /api/v1/search                                            │   │
│  │  └── POST /api/v1/webhooks (new DA notifications)                   │   │
│  │                                                                       │   │
│  │  Features:                                                           │   │
│  │  ├── API key authentication                                         │   │
│  │  ├── Rate limiting (tiered by plan)                                 │   │
│  │  ├── Response caching                                               │   │
│  │  ├── Usage tracking & billing                                       │   │
│  │  └── OpenAPI documentation                                          │   │
│  │                                                                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Orchestrator Implementation

```python
# ============================================================================
# FILE: orchestrator/main.py
# PURPOSE: Central orchestration of scraping, processing, and data pipeline
# ============================================================================

import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from celery import Celery
from celery.schedules import crontab
import redis
import logging

from config import settings
from adapters.registry import AdapterRegistry
from mappers.ai_field_mapper import AIFieldMapper, CategoryClassifier
from processors.enrichment import GeocoderService, DeduplicationService
from processors.validation import DataQualityValidator
from storage.database import DatabaseManager
from storage.raw_store import RawDataStore
from monitoring.alerts import AlertManager

# ----------------------------------------------------------------------------
# CONFIGURATION
# ----------------------------------------------------------------------------

logger = logging.getLogger(__name__)

celery_app = Celery(
    'council_scraper',
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

redis_client = redis.from_url(settings.REDIS_URL)

# ----------------------------------------------------------------------------
# CORE COMPONENTS
# ----------------------------------------------------------------------------

class ScraperOrchestrator:
    """
    Central orchestrator that coordinates:
    - Scheduled scraping jobs
    - Data processing pipeline
    - Quality monitoring
    - Alert management
    """
    
    def __init__(self):
        self.adapter_registry = AdapterRegistry()
        self.field_mapper = AIFieldMapper()
        self.classifier = CategoryClassifier()
        self.geocoder = GeocoderService()
        self.deduplicator = DeduplicationService()
        self.validator = DataQualityValidator()
        self.db = DatabaseManager()
        self.raw_store = RawDataStore()
        self.alerts = AlertManager()
    
    # ------------------------------------------------------------------------
    # SCRAPING JOBS
    # ------------------------------------------------------------------------
    
    async def scrape_council(
        self,
        council_code: str,
        mode: str = "active"
    ) -> Dict:
        """
        Scrape a single council.
        
        Args:
            council_code: Council identifier
            mode: "active" for current DAs, "historical" for backfill
            
        Returns:
            Scrape result summary
        """
        
        start_time = datetime.utcnow()
        result = {
            "council_code": council_code,
            "mode": mode,
            "started_at": start_time.isoformat(),
            "status": "pending",
            "records_scraped": 0,
            "records_processed": 0,
            "errors": []
        }
        
        try:
            # Get adapter for this council
            adapter = self.adapter_registry.get_adapter(council_code)
            
            # Check portal health first
            health = await adapter.get_portal_status()
            if not health.is_healthy:
                result["status"] = "skipped"
                result["errors"].append(f"Portal unhealthy: {health.message}")
                return result
            
            # Perform scrape
            if mode == "active":
                raw_records = await adapter.scrape_active()
            else:
                raw_records = await adapter.scrape_historical()
            
            result["records_scraped"] = len(raw_records)
            
            # Store raw data
            batch_id = await self.raw_store.store_batch(
                council_code=council_code,
                records=raw_records
            )
            
            # Process records
            processed = await self._process_records(council_code, raw_records)
            result["records_processed"] = len(processed)
            
            # Store to database
            await self.db.upsert_applications(processed)
            
            result["status"] = "success"
            result["completed_at"] = datetime.utcnow().isoformat()
            
        except Exception as e:
            logger.exception(f"Scrape failed for {council_code}")
            result["status"] = "failed"
            result["errors"].append(str(e))
            
            # Send alert
            await self.alerts.send_scraper_failure(
                council_code=council_code,
                error=str(e)
            )
        
        # Log result
        await self.db.log_scrape_run(result)
        
        return result
    
    async def _process_records(
        self,
        council_code: str,
        raw_records: List[Dict]
    ) -> List[Dict]:
        """
        Process raw records through the normalization pipeline.
        """
        
        processed = []
        
        for raw in raw_records:
            try:
                # 1. Apply field mapping
                normalized = self.field_mapper.apply_mapping(council_code, raw)
                
                # 2. Classify category
                if normalized.get("description"):
                    classification = self.classifier.classify(
                        normalized["description"]
                    )
                    normalized.update({
                        "category": classification["category"],
                        "subcategory": classification.get("subcategory"),
                        "dwelling_count": classification.get("dwelling_count") or normalized.get("dwelling_count"),
                        "lot_count": classification.get("lot_count"),
                        "classification_confidence": classification["confidence"]
                    })
                
                # 3. Geocode address
                if normalized.get("address") and not normalized.get("latitude"):
                    coords = await self.geocoder.geocode(
                        address=normalized["address"],
                        suburb=normalized.get("suburb"),
                        state=normalized.get("state", council_code[:3])
                    )
                    if coords:
                        normalized["latitude"] = coords["lat"]
                        normalized["longitude"] = coords["lng"]
                
                # 4. Validate data quality
                quality = self.validator.assess_quality(normalized)
                normalized["data_quality_score"] = quality["score"]
                
                # 5. Check for duplicates
                is_dup, existing_id = await self.deduplicator.check(normalized)
                if is_dup:
                    normalized["duplicate_of"] = existing_id
                
                processed.append(normalized)
                
            except Exception as e:
                logger.warning(f"Failed to process record: {e}")
                continue
        
        return processed
    
    # ------------------------------------------------------------------------
    # SCHEDULING
    # ------------------------------------------------------------------------
    
    def get_scrape_schedule(self) -> Dict[str, Dict]:
        """
        Define scraping schedule based on council priority.
        
        Returns:
            Celery beat schedule configuration
        """
        
        schedule = {}
        
        # Tier 1 councils (Top 50) - Every 6 hours
        tier1_councils = self.adapter_registry.get_councils_by_tier(1)
        for council in tier1_councils:
            schedule[f"scrape-{council.code}-tier1"] = {
                "task": "orchestrator.tasks.scrape_council",
                "schedule": crontab(hour="*/6"),
                "args": [council.code, "active"]
            }
        
        # Tier 2 councils (51-100) - Every 12 hours
        tier2_councils = self.adapter_registry.get_councils_by_tier(2)
        for council in tier2_councils:
            schedule[f"scrape-{council.code}-tier2"] = {
                "task": "orchestrator.tasks.scrape_council",
                "schedule": crontab(hour="*/12"),
                "args": [council.code, "active"]
            }
        
        # Tier 3-4 councils (101-200) - Daily
        tier34_councils = (
            self.adapter_registry.get_councils_by_tier(3) +
            self.adapter_registry.get_councils_by_tier(4)
        )
        for i, council in enumerate(tier34_councils):
            # Stagger throughout the day
            hour = i % 24
            schedule[f"scrape-{council.code}-daily"] = {
                "task": "orchestrator.tasks.scrape_council",
                "schedule": crontab(hour=hour, minute=0),
                "args": [council.code, "active"]
            }
        
        # Daily quality check
        schedule["daily-quality-check"] = {
            "task": "orchestrator.tasks.run_quality_checks",
            "schedule": crontab(hour=2, minute=0)
        }
        
        return schedule

# ----------------------------------------------------------------------------
# CELERY TASKS
# ----------------------------------------------------------------------------

@celery_app.task(bind=True, max_retries=3)
def scrape_council(self, council_code: str, mode: str = "active"):
    """
    Celery task for scraping a single council.
    """
    orchestrator = ScraperOrchestrator()
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(
        orchestrator.scrape_council(council_code, mode)
    )
    return result

@celery_app.task
def run_quality_checks():
    """
    Daily task to check data quality across all councils.
    """
    orchestrator = ScraperOrchestrator()
    loop = asyncio.get_event_loop()
    
    # Check each council for data anomalies
    councils = orchestrator.adapter_registry.get_all_councils()
    
    for council in councils:
        result = loop.run_until_complete(
            orchestrator.validator.check_council_health(council.code)
        )
        
        if result["status"] == "degraded":
            loop.run_until_complete(
                orchestrator.alerts.send_quality_alert(
                    council_code=council.code,
                    issues=result["issues"]
                )
            )

@celery_app.task
def backfill_council(council_code: str, start_date: str, end_date: str):
    """
    Task for historical backfill of a council's data.
    """
    orchestrator = ScraperOrchestrator()
    loop = asyncio.get_event_loop()
    
    result = loop.run_until_complete(
        orchestrator.scrape_council(council_code, mode="historical")
    )
    return result

# ----------------------------------------------------------------------------
# HEALTH MONITORING
# ----------------------------------------------------------------------------

class HealthMonitor:
    """
    Monitors overall system health and scraper status.
    """
    
    def __init__(self):
        self.db = DatabaseManager()
        self.redis = redis_client
    
    async def get_system_status(self) -> Dict:
        """Get overall system health status."""
        
        return {
            "status": "healthy",
            "councils_active": await self.db.count_active_councils(),
            "total_applications": await self.db.count_applications(),
            "last_24h_scrapes": await self.db.count_recent_scrapes(hours=24),
            "failed_scrapers": await self._get_failed_scrapers(),
            "queue_depth": self._get_queue_depth()
        }
    
    async def _get_failed_scrapers(self) -> List[str]:
        """Get list of councils with failed scrapers."""
        
        failed = await self.db.query("""
            SELECT council_code 
            FROM scrape_logs 
            WHERE status = 'failed' 
            AND created_at > NOW() - INTERVAL '24 hours'
            GROUP BY council_code
            HAVING COUNT(*) >= 3
        """)
        return [r["council_code"] for r in failed]
    
    def _get_queue_depth(self) -> int:
        """Get number of pending tasks in queue."""
        return self.redis.llen("celery")
```

---

## 4. AI-Assisted Scraper Generation

```python
# ============================================================================
# FILE: generators/scraper_generator.py
# PURPOSE: AI-powered scraper code generation from page analysis
# ============================================================================

from anthropic import Anthropic
from playwright.async_api import async_playwright
import json
import ast
from typing import Optional

# ----------------------------------------------------------------------------
# SCRAPER GENERATOR
# ----------------------------------------------------------------------------

class AIScraperGenerator:
    """
    Generates scraper code by analyzing council planning portal pages.
    """
    
    def __init__(self):
        self.client = Anthropic()
        self.model = "claude-sonnet-4-20250514"
    
    async def generate_scraper(
        self,
        council_code: str,
        portal_url: str
    ) -> str:
        """
        Generate a complete scraper for a council portal.
        
        Args:
            council_code: Council identifier
            portal_url: URL of the planning portal
            
        Returns:
            Python scraper code as string
        """
        
        # Fetch and analyze the page
        html_content = await self._fetch_page(portal_url)
        cleaned_html = self._clean_html(html_content)
        
        # Generate scraper code
        prompt = f"""
        Analyze this council planning portal HTML and generate a complete Python scraper.
        
        Council: {council_code}
        URL: {portal_url}
        
        HTML (truncated):
        ```html
        {cleaned_html[:15000]}
        ```
        
        Generate a Python scraper class that:
        1. Inherits from CouncilAdapter base class
        2. Uses Playwright for browser automation
        3. Extracts all visible development applications
        4. Handles pagination if present
        5. Returns data matching our raw schema
        
        Required methods:
        - async def scrape_active(self) -> List[Dict]
        - async def scrape_historical(self, start: date, end: date) -> List[Dict]
        - async def get_portal_status(self) -> PortalHealth
        
        Raw schema fields to extract:
        - application_number (required)
        - address (required)
        - description (required)
        - status
        - lodged_date
        - determined_date
        - estimated_cost
        - applicant
        - any other visible fields
        
        Include:
        - Error handling
        - Rate limiting (1 req/sec default)
        - Logging
        - Retry logic for transient failures
        
        IMPORTANT: Use proper async/await patterns with Playwright.
        
        Return ONLY the Python code, no explanations.
        """
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        code = self._extract_code(response.content[0].text)
        
        # Validate syntax
        if self._validate_python(code):
            return code
        else:
            # Retry with syntax error feedback
            return await self._fix_syntax(code)
    
    async def _fetch_page(self, url: str) -> str:
        """Fetch page HTML using Playwright."""
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            await page.goto(url, wait_until="networkidle")
            await page.wait_for_timeout(2000)  # Wait for JS
            
            html = await page.content()
            await browser.close()
            
            return html
    
    def _clean_html(self, html: str, max_tokens: int = 8000) -> str:
        """Clean and truncate HTML for LLM context."""
        
        from bs4 import BeautifulSoup
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove scripts, styles, comments
        for tag in soup.find_all(['script', 'style', 'meta', 'link']):
            tag.decompose()
        
        # Get text-heavy HTML
        cleaned = str(soup)
        
        # Rough token estimate and truncate
        if len(cleaned) > max_tokens * 4:
            cleaned = cleaned[:max_tokens * 4]
        
        return cleaned
    
    def _extract_code(self, response: str) -> str:
        """Extract Python code from LLM response."""
        
        if "```python" in response:
            return response.split("```python")[1].split("```")[0]
        elif "```" in response:
            return response.split("```")[1].split("```")[0]
        return response
    
    def _validate_python(self, code: str) -> bool:
        """Validate Python syntax."""
        try:
            ast.parse(code)
            return True
        except SyntaxError:
            return False
    
    async def _fix_syntax(self, code: str) -> str:
        """Attempt to fix syntax errors using LLM."""
        
        try:
            ast.parse(code)
            return code
        except SyntaxError as e:
            error_msg = str(e)
        
        prompt = f"""
        Fix the syntax error in this Python code:
        
        Error: {error_msg}
        
        Code:
        ```python
        {code}
        ```
        
        Return ONLY the corrected Python code, no explanations.
        """
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return self._extract_code(response.content[0].text)

# ----------------------------------------------------------------------------
# TEST GENERATOR
# ----------------------------------------------------------------------------

class TestGenerator:
    """
    Generates test cases for scrapers.
    """
    
    def __init__(self):
        self.client = Anthropic()
    
    def generate_tests(
        self,
        council_code: str,
        scraper_code: str,
        sample_output: List[Dict]
    ) -> str:
        """Generate pytest test cases for a scraper."""
        
        prompt = f"""
        Generate pytest test cases for this council scraper.
        
        Council: {council_code}
        
        Scraper code:
        ```python
        {scraper_code[:3000]}
        ```
        
        Sample output:
        {json.dumps(sample_output[:2], indent=2)}
        
        Generate tests for:
        1. Required fields present (application_number, address, description)
        2. Date formats valid
        3. Status values from expected set
        4. No empty required fields
        5. Basic data type validation
        
        Use pytest fixtures and mocking where appropriate.
        Return ONLY the test code.
        """
        
        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return response.content[0].text
```

---

## 5. Database Schema

```sql
-- ============================================================================
-- FILE: database/schema.sql
-- PURPOSE: PostgreSQL + PostGIS schema for council DA data
-- ============================================================================

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "postgis";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- ----------------------------------------------------------------------------
-- COUNCILS TABLE
-- ----------------------------------------------------------------------------

CREATE TABLE councils (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    state VARCHAR(3) NOT NULL,
    lga_code VARCHAR(10),
    population INTEGER,
    tier INTEGER DEFAULT 4,
    portal_url TEXT,
    portal_type VARCHAR(50),
    scraper_status VARCHAR(20) DEFAULT 'pending',
    last_scraped_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_councils_state ON councils(state);
CREATE INDEX idx_councils_tier ON councils(tier);

-- ----------------------------------------------------------------------------
-- APPLICATIONS TABLE (Main DA records)
-- ----------------------------------------------------------------------------

CREATE TABLE applications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    da_number VARCHAR(100) NOT NULL,
    council_id INTEGER REFERENCES councils(id),
    
    -- Property
    address TEXT NOT NULL,
    suburb VARCHAR(100),
    postcode VARCHAR(10),
    state VARCHAR(3),
    lot_plan VARCHAR(100),
    coordinates GEOMETRY(Point, 4326),
    land_area_sqm DECIMAL(12,2),
    
    -- Application
    application_type VARCHAR(50),
    category VARCHAR(50),
    subcategory VARCHAR(100),
    description TEXT,
    
    -- Status
    status VARCHAR(50),
    decision VARCHAR(50),
    decision_date DATE,
    
    -- Dates
    lodged_date DATE,
    validated_date DATE,
    exhibition_start DATE,
    exhibition_end DATE,
    determined_date DATE,
    
    -- Details
    estimated_cost DECIMAL(15,2),
    dwelling_count INTEGER,
    lot_count INTEGER,
    floor_area_sqm DECIMAL(12,2),
    storeys INTEGER,
    car_spaces INTEGER,
    
    -- Applicant
    applicant_name VARCHAR(255),
    applicant_type VARCHAR(50),
    owner_name VARCHAR(255),
    
    -- Metadata
    source_url TEXT,
    scraped_at TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_quality_score DECIMAL(3,2),
    
    -- Constraints
    UNIQUE(council_id, da_number)
);

-- Indexes for common queries
CREATE INDEX idx_applications_council ON applications(council_id);
CREATE INDEX idx_applications_status ON applications(status);
CREATE INDEX idx_applications_category ON applications(category);
CREATE INDEX idx_applications_lodged ON applications(lodged_date);
CREATE INDEX idx_applications_suburb ON applications(suburb);
CREATE INDEX idx_applications_postcode ON applications(postcode);

-- Spatial index for geo queries
CREATE INDEX idx_applications_geo ON applications USING GIST(coordinates);

-- Full-text search index
CREATE INDEX idx_applications_description ON applications 
    USING GIN(to_tsvector('english', description));

-- BRIN index for time-range queries (efficient for large tables)
CREATE INDEX idx_applications_lodged_brin ON applications 
    USING BRIN(lodged_date);

-- ----------------------------------------------------------------------------
-- DOCUMENTS TABLE
-- ----------------------------------------------------------------------------

CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    application_id UUID REFERENCES applications(id) ON DELETE CASCADE,
    name VARCHAR(500),
    url TEXT,
    doc_type VARCHAR(50),
    uploaded_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_documents_application ON documents(application_id);

-- ----------------------------------------------------------------------------
-- SCRAPE LOGS TABLE
-- ----------------------------------------------------------------------------

CREATE TABLE scrape_logs (
    id SERIAL PRIMARY KEY,
    council_id INTEGER REFERENCES councils(id),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    status VARCHAR(20),
    mode VARCHAR(20),
    records_scraped INTEGER DEFAULT 0,
    records_processed INTEGER DEFAULT 0,
    errors JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_scrape_logs_council ON scrape_logs(council_id);
CREATE INDEX idx_scrape_logs_created ON scrape_logs(created_at);

-- ----------------------------------------------------------------------------
-- FIELD MAPPINGS TABLE (AI-learned mappings)
-- ----------------------------------------------------------------------------

CREATE TABLE field_mappings (
    id SERIAL PRIMARY KEY,
    council_id INTEGER REFERENCES councils(id) UNIQUE,
    mapping JSONB NOT NULL,
    status_values JSONB,
    learned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------------------------------------------------------
-- API USAGE TABLE
-- ----------------------------------------------------------------------------

CREATE TABLE api_usage (
    id SERIAL PRIMARY KEY,
    api_key_id INTEGER,
    endpoint VARCHAR(100),
    method VARCHAR(10),
    response_time_ms INTEGER,
    status_code INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_api_usage_key ON api_usage(api_key_id);
CREATE INDEX idx_api_usage_created ON api_usage(created_at);

-- ----------------------------------------------------------------------------
-- USEFUL VIEWS
-- ----------------------------------------------------------------------------

-- Applications with council info
CREATE VIEW v_applications_full AS
SELECT 
    a.*,
    c.code as council_code,
    c.name as council_name,
    c.state as council_state,
    ST_Y(a.coordinates) as latitude,
    ST_X(a.coordinates) as longitude
FROM applications a
JOIN councils c ON a.council_id = c.id;

-- Council stats
CREATE VIEW v_council_stats AS
SELECT 
    c.id,
    c.code,
    c.name,
    c.state,
    COUNT(a.id) as total_applications,
    COUNT(CASE WHEN a.lodged_date > CURRENT_DATE - INTERVAL '30 days' THEN 1 END) as last_30_days,
    MAX(a.scraped_at) as last_scraped,
    AVG(a.data_quality_score) as avg_quality_score
FROM councils c
LEFT JOIN applications a ON c.id = a.council_id
GROUP BY c.id, c.code, c.name, c.state;
```

---

## 6. API Specification

```yaml
# ============================================================================
# FILE: api/openapi.yaml
# PURPOSE: OpenAPI specification for Council DA API
# ============================================================================

openapi: 3.0.3
info:
  title: Council Planning Data API
  description: |
    Unified API for Australian council Development Application data.
    Aggregates DAs from 200+ councils into a single, standardized format.
  version: 1.0.0
  contact:
    email: api@councildata.com.au

servers:
  - url: https://api.councildata.com.au/v1
    description: Production

security:
  - ApiKeyAuth: []

paths:
  /applications:
    get:
      summary: Search development applications
      parameters:
        - name: council
          in: query
          schema:
            type: string
          description: Filter by council code
        - name: status
          in: query
          schema:
            type: string
            enum: [lodged, under_assessment, approved, refused]
        - name: category
          in: query
          schema:
            type: string
        - name: suburb
          in: query
          schema:
            type: string
        - name: postcode
          in: query
          schema:
            type: string
        - name: lodged_after
          in: query
          schema:
            type: string
            format: date
        - name: lodged_before
          in: query
          schema:
            type: string
            format: date
        - name: min_cost
          in: query
          schema:
            type: number
        - name: max_cost
          in: query
          schema:
            type: number
        - name: page
          in: query
          schema:
            type: integer
            default: 1
        - name: limit
          in: query
          schema:
            type: integer
            default: 50
            maximum: 200
      responses:
        '200':
          description: List of applications
          content:
            application/json:
              schema:
                type: object
                properties:
                  data:
                    type: array
                    items:
                      $ref: '#/components/schemas/Application'
                  meta:
                    $ref: '#/components/schemas/PaginationMeta'

  /applications/near:
    get:
      summary: Find applications near a location
      parameters:
        - name: lat
          in: query
          required: true
          schema:
            type: number
        - name: lng
          in: query
          required: true
          schema:
            type: number
        - name: radius_km
          in: query
          schema:
            type: number
            default: 5
            maximum: 50
        - name: limit
          in: query
          schema:
            type: integer
            default: 50
      responses:
        '200':
          description: Applications within radius

  /applications/{id}:
    get:
      summary: Get single application by ID
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: string
            format: uuid
      responses:
        '200':
          description: Application details
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Application'

  /councils:
    get:
      summary: List all councils
      responses:
        '200':
          description: List of councils with stats

  /councils/{code}/stats:
    get:
      summary: Get council statistics
      parameters:
        - name: code
          in: path
          required: true
          schema:
            type: string

  /webhooks:
    post:
      summary: Register webhook for new DA notifications
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                url:
                  type: string
                  format: uri
                councils:
                  type: array
                  items:
                    type: string
                categories:
                  type: array
                  items:
                    type: string

components:
  schemas:
    Application:
      type: object
      properties:
        id:
          type: string
          format: uuid
        da_number:
          type: string
        council:
          type: object
          properties:
            code:
              type: string
            name:
              type: string
            state:
              type: string
        property:
          type: object
          properties:
            address:
              type: string
            suburb:
              type: string
            postcode:
              type: string
            coordinates:
              type: object
        application:
          type: object
          properties:
            type:
              type: string
            category:
              type: string
            description:
              type: string
        status:
          type: string
        dates:
          type: object
        details:
          type: object

    PaginationMeta:
      type: object
      properties:
        page:
          type: integer
        limit:
          type: integer
        total:
          type: integer
        pages:
          type: integer

  securitySchemes:
    ApiKeyAuth:
      type: apiKey
      in: header
      name: X-API-Key
```

---

## 7. Development Roadmap

### Phase 1: Foundation (Weeks 1-4)

| Week | Deliverables |
|------|--------------|
| 1 | Project setup, database schema, basic API scaffold |
| 2 | AI Field Mapper implementation, Master schema |
| 3 | First 10 council scrapers (manual), Orchestrator core |
| 4 | AI Scraper Generator, Testing framework |

### Phase 2: Scale (Weeks 5-10)

| Week | Deliverables |
|------|--------------|
| 5-6 | Generate scrapers for councils 11-50 (Tier 1) |
| 7-8 | Generate scrapers for councils 51-100 (Tier 2) |
| 9-10 | Quality validation, Monitoring, Alerting |

### Phase 3: Coverage (Weeks 11-16)

| Week | Deliverables |
|------|--------------|
| 11-12 | Generate scrapers for councils 101-150 (Tier 3) |
| 13-14 | Generate scrapers for councils 151-200 (Tier 4) |
| 15-16 | Historical backfill, Data quality improvements |

### Phase 4: Launch (Weeks 17-20)

| Week | Deliverables |
|------|--------------|
| 17 | API hardening, Rate limiting, Authentication |
| 18 | Documentation, Developer portal |
| 19 | Beta launch, First customers |
| 20 | Production monitoring, SLA establishment |

---


## 10. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Council portal changes | High | Medium | Monitoring + AI regeneration |
| Legal/ToS issues | Low | High | Public data only, polite scraping |
| Competition from CoreLogic | Medium | Medium | Focus on SMB/startup pricing |
| Scraper maintenance burden | High | Medium | AI assistance, automated alerts |
| Low initial demand | Medium | High | Pre-launch customer validation |
| Data quality issues | Medium | Medium | AI validation, quality scoring |

---


## Appendix: Key Contacts

### State Planning Portals

| State | Portal | URL |
|-------|--------|-----|
| NSW | ePlanning | https://www.planningportal.nsw.gov.au |
| VIC | Delwp | https://www.planning.vic.gov.au |
| QLD | Development.i | https://developmenti.dsdip.qld.gov.au |
| WA | PlanWA | https://www.dplh.wa.gov.au |
| SA | PlanSA | https://plan.sa.gov.au |

### Data Sources

| Source | Use | URL |
|--------|-----|-----|
| ABS LGA Data | Population stats | https://www.abs.gov.au/databyregion |
| GNAF | Geocoding | https://data.gov.au/dataset/geocoded-national-address-file |
| PlanningAlerts | Reference | https://www.planningalerts.org.au |



Most Important – 
planningalerts-scrapers
https://github.com/planningalerts-scrapers

openaustralia/atdis
https://github.com/openaustralia/atdis


