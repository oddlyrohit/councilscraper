# GitHub Repository Analysis for Council Planning Data API

## Executive Summary

I've analyzed GitHub for projects similar to our Council Planning Data Aggregation API. Here's the brutal truth:

**There IS an existing solution that does most of what you want:**
- **PlanningAlerts.org.au** by OpenAustralia Foundation - covers 195 councils (86% of Australia's population)
- They've been doing this for 15+ years with ~200 scrapers on morph.io
- All their code is open source under AGPL-3.0

**Your differentiation opportunity:** They focus on alerts for residents, not commercial API access with enriched data.

---

## CATEGORY 1: DIRECT COMPETITORS / EXISTING SOLUTIONS

### 🔴 PlanningAlerts Ecosystem (THE MAIN COMPETITOR)

| Repository | Purpose | Stars | Status | Relevance |
|------------|---------|-------|--------|-----------|
| [openaustralia/planningalerts](https://github.com/openaustralia/planningalerts) | Main Rails app | 81 | Active | **STUDY THIS** |
| [planningalerts-scrapers](https://github.com/planningalerts-scrapers) | ~200 council scrapers | N/A | Active | **FORK THESE** |
| [openaustralia/atdis](https://github.com/openaustralia/atdis) | ATDIS API client (Ruby) | 2 | Maintained | Useful |
| [openaustralia/morph](https://github.com/openaustralia/morph) | Scraper hosting platform | 455 | Active | Learn from |

**What PlanningAlerts has that you can leverage:**
- 195+ working scrapers for Australian councils
- ATDIS (Application Tracking Data Interchange Specification) implementation
- Field schema already defined
- Years of battle-tested patterns for council portal types (Masterview, Civica, Icon, ATDIS, Horizon, Technology One, Epathway)

**What PlanningAlerts DOESN'T have (your opportunity):**
- Commercial-grade API with SLA
- Enriched data (cost ranges, dwelling counts, categories)
- Webhooks for real-time notifications
- Bulk data export
- Historical data beyond 30-90 days
- AI-powered field normalization

---

## CATEGORY 2: ABSOLUTE NO-BRAINERS (Implement Phase 1)

These are repos you can directly use or fork immediately:

### ✅ Phase 1: Core Infrastructure

| Repository | What It Does | Why Use It | Integration Effort |
|------------|--------------|------------|-------------------|
| **[planningalerts-scrapers/*](https://github.com/planningalerts-scrapers)** | 195+ council scrapers | DON'T reinvent the wheel - fork existing scrapers | LOW - Just adapt output format |
| **[openaustralia/atdis](https://github.com/openaustralia/atdis)** | ATDIS spec client | ~30 councils support ATDIS natively | LOW - Ruby gem, port to Python |
| **[minus34/gnaf-loader](https://github.com/minus34/gnaf-loader)** | Australian address database (15M+ addresses) | Geocoding, address validation | MEDIUM - PostgreSQL setup |
| **[jasonrig/address-net](https://github.com/jasonrig/address-net)** | ML-based address parser | Parse messy council addresses | LOW - pip install |
| **[celery/celery](https://github.com/celery/celery)** | Task queue | Orchestrate 200 scrapers | LOW - Standard Python |

### Specific Scraper Patterns to Fork

```
planningalerts-scrapers/
├── melbourne        # City of Melbourne - Civica system
├── yarra            # City of Yarra - similar pattern
├── spear            # Victoria SPEAR system (covers most of VIC)
├── saplanningportal # SA Planning Portal (covers all SA)
├── perth            # City of Perth
├── launceston       # Tasmania example
├── BCC_DEVELOPMENT_APPLICATIONS  # Brisbane (JavaScript)
└── nsw_joint_regional_planning_panels  # NSW panels
```

**Recommendation:** Fork the entire `planningalerts-scrapers` organization and modernize scrapers from Ruby to Python.

---

## CATEGORY 3: PHASE 2 ENHANCEMENTS

### ⏳ Phase 2: Data Enrichment & Quality

| Repository | What It Does | When to Add | Integration Effort |
|------------|--------------|-------------|-------------------|
| **[yimbymelbourne/council-meeting-agenda-scraper](https://github.com/yimbymelbourne/council-meeting-agenda-scraper)** | Council agenda scraping | When adding meeting context | MEDIUM |
| **[ZacharyHampton/HomeHarvest](https://github.com/ZacharyHampton/HomeHarvest)** | Real estate scraper patterns | Learn structure for property data | LOW - Pattern study |
| **[fgrillo89/real-estate-scraper](https://github.com/fgrillo89/real-estate-scraper)** | Async scraper architecture | Scalable scraper patterns | MEDIUM |
| **[selinon/selinon](https://github.com/selinon/selinon)** | Advanced Celery workflow | Complex scraper DAGs | HIGH |
| **[milan1310/distributed-scrapy-scraping](https://github.com/milan1310/distributed-scrapy-scraping)** | Scrapy + Celery + Redis | Distributed scraping | MEDIUM |

### Address & Geocoding Stack

| Repository | Purpose | Stars | Notes |
|------------|---------|-------|-------|
| [minus34/gnaf-loader](https://github.com/minus34/gnaf-loader) | Load 15M Australian addresses to Postgres | 116 | **ESSENTIAL** for geocoding |
| [jasonrig/address-net](https://github.com/jasonrig/address-net) | ML address parser | 82 | Parse messy council addresses |
| [abcnews/geocoder](https://github.com/abcnews/geocoder) | Browser-based GNAF geocoder | - | Fast client-side geocoding |
| [Addresses-and-Postcodes/au-gnaf-importer](https://github.com/Addresses-and-Postcodes/au-gnaf-importer) | Docker GNAF import | - | Quick setup option |

---

## CATEGORY 4: PHASE 3-4 ADVANCED FEATURES

### 🔮 Phase 3: API & Platform

| Repository | What It Does | When to Add |
|------------|--------------|-------------|
| **[osauldmy/scrapy-mongodb-fastapi-apartments](https://github.com/osauldmy/scrapy-mongodb-fastapi-apartments)** | Full stack: Scrapy → MongoDB → FastAPI | API architecture reference |
| **[yennanliu/web_scraping](https://github.com/yennanliu/web_scraping)** | Celery + Redis + Docker scraper stack | Docker orchestration |
| **[channeng/celery-scheduler](https://github.com/channeng/celery-scheduler)** | Celery + Flask + supervisord | Production scheduler setup |
| **[codingforentrepreneurs/Web-Scraping-with-Django-Celery](https://github.com/codingforentrepreneurs/Web-Scraping-with-Django-Celery)** | Django + Celery scraping | If you prefer Django |

### 🔮 Phase 4: ML & AI Enhancement

| Repository | Purpose | Use Case |
|------------|---------|----------|
| [jasonrig/address-net](https://github.com/jasonrig/address-net) | Address parsing ML model | Parse inconsistent addresses |
| Custom | AI Field Mapper | Map council fields to schema |
| Custom | Category Classifier | Classify DA descriptions |

---

## COMPLETE TECHNOLOGY STACK RECOMMENDATION

Based on the GitHub analysis, here's the optimal stack:

```
┌─────────────────────────────────────────────────────────────────┐
│                    RECOMMENDED ARCHITECTURE                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  SCRAPING LAYER (Fork from PlanningAlerts)                      │
│  ├── planningalerts-scrapers (195 councils) → Port to Python    │
│  ├── ATDIS client → Port openaustralia/atdis to Python          │
│  └── Custom scrapers for remaining ~50 councils                  │
│                                                                  │
│  ORCHESTRATION LAYER (GitHub: celery/celery)                    │
│  ├── Celery + Redis for task queue                              │
│  ├── Celery Beat for scheduling                                 │
│  └── Flower for monitoring                                       │
│                                                                  │
│  DATA LAYER                                                      │
│  ├── PostgreSQL + PostGIS (with GNAF from minus34/gnaf-loader)  │
│  ├── Redis (caching, queues)                                    │
│  └── S3 (raw data archive)                                      │
│                                                                  │
│  ENRICHMENT LAYER                                                │
│  ├── Address parser (jasonrig/address-net)                      │
│  ├── Geocoding (GNAF database)                                  │
│  └── AI Field Mapper (Claude API)                               │
│                                                                  │
│  API LAYER                                                       │
│  ├── FastAPI (reference: osauldmy/scrapy-mongodb-fastapi)       │
│  ├── API key auth                                               │
│  └── Webhooks                                                    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## IMPLEMENTATION ROADMAP BY PHASE

### PHASE 1: Foundation (Weeks 1-4) - NO-BRAINERS

| Week | Task | GitHub Resource |
|------|------|-----------------|
| 1 | Set up PostgreSQL + PostGIS | minus34/gnaf-loader |
| 1 | Fork planningalerts-scrapers | planningalerts-scrapers/* |
| 2 | Set up Celery + Redis | celery/celery |
| 2 | Port 5 VIC SPEAR scrapers | planningalerts-scrapers/spear |
| 3 | Port 5 NSW scrapers | planningalerts-scrapers/nsw_* |
| 3 | Add address parser | jasonrig/address-net |
| 4 | Basic FastAPI | osauldmy/scrapy-mongodb-fastapi |
| 4 | Deploy to AWS | Standard infrastructure |

**Phase 1 GitHub Dependencies:**
```bash
# Core
pip install celery redis fastapi uvicorn

# Scraping
pip install beautifulsoup4 requests playwright

# Data
pip install sqlalchemy psycopg2-binary geoalchemy2

# Address parsing
pip install git+https://github.com/jasonrig/address-net.git
```

### PHASE 2: Scale (Weeks 5-10)

| Week | Task | GitHub Resource |
|------|------|-----------------|
| 5-6 | Port remaining 45 Tier 1 scrapers | planningalerts-scrapers/* |
| 7-8 | Add ATDIS support | openaustralia/atdis (port to Python) |
| 9 | Build AI Field Mapper | Custom (Claude API) |
| 10 | Quality monitoring dashboard | Flower + custom |

### PHASE 3: Coverage (Weeks 11-16)

| Week | Task | GitHub Resource |
|------|------|-----------------|
| 11-12 | Councils 51-100 | planningalerts-scrapers/* |
| 13-14 | Councils 101-150 | Custom + AI generation |
| 15-16 | Historical backfill | Custom |

### PHASE 4: Launch (Weeks 17-20)

| Week | Task | GitHub Resource |
|------|------|-----------------|
| 17 | API hardening | FastAPI best practices |
| 18 | Webhooks system | Custom |
| 19 | Documentation | OpenAPI / Swagger |
| 20 | Beta launch | - |

---

## SCRAPERS BY COUNCIL SYSTEM TYPE

PlanningAlerts has identified these common council portal systems. Each system type needs ONE scraper that can handle multiple councils:

| System | Councils Using It | Example Scraper | Effort to Port |
|--------|-------------------|-----------------|----------------|
| **SPEAR** (VIC) | ~50 VIC councils | planningalerts-scrapers/spear | LOW |
| **NSW ePlanning** | ~40 NSW councils | Custom (API available) | LOW |
| **SA Planning Portal** | All SA councils | planningalerts-scrapers/saplanningportal | LOW |
| **ATDIS** | ~30 councils | openaustralia/atdis | LOW |
| **Civica** | ~20 councils | Various PA scrapers | MEDIUM |
| **Technology One** | ~15 councils | Various PA scrapers | MEDIUM |
| **Epathway** | ~15 councils | Various PA scrapers | MEDIUM |
| **Masterview** | ~10 councils | Various PA scrapers | MEDIUM |
| **Custom portals** | ~20 councils | Individual scrapers | HIGH |

**Key Insight:** Building ONE scraper for SPEAR gives you ~50 Victorian councils instantly. That's 25% of your target with ONE scraper.

---

## CRITICAL SCRAPERS TO FORK FIRST

These PlanningAlerts scrapers cover the most population:

| Council | Population | Scraper Location | System |
|---------|------------|------------------|--------|
| Brisbane | 1.35M | planningalerts-scrapers/BCC_DEVELOPMENT_APPLICATIONS | Custom JS |
| Melbourne | 180K | planningalerts-scrapers/melbourne | Civica |
| Gold Coast | 640K | Need to create | Custom |
| Sydney | 275K | planningalerts-scrapers/sydney (check) | Custom |
| Blacktown | 415K | Via NSW ePlanning | API |
| Parramatta | 265K | Via NSW ePlanning | API |

---

## WHAT'S MISSING FROM GITHUB (Build Yourself)

These don't exist on GitHub and represent your differentiation:

1. **AI Field Mapper** - Maps council-specific fields to unified schema
2. **DA Category Classifier** - Classifies "New dwelling" vs "Multi-unit" etc.
3. **Cost Estimator** - Extracts/estimates project costs from descriptions
4. **Commercial API Layer** - Webhooks, rate limiting, SLA monitoring
5. **Data Quality Scoring** - Confidence scores for each record

---

## SIMILAR PROJECTS (Not Direct Competitors)

| Project | What It Does | Relevance |
|---------|--------------|-----------|
| [Searchland (UK)](https://searchland.co.uk) | UK planning data | Competitor model to study |
| [Glenigan (UK)](https://www.glenigan.com) | UK construction leads | Revenue model reference |
| [HomeHarvest](https://github.com/ZacharyHampton/HomeHarvest) | US real estate scraping | Code quality reference |
| [Cordell Connect](https://www.cordellconnect.com.au) | AU construction leads | Direct competitor (CoreLogic) |

---

## FINAL RECOMMENDATIONS

### DO THIS IMMEDIATELY:

1. **Fork `planningalerts-scrapers`** - Don't reinvent 195 wheels
2. **Study the PlanningAlerts schema** - Compatible data = easier adoption
3. **Start with SPEAR** - One scraper = 50 councils
4. **Use GNAF for geocoding** - Free, comprehensive, official

### DON'T DO THIS:

1. ❌ Build scrapers from scratch when PA has working ones
2. ❌ Ignore the ATDIS spec (it's the official standard)
3. ❌ Use a non-standard schema (follow PA for ecosystem compatibility)
4. ❌ Underestimate maintenance (scrapers break constantly)

### YOUR COMPETITIVE MOAT:

| PA Has | You Should Add |
|--------|----------------|
| Basic alerts | Commercial API with SLA |
| Raw council data | AI-enriched, normalized data |
| Free for residents | Paid tiers for businesses |
| ~195 councils | 200+ councils |
| Email alerts only | Webhooks + bulk API |
| No historical depth | 12+ months history |

---

## EFFORT ESTIMATE REVISION

With the GitHub ecosystem leverage:

| Original Estimate | Revised with GitHub Leverage |
|-------------------|------------------------------|
| 630 hours development | ~350 hours (44% reduction) |
| 4-5 months part-time | 2.5-3 months part-time |
| $31,500 dev cost | ~$17,500 dev cost |

**Why the reduction:**
- 195 scrapers already exist (don't rewrite)
- GNAF loader is production-ready
- Celery patterns are well-documented
- Address parsing is solved
- ATDIS spec implementation exists

The hard work is ALREADY DONE by the open-source community. Your job is to:
1. Fork and modernize
2. Add commercial features
3. Improve data quality with AI
4. Build the business layer
