# F1 Hybrid RAG Analytics Assistant

A hybrid RAG (Retrieval-Augmented Generation) analytics platform that answers both **stats questions** ("Which driver had the most points in 2023?") and **narrative questions** ("Why did Ferrari's strategy fail at Singapore?") about Formula 1, by combining structured SQL data with unstructured race reports (vector search).

**Current state:** Phases 1–6 complete. The full 2023 season is loaded into Postgres, a FastAPI backend serves 9 validated endpoints, and a React dashboard displays live data with zero hardcoded values.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Database | PostgreSQL 18 (`f1_analytics`) |
| ORM | SQLAlchemy ≥2.0.44 |
| DB Driver | psycopg v3 (`psycopg[binary]`) |
| Data source | FastF1 ≥3.7.0 → Jolpica API |
| Backend | FastAPI ≥0.115 · Uvicorn ≥0.32 |
| Frontend | React 19 · TypeScript · Vite |
| Charts | Recharts |
| HTTP client | Axios |
| Language | Python 3.14 |

---

## Project Structure

```
f1_data_pipeline/
├── backend/
│   ├── api/              FastAPI app (main.py, schemas.py, dependencies.py)
│   ├── database/         SQLAlchemy models, connection layer, schema.sql
│   ├── ingestion/        6 ETL scripts (schedule, results, laps, pitstops, stints, weather)
│   ├── rag/              Phase 7-8 — empty, reserved for vector DB + RAG
│   ├── tests/            smoke_test.py (43 checks — DB + API + frontend)
│   ├── .env              DB credentials (gitignored)
│   ├── .env.example      Template
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/   Sidebar, TopBar, StatCard, LoadingSpinner, ConstructorChart
│   │   ├── pages/        Dashboard, Standings, Races, RaceDetail, ComingSoon
│   │   └── services/     api.ts — typed Axios client for all 9 endpoints
│   └── package.json
└── Docs/
    ├── F1_RAG_Project_Plan_Updated-phase-6.md   ← current project plan
    └── F1_API_Frontend_Guide.md                  ← API contract reference
```

---

## Prerequisites

- Python 3.14 with a virtual environment at `.venv/`
- PostgreSQL 18 running locally (Homebrew: `brew services start postgresql@18`)
- Node.js 20+ and npm

---

## 1 — Database Setup

```bash
# Create the database
createdb f1_analytics

# Activate the virtual environment
source .venv/bin/activate

# Install Python dependencies
pip install -r backend/requirements.txt

# Create all 13 tables
cd backend
python database/init_db.py
```

---

## 2 — Load the 2023 Season

Run the ETL scripts in order. `fetch_schedule.py` must run first; the rest can run in any order.

```bash
cd backend
python ingestion/fetch_schedule.py 2023    # seasons, circuits, events, sessions
python ingestion/fetch_results.py 2023     # Race AND Sprint results
python ingestion/fetch_laps.py 2023        # lap-by-lap timing (24,420 rows)
python ingestion/fetch_pitstops.py 2023    # pit stop events (943 rows)
python ingestion/fetch_stints.py 2023      # tyre stints (1,348 rows)
python ingestion/fetch_weather.py 2023     # session weather (3,619 rows)
```

> **Note:** First run is slow — FastF1 fetches and caches each session from Jolpica (expect 5–10 min total). Re-runs are fast because data is cached locally in `fastf1_cache/`.

> **Note:** Every script uses `ON CONFLICT ... DO UPDATE` upserts — safe to re-run without creating duplicates.

---

## 3 — Start the Backend

```bash
cd backend
../.venv/bin/python -m uvicorn api.main:app --host 127.0.0.1 --port 8000
```

The API will be live at `http://127.0.0.1:8000`. Check:

```bash
curl http://127.0.0.1:8000/health
# → {"status":"ok","database":"connected"}
```

---

## 4 — Start the Frontend

```bash
cd frontend
npm install        # first time only
npm run dev
# → http://localhost:5173
```

---

## 5 — API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | API + DB connectivity check |
| `GET` | `/constructors/standings?season=2023` | Championship points (Race + Sprint) |
| `GET` | `/constructors/count?season=2023` | Number of constructors |
| `GET` | `/drivers/wins?season=2023` | Win counts per driver (Race only) |
| `GET` | `/drivers/podiums?season=2023` | Podium counts per driver (Race only) |
| `GET` | `/drivers/count?season=2023` | Number of drivers |
| `GET` | `/drivers/{id}` | Driver profile |
| `GET` | `/drivers/{id}/stats?season=2023` | Wins / podiums / poles / DNFs / avg finish |
| `GET` | `/events?season=2023&limit=22` | Paginated race calendar |
| `GET` | `/events/{event_id}/results` | Full race classification |
| `GET` | `/sessions/{session_id}/fastest-lap` | Fastest lap of a session |

All `season` params are optional — omitting returns all seasons combined.

---

## 6 — Run the Smoke Test

Requires both servers running (`port 8000` and `port 5173`):

```bash
cd backend
../.venv/bin/python tests/smoke_test.py
```

Expected output: **43 passed, 0 failed** — covers database row counts, all API endpoints with real-value assertions, CORS headers, pagination, and the frontend dev server.

---

## 7 — Validated Data (2023 Season)

| Metric | Value |
|---|---|
| Races | 22 |
| Sprint rounds | 6 |
| Drivers | 22 |
| Constructors | 10 |
| Results | 560 |
| Lap times | 24,420 |
| Pit stops | 943 |
| Stints | 1,348 |
| Weather rows | 3,619 |

Constructor standings match the official 2023 F1 results exactly:
**Red Bull 860 · Mercedes 409 · Ferrari 406 · McLaren 302 · Aston Martin 280 · Alpine 120 · Williams 28 · AlphaTauri 25 · Alfa Romeo 16 · Haas 12**

---

## Roadmap

| Phase | Status |
|---|---|
| Phase 1 — Database Architecture | ✅ Done |
| Phase 2 — FastF1 ETL | ✅ Done |
| Phase 3 — Historical Data (2023) | ✅ Done |
| Phase 4 — SQL Analytics | ✅ Done |
| Phase 5 — FastAPI (9 endpoints) | ✅ Done |
| Phase 6 — React Dashboard | ✅ Done |
| Phase 7 — Vector Database (Chroma) | ⏳ Next |
| Phase 8 — RAG + LLM synthesis | ⏳ Planned |
| Phase 9 — Docker | ⏳ Planned |
| Phase 10 — Cloud Deployment | ⏳ Planned |
| Phase 11 — Evaluation | ⏳ Planned |

See [`Docs/F1_RAG_Project_Plan_Updated-phase-6.md`](Docs/F1_RAG_Project_Plan_Updated-phase-6.md) for the full project plan.