"""
Council Configuration and Registry
Contains the top 200 Australian councils with metadata
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class State(str, Enum):
    NSW = "NSW"
    VIC = "VIC"
    QLD = "QLD"
    SA = "SA"
    WA = "WA"
    TAS = "TAS"
    NT = "NT"
    ACT = "ACT"


class PortalType(str, Enum):
    EPLANNING_NSW = "eplanning_nsw"
    SPEAR_VIC = "spear_vic"
    DEVELOPMENT_I_QLD = "development_i_qld"
    PLAN_SA = "plan_sa"
    PLAN_WA = "plan_wa"
    CIVICA = "civica"
    TECHNOLOGY_ONE = "technology_one"
    MASTERVIEW = "masterview"
    EPATHWAY = "epathway"
    ATDIS = "atdis"
    CUSTOM = "custom"


class ScraperStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    BROKEN = "broken"
    DISABLED = "disabled"


@dataclass
class CouncilConfig:
    """Configuration for a single council."""

    code: str
    name: str
    state: State
    population: int
    tier: int  # 1-4, 1 being highest priority
    portal_url: Optional[str] = None
    portal_type: Optional[PortalType] = None
    scraper_class: Optional[str] = None
    lga_code: Optional[str] = None
    metro_area: Optional[str] = None
    scraper_status: ScraperStatus = ScraperStatus.PENDING
    notes: Optional[str] = None


# =============================================================================
# TIER 1: Major Metro Councils (1-50) - Scrape every 6 hours
# =============================================================================

TIER_1_COUNCILS = [
    # Queensland
    CouncilConfig(
        code="BRISBANE",
        name="Brisbane City Council",
        state=State.QLD,
        population=1350000,
        tier=1,
        portal_url="https://developmenti.brisbane.qld.gov.au/",
        portal_type=PortalType.DEVELOPMENT_I_QLD,
        metro_area="Brisbane",
    ),
    CouncilConfig(
        code="GOLD_COAST",
        name="Gold Coast City Council",
        state=State.QLD,
        population=640000,
        tier=1,
        portal_url="https://cogc.cloud.infor.com/ePathway/epthprod/Web/",
        portal_type=PortalType.EPATHWAY,
        metro_area="Gold Coast",
    ),
    CouncilConfig(
        code="MORETON_BAY",
        name="Moreton Bay Regional Council",
        state=State.QLD,
        population=510000,
        tier=1,
        portal_type=PortalType.DEVELOPMENT_I_QLD,
        metro_area="Brisbane",
    ),
    CouncilConfig(
        code="LOGAN",
        name="Logan City Council",
        state=State.QLD,
        population=360000,
        tier=1,
        portal_type=PortalType.DEVELOPMENT_I_QLD,
        metro_area="Brisbane",
    ),
    CouncilConfig(
        code="SUNSHINE_COAST",
        name="Sunshine Coast Council",
        state=State.QLD,
        population=360000,
        tier=1,
        portal_type=PortalType.DEVELOPMENT_I_QLD,
        metro_area="Sunshine Coast",
    ),
    CouncilConfig(
        code="IPSWICH",
        name="Ipswich City Council",
        state=State.QLD,
        population=250000,
        tier=1,
        portal_type=PortalType.DEVELOPMENT_I_QLD,
        metro_area="Brisbane",
    ),

    # New South Wales
    CouncilConfig(
        code="BLACKTOWN",
        name="Blacktown City Council",
        state=State.NSW,
        population=415000,
        tier=1,
        portal_url="https://www.planningportal.nsw.gov.au/",
        portal_type=PortalType.EPLANNING_NSW,
        metro_area="Sydney",
    ),
    CouncilConfig(
        code="CANTERBURY_BANKSTOWN",
        name="Canterbury-Bankstown Council",
        state=State.NSW,
        population=380000,
        tier=1,
        portal_type=PortalType.EPLANNING_NSW,
        metro_area="Sydney",
    ),
    CouncilConfig(
        code="CENTRAL_COAST",
        name="Central Coast Council",
        state=State.NSW,
        population=350000,
        tier=1,
        portal_type=PortalType.EPLANNING_NSW,
        metro_area="Central Coast",
    ),
    CouncilConfig(
        code="PARRAMATTA",
        name="City of Parramatta",
        state=State.NSW,
        population=270000,
        tier=1,
        portal_type=PortalType.EPLANNING_NSW,
        metro_area="Sydney",
    ),
    CouncilConfig(
        code="NORTHERN_BEACHES",
        name="Northern Beaches Council",
        state=State.NSW,
        population=275000,
        tier=1,
        portal_type=PortalType.EPLANNING_NSW,
        metro_area="Sydney",
    ),
    CouncilConfig(
        code="CUMBERLAND",
        name="Cumberland City Council",
        state=State.NSW,
        population=250000,
        tier=1,
        portal_type=PortalType.EPLANNING_NSW,
        metro_area="Sydney",
    ),
    CouncilConfig(
        code="SUTHERLAND",
        name="Sutherland Shire Council",
        state=State.NSW,
        population=240000,
        tier=1,
        portal_type=PortalType.EPLANNING_NSW,
        metro_area="Sydney",
    ),
    CouncilConfig(
        code="LIVERPOOL",
        name="Liverpool City Council",
        state=State.NSW,
        population=240000,
        tier=1,
        portal_type=PortalType.EPLANNING_NSW,
        metro_area="Sydney",
    ),
    CouncilConfig(
        code="PENRITH",
        name="Penrith City Council",
        state=State.NSW,
        population=230000,
        tier=1,
        portal_type=PortalType.EPLANNING_NSW,
        metro_area="Sydney",
    ),
    CouncilConfig(
        code="SYDNEY",
        name="City of Sydney",
        state=State.NSW,
        population=220000,
        tier=1,
        portal_url="https://online.cityofsydney.nsw.gov.au/DA/",
        portal_type=PortalType.CUSTOM,
        metro_area="Sydney",
    ),
    CouncilConfig(
        code="FAIRFIELD",
        name="Fairfield City Council",
        state=State.NSW,
        population=220000,
        tier=1,
        portal_type=PortalType.EPLANNING_NSW,
        metro_area="Sydney",
    ),
    CouncilConfig(
        code="WOLLONGONG",
        name="Wollongong City Council",
        state=State.NSW,
        population=220000,
        tier=1,
        portal_type=PortalType.EPLANNING_NSW,
        metro_area="Wollongong",
    ),
    CouncilConfig(
        code="LAKE_MACQUARIE",
        name="Lake Macquarie City Council",
        state=State.NSW,
        population=215000,
        tier=1,
        portal_type=PortalType.EPLANNING_NSW,
        metro_area="Newcastle",
    ),
    CouncilConfig(
        code="INNER_WEST",
        name="Inner West Council",
        state=State.NSW,
        population=200000,
        tier=1,
        portal_type=PortalType.EPLANNING_NSW,
        metro_area="Sydney",
    ),
    CouncilConfig(
        code="THE_HILLS",
        name="The Hills Shire Council",
        state=State.NSW,
        population=200000,
        tier=1,
        portal_type=PortalType.EPLANNING_NSW,
        metro_area="Sydney",
    ),
    CouncilConfig(
        code="CAMPBELLTOWN_NSW",
        name="Campbelltown City Council",
        state=State.NSW,
        population=185000,
        tier=1,
        portal_type=PortalType.EPLANNING_NSW,
        metro_area="Sydney",
    ),
    CouncilConfig(
        code="BAYSIDE_NSW",
        name="Bayside Council",
        state=State.NSW,
        population=180000,
        tier=1,
        portal_type=PortalType.EPLANNING_NSW,
        metro_area="Sydney",
    ),
    CouncilConfig(
        code="NEWCASTLE",
        name="Newcastle City Council",
        state=State.NSW,
        population=170000,
        tier=1,
        portal_type=PortalType.EPLANNING_NSW,
        metro_area="Newcastle",
    ),
    CouncilConfig(
        code="GEORGES_RIVER",
        name="Georges River Council",
        state=State.NSW,
        population=160000,
        tier=1,
        portal_type=PortalType.EPLANNING_NSW,
        metro_area="Sydney",
    ),
    CouncilConfig(
        code="HORNSBY",
        name="Hornsby Shire Council",
        state=State.NSW,
        population=160000,
        tier=1,
        portal_type=PortalType.EPLANNING_NSW,
        metro_area="Sydney",
    ),
    CouncilConfig(
        code="RANDWICK",
        name="Randwick City Council",
        state=State.NSW,
        population=160000,
        tier=1,
        portal_type=PortalType.EPLANNING_NSW,
        metro_area="Sydney",
    ),
    CouncilConfig(
        code="CAMDEN",
        name="Camden Council",
        state=State.NSW,
        population=135000,
        tier=1,
        portal_type=PortalType.EPLANNING_NSW,
        metro_area="Sydney",
    ),

    # Victoria
    CouncilConfig(
        code="CASEY",
        name="City of Casey",
        state=State.VIC,
        population=380000,
        tier=1,
        portal_url="https://www.spear.land.vic.gov.au/",
        portal_type=PortalType.SPEAR_VIC,
        metro_area="Melbourne",
    ),
    CouncilConfig(
        code="WYNDHAM",
        name="Wyndham City Council",
        state=State.VIC,
        population=320000,
        tier=1,
        portal_type=PortalType.SPEAR_VIC,
        metro_area="Melbourne",
    ),
    CouncilConfig(
        code="GREATER_GEELONG",
        name="City of Greater Geelong",
        state=State.VIC,
        population=280000,
        tier=1,
        portal_type=PortalType.SPEAR_VIC,
        metro_area="Geelong",
    ),
    CouncilConfig(
        code="HUME",
        name="City of Hume",
        state=State.VIC,
        population=250000,
        tier=1,
        portal_type=PortalType.SPEAR_VIC,
        metro_area="Melbourne",
    ),
    CouncilConfig(
        code="WHITTLESEA",
        name="City of Whittlesea",
        state=State.VIC,
        population=250000,
        tier=1,
        portal_type=PortalType.SPEAR_VIC,
        metro_area="Melbourne",
    ),
    CouncilConfig(
        code="BRIMBANK",
        name="City of Brimbank",
        state=State.VIC,
        population=220000,
        tier=1,
        portal_type=PortalType.SPEAR_VIC,
        metro_area="Melbourne",
    ),
    CouncilConfig(
        code="MONASH",
        name="City of Monash",
        state=State.VIC,
        population=210000,
        tier=1,
        portal_type=PortalType.SPEAR_VIC,
        metro_area="Melbourne",
    ),
    CouncilConfig(
        code="MELTON",
        name="City of Melton",
        state=State.VIC,
        population=200000,
        tier=1,
        portal_type=PortalType.SPEAR_VIC,
        metro_area="Melbourne",
    ),
    CouncilConfig(
        code="BOROONDARA",
        name="City of Boroondara",
        state=State.VIC,
        population=185000,
        tier=1,
        portal_type=PortalType.SPEAR_VIC,
        metro_area="Melbourne",
    ),
    CouncilConfig(
        code="MORELAND",
        name="City of Merri-bek (Moreland)",
        state=State.VIC,
        population=185000,
        tier=1,
        portal_type=PortalType.SPEAR_VIC,
        metro_area="Melbourne",
    ),
    CouncilConfig(
        code="GREATER_DANDENONG",
        name="City of Greater Dandenong",
        state=State.VIC,
        population=180000,
        tier=1,
        portal_type=PortalType.SPEAR_VIC,
        metro_area="Melbourne",
    ),
    CouncilConfig(
        code="KNOX",
        name="City of Knox",
        state=State.VIC,
        population=170000,
        tier=1,
        portal_type=PortalType.SPEAR_VIC,
        metro_area="Melbourne",
    ),
    CouncilConfig(
        code="DAREBIN",
        name="City of Darebin",
        state=State.VIC,
        population=170000,
        tier=1,
        portal_type=PortalType.SPEAR_VIC,
        metro_area="Melbourne",
    ),
    CouncilConfig(
        code="MELBOURNE",
        name="City of Melbourne",
        state=State.VIC,
        population=180000,
        tier=1,
        portal_url="https://www.melbourne.vic.gov.au/building-and-development/",
        portal_type=PortalType.CIVICA,
        metro_area="Melbourne",
    ),

    # Western Australia
    CouncilConfig(
        code="WANNEROO",
        name="City of Wanneroo",
        state=State.WA,
        population=250000,
        tier=1,
        portal_type=PortalType.PLAN_WA,
        metro_area="Perth",
    ),
    CouncilConfig(
        code="STIRLING",
        name="City of Stirling",
        state=State.WA,
        population=240000,
        tier=1,
        portal_type=PortalType.PLAN_WA,
        metro_area="Perth",
    ),
    CouncilConfig(
        code="JOONDALUP",
        name="City of Joondalup",
        state=State.WA,
        population=165000,
        tier=1,
        portal_type=PortalType.PLAN_WA,
        metro_area="Perth",
    ),
    CouncilConfig(
        code="SWAN",
        name="City of Swan",
        state=State.WA,
        population=165000,
        tier=1,
        portal_type=PortalType.PLAN_WA,
        metro_area="Perth",
    ),
    CouncilConfig(
        code="ROCKINGHAM",
        name="City of Rockingham",
        state=State.WA,
        population=145000,
        tier=1,
        portal_type=PortalType.PLAN_WA,
        metro_area="Perth",
    ),
    CouncilConfig(
        code="GOSNELLS",
        name="City of Gosnells",
        state=State.WA,
        population=130000,
        tier=1,
        portal_type=PortalType.PLAN_WA,
        metro_area="Perth",
    ),
    CouncilConfig(
        code="COCKBURN",
        name="City of Cockburn",
        state=State.WA,
        population=125000,
        tier=1,
        portal_type=PortalType.PLAN_WA,
        metro_area="Perth",
    ),
]

# =============================================================================
# TIER 2: Secondary Metro & Regional Cities (51-100) - Scrape every 12 hours
# =============================================================================

TIER_2_COUNCILS = [
    # Queensland
    CouncilConfig(
        code="TOWNSVILLE",
        name="Townsville City Council",
        state=State.QLD,
        population=200000,
        tier=2,
        portal_type=PortalType.DEVELOPMENT_I_QLD,
        metro_area="Townsville",
    ),
    CouncilConfig(
        code="TOOWOOMBA",
        name="Toowoomba Regional Council",
        state=State.QLD,
        population=180000,
        tier=2,
        portal_type=PortalType.DEVELOPMENT_I_QLD,
        metro_area="Toowoomba",
    ),
    CouncilConfig(
        code="CAIRNS",
        name="Cairns Regional Council",
        state=State.QLD,
        population=170000,
        tier=2,
        portal_type=PortalType.DEVELOPMENT_I_QLD,
        metro_area="Cairns",
    ),
    CouncilConfig(
        code="REDLAND",
        name="Redland City Council",
        state=State.QLD,
        population=165000,
        tier=2,
        portal_type=PortalType.DEVELOPMENT_I_QLD,
        metro_area="Brisbane",
    ),
    CouncilConfig(
        code="MACKAY",
        name="Mackay Regional Council",
        state=State.QLD,
        population=125000,
        tier=2,
        portal_type=PortalType.DEVELOPMENT_I_QLD,
        metro_area="Mackay",
    ),
    CouncilConfig(
        code="FRASER_COAST",
        name="Fraser Coast Regional Council",
        state=State.QLD,
        population=110000,
        tier=2,
        portal_type=PortalType.DEVELOPMENT_I_QLD,
        metro_area="Hervey Bay",
    ),
    CouncilConfig(
        code="BUNDABERG",
        name="Bundaberg Regional Council",
        state=State.QLD,
        population=100000,
        tier=2,
        portal_type=PortalType.DEVELOPMENT_I_QLD,
        metro_area="Bundaberg",
    ),
    CouncilConfig(
        code="ROCKHAMPTON",
        name="Rockhampton Regional Council",
        state=State.QLD,
        population=90000,
        tier=2,
        portal_type=PortalType.DEVELOPMENT_I_QLD,
        metro_area="Rockhampton",
    ),

    # Victoria
    CouncilConfig(
        code="FRANKSTON",
        name="City of Frankston",
        state=State.VIC,
        population=145000,
        tier=2,
        portal_type=PortalType.SPEAR_VIC,
        metro_area="Melbourne",
    ),
    CouncilConfig(
        code="MOONEE_VALLEY",
        name="City of Moonee Valley",
        state=State.VIC,
        population=135000,
        tier=2,
        portal_type=PortalType.SPEAR_VIC,
        metro_area="Melbourne",
    ),
    CouncilConfig(
        code="BALLARAT",
        name="City of Ballarat",
        state=State.VIC,
        population=120000,
        tier=2,
        portal_type=PortalType.SPEAR_VIC,
        metro_area="Ballarat",
    ),
    CouncilConfig(
        code="BENDIGO",
        name="City of Greater Bendigo",
        state=State.VIC,
        population=120000,
        tier=2,
        portal_type=PortalType.SPEAR_VIC,
        metro_area="Bendigo",
    ),

    # New South Wales
    CouncilConfig(
        code="KU_RING_GAI",
        name="Ku-ring-gai Council",
        state=State.NSW,
        population=130000,
        tier=2,
        portal_type=PortalType.EPLANNING_NSW,
        metro_area="Sydney",
    ),
    CouncilConfig(
        code="SHOALHAVEN",
        name="Shoalhaven City Council",
        state=State.NSW,
        population=110000,
        tier=2,
        portal_type=PortalType.EPLANNING_NSW,
    ),
    CouncilConfig(
        code="TWEED",
        name="Tweed Shire Council",
        state=State.NSW,
        population=100000,
        tier=2,
        portal_type=PortalType.EPLANNING_NSW,
    ),
    CouncilConfig(
        code="MAITLAND",
        name="Maitland City Council",
        state=State.NSW,
        population=95000,
        tier=2,
        portal_type=PortalType.EPLANNING_NSW,
        metro_area="Newcastle",
    ),
    CouncilConfig(
        code="PORT_MACQUARIE",
        name="Port Macquarie-Hastings Council",
        state=State.NSW,
        population=90000,
        tier=2,
        portal_type=PortalType.EPLANNING_NSW,
    ),
    CouncilConfig(
        code="BLUE_MOUNTAINS",
        name="Blue Mountains City Council",
        state=State.NSW,
        population=80000,
        tier=2,
        portal_type=PortalType.EPLANNING_NSW,
        metro_area="Sydney",
    ),
    CouncilConfig(
        code="COFFS_HARBOUR",
        name="Coffs Harbour City Council",
        state=State.NSW,
        population=80000,
        tier=2,
        portal_type=PortalType.EPLANNING_NSW,
    ),
    CouncilConfig(
        code="SHELLHARBOUR",
        name="Shellharbour City Council",
        state=State.NSW,
        population=80000,
        tier=2,
        portal_type=PortalType.EPLANNING_NSW,
        metro_area="Wollongong",
    ),

    # South Australia
    CouncilConfig(
        code="ONKAPARINGA",
        name="City of Onkaparinga",
        state=State.SA,
        population=175000,
        tier=2,
        portal_url="https://plan.sa.gov.au/",
        portal_type=PortalType.PLAN_SA,
        metro_area="Adelaide",
    ),
    CouncilConfig(
        code="SALISBURY",
        name="City of Salisbury",
        state=State.SA,
        population=145000,
        tier=2,
        portal_type=PortalType.PLAN_SA,
        metro_area="Adelaide",
    ),
    CouncilConfig(
        code="PORT_ADELAIDE_ENFIELD",
        name="City of Port Adelaide Enfield",
        state=State.SA,
        population=130000,
        tier=2,
        portal_type=PortalType.PLAN_SA,
        metro_area="Adelaide",
    ),
    CouncilConfig(
        code="CHARLES_STURT",
        name="City of Charles Sturt",
        state=State.SA,
        population=120000,
        tier=2,
        portal_type=PortalType.PLAN_SA,
        metro_area="Adelaide",
    ),
    CouncilConfig(
        code="TEA_TREE_GULLY",
        name="City of Tea Tree Gully",
        state=State.SA,
        population=105000,
        tier=2,
        portal_type=PortalType.PLAN_SA,
        metro_area="Adelaide",
    ),
    CouncilConfig(
        code="PLAYFORD",
        name="City of Playford",
        state=State.SA,
        population=100000,
        tier=2,
        portal_type=PortalType.PLAN_SA,
        metro_area="Adelaide",
    ),
    CouncilConfig(
        code="MARION",
        name="City of Marion",
        state=State.SA,
        population=95000,
        tier=2,
        portal_type=PortalType.PLAN_SA,
        metro_area="Adelaide",
    ),

    # Western Australia
    CouncilConfig(
        code="CANNING",
        name="City of Canning",
        state=State.WA,
        population=105000,
        tier=2,
        portal_type=PortalType.PLAN_WA,
        metro_area="Perth",
    ),
    CouncilConfig(
        code="MELVILLE",
        name="City of Melville",
        state=State.WA,
        population=105000,
        tier=2,
        portal_type=PortalType.PLAN_WA,
        metro_area="Perth",
    ),
    CouncilConfig(
        code="ARMADALE",
        name="City of Armadale",
        state=State.WA,
        population=105000,
        tier=2,
        portal_type=PortalType.PLAN_WA,
        metro_area="Perth",
    ),
    CouncilConfig(
        code="MANDURAH",
        name="City of Mandurah",
        state=State.WA,
        population=95000,
        tier=2,
        portal_type=PortalType.PLAN_WA,
        metro_area="Perth",
    ),

    # Tasmania
    CouncilConfig(
        code="LAUNCESTON",
        name="City of Launceston",
        state=State.TAS,
        population=70000,
        tier=2,
        portal_type=PortalType.EPATHWAY,
        metro_area="Launceston",
    ),
    CouncilConfig(
        code="CLARENCE",
        name="Clarence City Council",
        state=State.TAS,
        population=60000,
        tier=2,
        portal_type=PortalType.EPATHWAY,
        metro_area="Hobart",
    ),
    CouncilConfig(
        code="HOBART",
        name="City of Hobart",
        state=State.TAS,
        population=57000,
        tier=2,
        portal_type=PortalType.EPATHWAY,
        metro_area="Hobart",
    ),
    CouncilConfig(
        code="GLENORCHY",
        name="Glenorchy City Council",
        state=State.TAS,
        population=50000,
        tier=2,
        portal_type=PortalType.EPATHWAY,
        metro_area="Hobart",
    ),

    # Northern Territory
    CouncilConfig(
        code="DARWIN",
        name="City of Darwin",
        state=State.NT,
        population=90000,
        tier=2,
        portal_type=PortalType.CUSTOM,
        metro_area="Darwin",
    ),
    CouncilConfig(
        code="PALMERSTON",
        name="City of Palmerston",
        state=State.NT,
        population=40000,
        tier=2,
        portal_type=PortalType.CUSTOM,
        metro_area="Darwin",
    ),
]

# =============================================================================
# TIER 3: Regional & Outer Metro (101-150) - Scrape daily
# =============================================================================

TIER_3_COUNCILS = [
    # New South Wales Regional
    CouncilConfig(
        code="WAGGA_WAGGA", name="Wagga Wagga City Council",
        state=State.NSW, population=70000, tier=3,
        portal_type=PortalType.EPLANNING_NSW,
    ),
    CouncilConfig(
        code="HAWKESBURY", name="Hawkesbury City Council",
        state=State.NSW, population=70000, tier=3,
        portal_type=PortalType.EPLANNING_NSW, metro_area="Sydney",
    ),
    CouncilConfig(
        code="TAMWORTH", name="Tamworth Regional Council",
        state=State.NSW, population=65000, tier=3,
        portal_type=PortalType.EPLANNING_NSW,
    ),
    CouncilConfig(
        code="QUEANBEYAN_PALERANG", name="Queanbeyan-Palerang Regional Council",
        state=State.NSW, population=65000, tier=3,
        portal_type=PortalType.EPLANNING_NSW,
    ),
    CouncilConfig(
        code="CESSNOCK", name="Cessnock City Council",
        state=State.NSW, population=60000, tier=3,
        portal_type=PortalType.EPLANNING_NSW, metro_area="Newcastle",
    ),
    CouncilConfig(
        code="PORT_STEPHENS", name="Port Stephens Council",
        state=State.NSW, population=75000, tier=3,
        portal_type=PortalType.EPLANNING_NSW, metro_area="Newcastle",
    ),
    CouncilConfig(
        code="DUBBO", name="Dubbo Regional Council",
        state=State.NSW, population=55000, tier=3,
        portal_type=PortalType.EPLANNING_NSW,
    ),
    CouncilConfig(
        code="WOLLONDILLY", name="Wollondilly Shire Council",
        state=State.NSW, population=55000, tier=3,
        portal_type=PortalType.EPLANNING_NSW, metro_area="Sydney",
    ),
    CouncilConfig(
        code="WINGECARRIBEE", name="Wingecarribee Shire Council",
        state=State.NSW, population=55000, tier=3,
        portal_type=PortalType.EPLANNING_NSW,
    ),
    CouncilConfig(
        code="ALBURY", name="Albury City Council",
        state=State.NSW, population=55000, tier=3,
        portal_type=PortalType.EPLANNING_NSW,
    ),
    CouncilConfig(
        code="CLARENCE_VALLEY", name="Clarence Valley Council",
        state=State.NSW, population=55000, tier=3,
        portal_type=PortalType.EPLANNING_NSW,
    ),
    CouncilConfig(
        code="LISMORE", name="Lismore City Council",
        state=State.NSW, population=45000, tier=3,
        portal_type=PortalType.EPLANNING_NSW,
    ),
    CouncilConfig(
        code="BALLINA", name="Ballina Shire Council",
        state=State.NSW, population=45000, tier=3,
        portal_type=PortalType.EPLANNING_NSW,
    ),
    CouncilConfig(
        code="ORANGE", name="Orange City Council",
        state=State.NSW, population=45000, tier=3,
        portal_type=PortalType.EPLANNING_NSW,
    ),
    CouncilConfig(
        code="BATHURST", name="Bathurst Regional Council",
        state=State.NSW, population=45000, tier=3,
        portal_type=PortalType.EPLANNING_NSW,
    ),
    CouncilConfig(
        code="EUROBODALLA", name="Eurobodalla Shire Council",
        state=State.NSW, population=40000, tier=3,
        portal_type=PortalType.EPLANNING_NSW,
    ),
    CouncilConfig(
        code="BYRON", name="Byron Shire Council",
        state=State.NSW, population=37000, tier=3,
        portal_type=PortalType.EPLANNING_NSW,
    ),
    CouncilConfig(
        code="BEGA_VALLEY", name="Bega Valley Shire Council",
        state=State.NSW, population=35000, tier=3,
        portal_type=PortalType.EPLANNING_NSW,
    ),

    # Victoria Regional
    CouncilConfig(
        code="LATROBE_VIC", name="City of Latrobe",
        state=State.VIC, population=80000, tier=3,
        portal_type=PortalType.SPEAR_VIC,
    ),
    CouncilConfig(
        code="SHEPPARTON", name="City of Greater Shepparton",
        state=State.VIC, population=70000, tier=3,
        portal_type=PortalType.SPEAR_VIC,
    ),
    CouncilConfig(
        code="MILDURA", name="City of Mildura",
        state=State.VIC, population=58000, tier=3,
        portal_type=PortalType.SPEAR_VIC,
    ),
    CouncilConfig(
        code="BAW_BAW", name="Baw Baw Shire Council",
        state=State.VIC, population=58000, tier=3,
        portal_type=PortalType.SPEAR_VIC,
    ),
    CouncilConfig(
        code="MITCHELL", name="Mitchell Shire Council",
        state=State.VIC, population=55000, tier=3,
        portal_type=PortalType.SPEAR_VIC,
    ),
    CouncilConfig(
        code="MACEDON_RANGES", name="Macedon Ranges Shire Council",
        state=State.VIC, population=55000, tier=3,
        portal_type=PortalType.SPEAR_VIC,
    ),
    CouncilConfig(
        code="EAST_GIPPSLAND", name="East Gippsland Shire Council",
        state=State.VIC, population=48000, tier=3,
        portal_type=PortalType.SPEAR_VIC,
    ),
    CouncilConfig(
        code="WELLINGTON", name="Wellington Shire Council",
        state=State.VIC, population=45000, tier=3,
        portal_type=PortalType.SPEAR_VIC,
    ),
    CouncilConfig(
        code="WODONGA", name="City of Wodonga",
        state=State.VIC, population=45000, tier=3,
        portal_type=PortalType.SPEAR_VIC,
    ),
    CouncilConfig(
        code="BASS_COAST", name="Bass Coast Shire Council",
        state=State.VIC, population=40000, tier=3,
        portal_type=PortalType.SPEAR_VIC,
    ),
    CouncilConfig(
        code="SURF_COAST", name="Surf Coast Shire Council",
        state=State.VIC, population=38000, tier=3,
        portal_type=PortalType.SPEAR_VIC,
    ),

    # Queensland Regional
    CouncilConfig(
        code="GLADSTONE", name="Gladstone Regional Council",
        state=State.QLD, population=65000, tier=3,
        portal_type=PortalType.DEVELOPMENT_I_QLD,
    ),
    CouncilConfig(
        code="NOOSA", name="Noosa Shire Council",
        state=State.QLD, population=60000, tier=3,
        portal_type=PortalType.DEVELOPMENT_I_QLD,
    ),
    CouncilConfig(
        code="GYMPIE", name="Gympie Regional Council",
        state=State.QLD, population=55000, tier=3,
        portal_type=PortalType.DEVELOPMENT_I_QLD,
    ),
    CouncilConfig(
        code="SCENIC_RIM", name="Scenic Rim Regional Council",
        state=State.QLD, population=45000, tier=3,
        portal_type=PortalType.DEVELOPMENT_I_QLD,
    ),
    CouncilConfig(
        code="LOCKYER_VALLEY", name="Lockyer Valley Regional Council",
        state=State.QLD, population=45000, tier=3,
        portal_type=PortalType.DEVELOPMENT_I_QLD,
    ),
    CouncilConfig(
        code="LIVINGSTONE", name="Livingstone Shire Council",
        state=State.QLD, population=40000, tier=3,
        portal_type=PortalType.DEVELOPMENT_I_QLD,
    ),

    # South Australia
    CouncilConfig(
        code="WEST_TORRENS", name="City of West Torrens",
        state=State.SA, population=62000, tier=3,
        portal_type=PortalType.PLAN_SA, metro_area="Adelaide",
    ),
    CouncilConfig(
        code="CAMPBELLTOWN_SA", name="City of Campbelltown (SA)",
        state=State.SA, population=55000, tier=3,
        portal_type=PortalType.PLAN_SA, metro_area="Adelaide",
    ),
    CouncilConfig(
        code="BURNSIDE", name="City of Burnside",
        state=State.SA, population=47000, tier=3,
        portal_type=PortalType.PLAN_SA, metro_area="Adelaide",
    ),
    CouncilConfig(
        code="MOUNT_BARKER", name="Mount Barker District Council",
        state=State.SA, population=42000, tier=3,
        portal_type=PortalType.PLAN_SA,
    ),
    CouncilConfig(
        code="ADELAIDE_HILLS", name="Adelaide Hills Council",
        state=State.SA, population=42000, tier=3,
        portal_type=PortalType.PLAN_SA, metro_area="Adelaide",
    ),

    # Western Australia
    CouncilConfig(
        code="BAYSWATER", name="City of Bayswater",
        state=State.WA, population=70000, tier=3,
        portal_type=PortalType.PLAN_WA, metro_area="Perth",
    ),
    CouncilConfig(
        code="SOUTH_PERTH", name="City of South Perth",
        state=State.WA, population=48000, tier=3,
        portal_type=PortalType.PLAN_WA, metro_area="Perth",
    ),
    CouncilConfig(
        code="BELMONT", name="City of Belmont",
        state=State.WA, population=45000, tier=3,
        portal_type=PortalType.PLAN_WA, metro_area="Perth",
    ),
    CouncilConfig(
        code="GERALDTON", name="City of Greater Geraldton",
        state=State.WA, population=42000, tier=3,
        portal_type=PortalType.PLAN_WA,
    ),
    CouncilConfig(
        code="ALBANY", name="City of Albany",
        state=State.WA, population=40000, tier=3,
        portal_type=PortalType.PLAN_WA,
    ),
    CouncilConfig(
        code="VICTORIA_PARK", name="Town of Victoria Park",
        state=State.WA, population=40000, tier=3,
        portal_type=PortalType.PLAN_WA, metro_area="Perth",
    ),

    # Tasmania
    CouncilConfig(
        code="KINGBOROUGH", name="Kingborough Council",
        state=State.TAS, population=42000, tier=3,
        portal_type=PortalType.EPATHWAY, metro_area="Hobart",
    ),
]

# =============================================================================
# TIER 4: Additional Regional (151-200) - Scrape daily
# =============================================================================

TIER_4_COUNCILS = [
    # Victoria
    CouncilConfig(
        code="WANGARATTA", name="Wangaratta Rural City Council",
        state=State.VIC, population=30000, tier=4,
        portal_type=PortalType.SPEAR_VIC,
    ),
    CouncilConfig(
        code="MOIRA", name="Moira Shire Council",
        state=State.VIC, population=30000, tier=4,
        portal_type=PortalType.SPEAR_VIC,
    ),
    CouncilConfig(
        code="CAMPASPE", name="Campaspe Shire Council",
        state=State.VIC, population=38000, tier=4,
        portal_type=PortalType.SPEAR_VIC,
    ),
    CouncilConfig(
        code="SOUTH_GIPPSLAND", name="South Gippsland Shire Council",
        state=State.VIC, population=30000, tier=4,
        portal_type=PortalType.SPEAR_VIC,
    ),
    CouncilConfig(
        code="WARRNAMBOOL", name="City of Warrnambool",
        state=State.VIC, population=36000, tier=4,
        portal_type=PortalType.SPEAR_VIC,
    ),
    CouncilConfig(
        code="COLAC_OTWAY", name="Colac Otway Shire Council",
        state=State.VIC, population=22000, tier=4,
        portal_type=PortalType.SPEAR_VIC,
    ),
    CouncilConfig(
        code="MOUNT_ALEXANDER", name="Mount Alexander Shire Council",
        state=State.VIC, population=20000, tier=4,
        portal_type=PortalType.SPEAR_VIC,
    ),
    CouncilConfig(
        code="HORSHAM", name="City of Horsham",
        state=State.VIC, population=20000, tier=4,
        portal_type=PortalType.SPEAR_VIC,
    ),
    CouncilConfig(
        code="INDIGO", name="Indigo Shire Council",
        state=State.VIC, population=18000, tier=4,
        portal_type=PortalType.SPEAR_VIC,
    ),
    CouncilConfig(
        code="HEPBURN", name="Hepburn Shire Council",
        state=State.VIC, population=16000, tier=4,
        portal_type=PortalType.SPEAR_VIC,
    ),
    CouncilConfig(
        code="BENALLA", name="Benalla Rural City Council",
        state=State.VIC, population=15000, tier=4,
        portal_type=PortalType.SPEAR_VIC,
    ),
    CouncilConfig(
        code="MURRINDINDI", name="Murrindindi Shire Council",
        state=State.VIC, population=15000, tier=4,
        portal_type=PortalType.SPEAR_VIC,
    ),
    CouncilConfig(
        code="ALPINE", name="Alpine Shire Council",
        state=State.VIC, population=13000, tier=4,
        portal_type=PortalType.SPEAR_VIC,
    ),
    CouncilConfig(
        code="ARARAT", name="Ararat Rural City Council",
        state=State.VIC, population=12000, tier=4,
        portal_type=PortalType.SPEAR_VIC,
    ),

    # South Australia
    CouncilConfig(
        code="UNLEY", name="City of Unley",
        state=State.SA, population=40000, tier=4,
        portal_type=PortalType.PLAN_SA, metro_area="Adelaide",
    ),
    CouncilConfig(
        code="NORWOOD", name="City of Norwood Payneham St Peters",
        state=State.SA, population=38000, tier=4,
        portal_type=PortalType.PLAN_SA, metro_area="Adelaide",
    ),
    CouncilConfig(
        code="ALEXANDRINA", name="Alexandrina Council",
        state=State.SA, population=30000, tier=4,
        portal_type=PortalType.PLAN_SA,
    ),
    CouncilConfig(
        code="MOUNT_GAMBIER", name="City of Mount Gambier",
        state=State.SA, population=28000, tier=4,
        portal_type=PortalType.PLAN_SA,
    ),
    CouncilConfig(
        code="BAROSSA", name="Barossa Council",
        state=State.SA, population=27000, tier=4,
        portal_type=PortalType.PLAN_SA,
    ),
    CouncilConfig(
        code="GAWLER", name="Town of Gawler",
        state=State.SA, population=27000, tier=4,
        portal_type=PortalType.PLAN_SA, metro_area="Adelaide",
    ),
    CouncilConfig(
        code="MURRAY_BRIDGE", name="Murray Bridge Council",
        state=State.SA, population=24000, tier=4,
        portal_type=PortalType.PLAN_SA,
    ),
    CouncilConfig(
        code="PROSPECT", name="City of Prospect",
        state=State.SA, population=22000, tier=4,
        portal_type=PortalType.PLAN_SA, metro_area="Adelaide",
    ),
    CouncilConfig(
        code="WHYALLA", name="City of Whyalla",
        state=State.SA, population=22000, tier=4,
        portal_type=PortalType.PLAN_SA,
    ),

    # Queensland
    CouncilConfig(
        code="WESTERN_DOWNS", name="Western Downs Regional Council",
        state=State.QLD, population=35000, tier=4,
        portal_type=PortalType.DEVELOPMENT_I_QLD,
    ),
    CouncilConfig(
        code="SOUTH_BURNETT", name="South Burnett Regional Council",
        state=State.QLD, population=32000, tier=4,
        portal_type=PortalType.DEVELOPMENT_I_QLD,
    ),
    CouncilConfig(
        code="CENTRAL_HIGHLANDS", name="Central Highlands Regional Council",
        state=State.QLD, population=30000, tier=4,
        portal_type=PortalType.DEVELOPMENT_I_QLD,
    ),
    CouncilConfig(
        code="CASSOWARY_COAST", name="Cassowary Coast Regional Council",
        state=State.QLD, population=30000, tier=4,
        portal_type=PortalType.DEVELOPMENT_I_QLD,
    ),
    CouncilConfig(
        code="SOMERSET", name="Somerset Regional Council",
        state=State.QLD, population=28000, tier=4,
        portal_type=PortalType.DEVELOPMENT_I_QLD,
    ),
    CouncilConfig(
        code="TABLELANDS", name="Tablelands Regional Council",
        state=State.QLD, population=27000, tier=4,
        portal_type=PortalType.DEVELOPMENT_I_QLD,
    ),
    CouncilConfig(
        code="ISAAC", name="Isaac Regional Council",
        state=State.QLD, population=22000, tier=4,
        portal_type=PortalType.DEVELOPMENT_I_QLD,
    ),
    CouncilConfig(
        code="BURDEKIN", name="Burdekin Shire Council",
        state=State.QLD, population=18000, tier=4,
        portal_type=PortalType.DEVELOPMENT_I_QLD,
    ),

    # New South Wales
    CouncilConfig(
        code="GOULBURN", name="Goulburn Mulwaree Council",
        state=State.NSW, population=32000, tier=4,
        portal_type=PortalType.EPLANNING_NSW,
    ),
    CouncilConfig(
        code="GRIFFITH", name="Griffith City Council",
        state=State.NSW, population=27000, tier=4,
        portal_type=PortalType.EPLANNING_NSW,
    ),
    CouncilConfig(
        code="SINGLETON", name="Singleton Council",
        state=State.NSW, population=25000, tier=4,
        portal_type=PortalType.EPLANNING_NSW,
    ),
    CouncilConfig(
        code="RICHMOND_VALLEY", name="Richmond Valley Council",
        state=State.NSW, population=25000, tier=4,
        portal_type=PortalType.EPLANNING_NSW,
    ),
    CouncilConfig(
        code="KIAMA", name="Kiama Municipal Council",
        state=State.NSW, population=25000, tier=4,
        portal_type=PortalType.EPLANNING_NSW, metro_area="Wollongong",
    ),
    CouncilConfig(
        code="SNOWY_MONARO", name="Snowy Monaro Regional Council",
        state=State.NSW, population=22000, tier=4,
        portal_type=PortalType.EPLANNING_NSW,
    ),

    # Western Australia
    CouncilConfig(
        code="VINCENT", name="City of Vincent",
        state=State.WA, population=38000, tier=4,
        portal_type=PortalType.PLAN_WA, metro_area="Perth",
    ),
    CouncilConfig(
        code="BUNBURY", name="City of Bunbury",
        state=State.WA, population=35000, tier=4,
        portal_type=PortalType.PLAN_WA,
    ),
    CouncilConfig(
        code="FREMANTLE", name="City of Fremantle",
        state=State.WA, population=32000, tier=4,
        portal_type=PortalType.PLAN_WA, metro_area="Perth",
    ),
    CouncilConfig(
        code="KALGOORLIE", name="City of Kalgoorlie-Boulder",
        state=State.WA, population=32000, tier=4,
        portal_type=PortalType.PLAN_WA,
    ),

    # Northern Territory
    CouncilConfig(
        code="LITCHFIELD", name="Litchfield Council",
        state=State.NT, population=25000, tier=4,
        portal_type=PortalType.CUSTOM, metro_area="Darwin",
    ),
    CouncilConfig(
        code="ALICE_SPRINGS", name="Alice Springs Town Council",
        state=State.NT, population=25000, tier=4,
        portal_type=PortalType.CUSTOM,
    ),
]


# =============================================================================
# ALL COUNCILS COMBINED
# =============================================================================

ALL_COUNCILS = TIER_1_COUNCILS + TIER_2_COUNCILS + TIER_3_COUNCILS + TIER_4_COUNCILS


def get_council_by_code(code: str) -> Optional[CouncilConfig]:
    """Get council configuration by code."""
    for council in ALL_COUNCILS:
        if council.code == code:
            return council
    return None


def get_councils_by_state(state: State) -> list[CouncilConfig]:
    """Get all councils in a state."""
    return [c for c in ALL_COUNCILS if c.state == state]


def get_councils_by_tier(tier: int) -> list[CouncilConfig]:
    """Get all councils in a tier."""
    return [c for c in ALL_COUNCILS if c.tier == tier]


def get_councils_by_portal_type(portal_type: PortalType) -> list[CouncilConfig]:
    """Get all councils using a specific portal type."""
    return [c for c in ALL_COUNCILS if c.portal_type == portal_type]


# Summary statistics
COUNCIL_STATS = {
    "total": len(ALL_COUNCILS),
    "tier_1": len(TIER_1_COUNCILS),
    "tier_2": len(TIER_2_COUNCILS),
    "tier_3": len(TIER_3_COUNCILS),
    "tier_4": len(TIER_4_COUNCILS),
    "by_state": {
        state.value: len(get_councils_by_state(state))
        for state in State
    },
    "by_portal_type": {
        pt.value: len(get_councils_by_portal_type(pt))
        for pt in PortalType
    },
}
