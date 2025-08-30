# DynaLinks · Dynamic Link Service

A production-ready alternative to Firebase Dynamic Links. Create short links with platform-aware redirects, deep linking, and built-in analytics.

## ✨ Highlights

- **Smart redirects**: iOS, Android, and Desktop
- **Deep links** with JS-based app detection and graceful fallbacks
- **Analytics**: clicks by platform, referrer, and geolocation (optional)
- **Privacy**: IPs are hashed before storage
- **Fast**: Async FastAPI + PostgreSQL + Redis
- **Docs**: OpenAPI available at `/docs`

## 🚀 Quick Start

### Docker (recommended)
```bash
git clone <repository-url>
cd dynalinks
just db-init        # starts Docker and loads schema
just run            # starts API with auto-reload
```
Open: `http://localhost:8000/docs`

### Manual
```bash
just setup          # creates venv and installs deps
createdb dynalinks
psql dynalinks < schema.sql
redis-server        # or use Docker
just run
```

## ⚙️ Configuration (.env)

```env
# Required
DATABASE_URL=postgresql://username:password@localhost:5432/dynalinks
REDIS_URL=redis://localhost:6379/0
BASE_DOMAIN=https://yourdomain.com
SHORT_DOMAIN=https://dl.yourdomain.com
SECRET_KEY=change-me

# Optional
ENABLE_ANALYTICS=true
# If set, enables country/region/city analytics
GEOIP_DB_PATH=./data/GeoLite2-City.mmdb

ENVIRONMENT=development
DEBUG=true
RATE_LIMIT_PER_MINUTE=60
```

## 🌍 GeoIP2 / GeoLite2 (optional)

GeoIP2 provides country/region/city from an IP address for analytics. This project uses the free MaxMind GeoLite2 City database when `GEOIP_DB_PATH` is configured.

Setup (requires free MaxMind signup):
- Create an account at the MaxMind site: `https://dev.maxmind.com/geoip/geolite2-free-geolocation-data`
- Generate a License Key in your account
- Download the GeoLite2 City database and extract the `.mmdb` file:
  ```bash
  mkdir -p ./data && cd ./data
  curl -L "https://download.maxmind.com/app/geoip_download?edition_id=GeoLite2-City&license_key=YOUR_LICENSE_KEY&suffix=tar.gz" -o GeoLite2-City.tar.gz
  tar -xzf GeoLite2-City.tar.gz
  mv GeoLite2-City_*/GeoLite2-City.mmdb ./
  rm -rf GeoLite2-City_* GeoLite2-City.tar.gz
  ```
- Set `GEOIP_DB_PATH=./data/GeoLite2-City.mmdb` in `.env` and restart the app

Notes:
- Database size ~60–100MB on disk; with the default code it is opened per lookup (no persistent RAM usage). You can keep a reader open to trade ~100MB RAM for faster lookups.
- If `GEOIP_DB_PATH` is unset, location fields are stored as `NULL` and analytics still work.

## 📖 API

- Explore and try endpoints in the interactive docs: `http://localhost:8000/docs`
- Create a link (example):
  ```bash
  curl -X POST "http://localhost:8000/api/v1/links/" \
    -H "Content-Type: application/json" \
    -d '{"fallback_url": "https://example.com", "ios_url": "myapp://x", "android_url": "myapp://x"}'
  ```
- Redirect endpoint: `GET /{short_code}`
- Analytics endpoint: `GET /api/v1/analytics/{short_code}`

## 🧰 Tech Stack

- FastAPI, asyncpg, PostgreSQL, Redis
- Pydantic for config and schemas
- Deployed via Docker/Kubernetes (see `k8s-manifests.yaml`)

## 🧪 Tests

```bash
just test    # or: pytest
```

## 🤝 Contributing

PRs welcome! Please add tests where applicable and run `just test` before submitting.

## 📄 License

MIT — see `LICENSE`.