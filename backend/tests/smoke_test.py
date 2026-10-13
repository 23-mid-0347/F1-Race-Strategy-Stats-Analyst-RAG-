"""
Smoke test for the whole stack: database -> API -> frontend.

Run from the backend/ folder, with the API already running in another terminal:
    cd backend
    python tests/smoke_test.py

Prints PASS/FAIL per check and exits with code 1 if anything failed.
Expected values are the ones we validated by hand against the official 2023 season
(e.g. Red Bull 860 constructor points, Verstappen 19 wins, Zhou's Bahrain fastest lap).
"""
import json
import os
import sys
import urllib.error
import urllib.request

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

API = os.getenv("API_URL", "http://127.0.0.1:8000")
FRONTEND_URLS = ["http://localhost:5173", "http://localhost:5174"]

passed = 0
failed = 0


def check(name, ok, detail=""):
    global passed, failed
    if ok:
        passed += 1
    else:
        failed += 1
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f"  ({detail})" if detail else ""))


def call(path, method="GET", headers=None):
    """Returns (status, json_body, lowercase_headers). Never raises; status is None if unreachable."""
    req = urllib.request.Request(API + path, method=method, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read().decode()
            try:
                body = json.loads(raw) if raw else None
            except ValueError:
                body = raw  # not JSON (e.g. the plain-text "OK" of a CORS preflight)
            return resp.status, body, {k.lower(): v for k, v in resp.headers.items()}
    except urllib.error.HTTPError as e:
        try:
            body = json.loads(e.read().decode())
        except Exception:
            body = None
        return e.code, body, {k.lower(): v for k, v in e.headers.items()}
    except Exception as e:
        return None, str(e), {}


def check_endpoint(path, test, label=None, expected_status=200):
    """Calls path, checks the HTTP status, then (optionally) runs test(body) -> bool."""
    status, body, _ = call(path)
    ok = status == expected_status
    detail = f"HTTP {status}" if not ok else ""
    if ok and test is not None:
        try:
            ok = bool(test(body))
        except Exception as e:
            ok = False
            detail = f"unexpected response shape: {type(e).__name__}"
        if not ok and not detail:
            detail = f"got: {str(body)[:150]}"
    check(label or f"GET {path}", ok, detail)


# ---------------------------------------------------------------- 1. DATABASE
print("\n1. DATABASE")
bahrain_race_session_id = None
try:
    from sqlalchemy import text
    from database.connection import get_engine

    min_rows = {
        "seasons": 1, "circuits": 20, "events": 22, "sessions": 100,
        "drivers": 20, "constructors": 10, "results": 500,
        "lap_times": 20000, "pit_stops": 300, "stints": 500, "weather": 2000,
    }
    with get_engine().connect() as conn:
        check("connected to the database", True)

        for table, minimum in min_rows.items():
            n = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar_one()
            check(f"{table}: at least {minimum} rows", n >= minimum, f"found {n}")

        nan_points = conn.execute(text("SELECT COUNT(*) FROM results WHERE points = 'NaN'")).scalar_one()
        check("no NaN values in results.points", nan_points == 0, f"found {nan_points}")

        # Every event should have Race data in each of these tables (catches a skipped round)
        for label, table in [("results", "results"), ("lap times", "lap_times"),
                             ("stints", "stints"), ("weather", "weather")]:
            missing = conn.execute(text(f"""
                SELECT COUNT(*) FROM events e
                WHERE NOT EXISTS (
                    SELECT 1 FROM {table} t
                    JOIN sessions s ON s.session_id = t.session_id
                    WHERE s.event_id = e.event_id AND s.session_type = 'Race'
                )
            """)).scalar_one()
            check(f"every event has Race {label}", missing == 0, f"{missing} events missing")

        row = conn.execute(text("""
            SELECT s.session_id FROM sessions s
            JOIN events e ON e.event_id = s.event_id
            JOIN seasons se ON se.season_id = e.season_id
            WHERE se.year = 2023 AND e.round = 1 AND s.session_type = 'Race'
        """)).first()
        bahrain_race_session_id = row[0] if row else None
except Exception as e:
    check("database checks", False, f"{type(e).__name__}: {str(e)[:150]}")

# --------------------------------------------------------------------- 2. API
print(f"\n2. API  ({API})")
status, body, _ = call("/health")
if status is None:
    check("API reachable", False, "start it first: cd backend && uvicorn api.main:app --reload")
else:
    check("GET /health", status == 200 and body.get("database") == "connected", f"HTTP {status}")

    # Known-answer checks (values validated against the official 2023 season)
    pts = lambda b: {r["name"]: r["total_points"] for r in b}
    check_endpoint("/constructors/standings?season=2023",
                   lambda b: (pts(b).get("Red Bull Racing"), pts(b).get("Mercedes"), pts(b).get("Ferrari")) == (860, 409, 406),
                   "constructor standings: Red Bull 860, Mercedes 409, Ferrari 406")
    wins = lambda b: {r["full_name"]: r["wins"] for r in b}
    check_endpoint("/drivers/wins?season=2023",
                   lambda b: wins(b) == {"Max Verstappen": 19, "Sergio Perez": 2, "Carlos Sainz": 1},
                   "driver wins: Verstappen 19, Perez 2, Sainz 1")
    pods = lambda b: {r["full_name"]: r["podiums"] for r in b}
    check_endpoint("/drivers/podiums?season=2023",
                   lambda b: pods(b).get("Max Verstappen") == 21,
                   "podiums: Verstappen 21")
    check_endpoint("/drivers/count?season=2023", lambda b: b["count"] == 22, "driver count = 22")
    check_endpoint("/constructors/count?season=2023", lambda b: b["count"] == 10, "constructor count = 10")
    check_endpoint("/events?season=2023&limit=5&offset=20",
                   lambda b: b["total"] == 22 and len(b["items"]) == 2,
                   "events pagination: total 22, last page has 2")
    check_endpoint("/events/1/results",
                   lambda b: len(b["results"]) == 20 and b["results"][0]["driver_code"] == "VER" and b["results"][0]["points"] == 25,
                   "Bahrain results: 20 drivers, Verstappen P1 with 25 pts")
    check_endpoint("/drivers/1", lambda b: b["driver_code"] == "VER", "driver 1 is VER")
    check_endpoint("/drivers/1/stats?season=2023",
                   lambda b: (b["races"], b["wins"], b["podiums"], b["poles"]) == (22, 19, 21, 12),
                   "Verstappen 2023: 22 races, 19 wins, 21 podiums, 12 poles")
    if bahrain_race_session_id:
        check_endpoint(f"/sessions/{bahrain_race_session_id}/fastest-lap",
                       lambda b: b["full_name"] == "Guanyu Zhou" and abs(b["lap_time_ms"] - 93996) <= 1,
                       "Bahrain fastest lap: Zhou, 93996 ms (+/- 1 ms for the rounding fix)")

    # Regression check for the psycopg v3 bug: every filterable endpoint with season OMITTED
    for path in ["/constructors/standings", "/constructors/count", "/drivers/wins",
                 "/drivers/podiums", "/drivers/count", "/events", "/drivers/1/stats"]:
        check_endpoint(path, None, f"GET {path}  (season omitted)")

    # Error handling
    check_endpoint("/drivers/999999", None, "unknown driver -> 404", expected_status=404)
    check_endpoint("/events/999999/results", None, "unknown event -> 404", expected_status=404)
    check_endpoint("/sessions/999999/fastest-lap", None, "unknown session -> 404", expected_status=404)
    check_endpoint("/events?limit=0", None, "limit=0 rejected -> 422", expected_status=422)
    check_endpoint("/drivers/wins?season=1950", lambda b: b == [], "season with no data -> empty list, not an error")

    # CORS: can the React dev server call this API?
    for origin in FRONTEND_URLS:
        s, _, headers = call("/drivers/1", method="OPTIONS",
                             headers={"Origin": origin, "Access-Control-Request-Method": "GET"})
        check(f"CORS allows {origin}", headers.get("access-control-allow-origin") == origin, f"HTTP {s}")

# ---------------------------------------------------------------- 3. FRONTEND
print("\n3. FRONTEND  (optional)")
reachable = []
for url in FRONTEND_URLS:
    try:
        urllib.request.urlopen(url, timeout=3)
        reachable.append(url)
    except Exception:
        pass
if reachable:
    check("frontend dev server is running", True, reachable[0])
else:
    print("  [SKIP] dev server not running (start it with: cd frontend && npm run dev)")

print(f"\n{passed} passed, {failed} failed")
sys.exit(1 if failed else 0)