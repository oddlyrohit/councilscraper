# Council DA Scraper Platform

A comprehensive platform for aggregating development application (DA) data from 200+ Australian local councils into a unified, commercially licensable dataset.

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](BUILD_SUMMARY.md)
[![Python](https://img.shields.io/badge/python-3.11+-green.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## Features

- **200+ Council Coverage** - Scrapers for all major Australian councils
- **AI Field Mapping** - Claude-powered intelligent field normalization
- **Geospatial Search** - PostGIS-enabled location queries
- **Real-time Webhooks** - Get notified of new applications
- **Distributed Scraping** - Celery workers with browser automation
- **REST API** - FastAPI with automatic OpenAPI docs

## Quick Start

### Local Development

```bash
# Clone repository
git clone https://github.com/oddlyrohit/councilscraper.git
cd councilscraper

# Copy environment config
cp env.example .env
# Edit .env with your API keys (ANTHROPIC_API_KEY required)

# Start with Docker
docker-compose up -d

# Or use Make commands
make dev
```

### Access Services

| Service | URL |
|---------|-----|
| API Docs | http://localhost:8000/docs |
| Health Check | http://localhost:8000/health |
| Flower (Task Monitor) | http://localhost:5555 |

## API Endpoints

### Applications

```bash
# List applications
GET /applications?council=SYDNEY&status=lodged&limit=50

# Search applications
GET /search?q=residential+dwelling&category=residential

# Geo search
GET /applications/near?lat=-33.8688&lng=151.2093&radius_km=5

# Get single application
GET /applications/{id}
```

### Councils

```bash
# List all councils
GET /councils?state=NSW&tier=1

# Get council details
GET /councils/SYDNEY

# Council statistics
GET /councils/SYDNEY/stats
```

### Admin (requires API key)

```bash
# Trigger scrape
POST /admin/scrape
{
  "council_code": "SYDNEY",
  "mode": "active"
}

# Trigger tier scrape
POST /admin/scrape/tier/1

# Check task status
GET /admin/tasks/{task_id}
```

### Webhooks

```bash
# Register webhook
POST /webhooks
{
  "url": "https://your-server.com/webhook",
  "councils": ["SYDNEY", "MELBOURNE"],
  "categories": ["residential"]
}
```

## Deployment on Render

### One-Click Deploy

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/oddlyrohit/councilscraper)

### Manual Setup

1. **Create Services on Render Dashboard:**

   - **Web Service** (API)
     - Runtime: Python 3.11
     - Build: `pip install -e .`
     - Start: `uvicorn src.api.main:app --host 0.0.0.0 --port $PORT`

   - **Background Worker** (Celery)
     - Runtime: Python 3.11
     - Build: `pip install -e . && pip install playwright && playwright install chromium --with-deps`
     - Start: `celery -A src.orchestrator.celery_app worker --loglevel=info`

   - **Cron Worker** (Scheduler)
     - Start: `celery -A src.orchestrator.celery_app beat --loglevel=info`

2. **Create Databases:**

   - PostgreSQL (Render managed or external with PostGIS)
   - Redis (Render managed)

3. **Set Environment Variables:**

   ```
   DATABASE_URL=postgresql://...
   REDIS_URL=redis://...
   ANTHROPIC_API_KEY=sk-ant-...
   SECRET_KEY=<generated>
   ```

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `REDIS_URL` | Yes | Redis connection string |
| `ANTHROPIC_API_KEY` | Yes | Claude API key for AI mapping |
| `GOOGLE_MAPS_API_KEY` | No | For geocoding (Nominatim fallback) |
| `SECRET_KEY` | Yes | JWT signing key |
| `LOG_LEVEL` | No | INFO, DEBUG, WARNING |

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Clients                             │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI (Render Web)                     │
│         /applications  /councils  /search  /admin           │
└─────────────────────────┬───────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│  PostgreSQL │   │    Redis    │   │   Claude    │
│  (+ PostGIS)│   │   (Broker)  │   │     API     │
└─────────────┘   └──────┬──────┘   └─────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Celery Workers (Render Background)             │
│    ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐      │
│    │   NSW   │  │   VIC   │  │   QLD   │  │   ...   │      │
│    │ Scraper │  │ Scraper │  │ Scraper │  │         │      │
│    └─────────┘  └─────────┘  └─────────┘  └─────────┘      │
└─────────────────────────────────────────────────────────────┘
```

## Project Structure

```
councilscraper/
├── src/
│   ├── api/              # FastAPI application
│   │   ├── main.py
│   │   └── routes/       # API endpoints
│   ├── config/           # Settings and council registry
│   ├── mappers/          # AI field mapping
│   ├── models/           # SQLAlchemy models
│   ├── orchestrator/     # Celery tasks
│   ├── scrapers/         # State-specific scrapers
│   │   ├── base/         # Abstract adapter
│   │   ├── nsw/          # NSW ePlanning
│   │   ├── vic/          # VIC SPEAR
│   │   ├── qld/          # QLD Development.i
│   │   └── ...
│   ├── services/         # Geocoding, enrichment
│   └── storage/          # Database manager
├── docker-compose.yml
├── render.yaml           # Render deployment config
└── Makefile
```

## Development

```bash
# Install dependencies
pip install -e ".[dev]"

# Run tests
make test

# Lint code
make lint

# Format code
make format
```

## Scraping Commands

```bash
# Scrape single council
make scrape COUNCIL=SYDNEY

# Scrape all tier 1 councils (major metros)
make scrape-tier1

# Historical backfill
make backfill COUNCIL=SYDNEY START=2024-01-01 END=2024-12-31
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

Built with ❤️ for Australian planning data transparency.
