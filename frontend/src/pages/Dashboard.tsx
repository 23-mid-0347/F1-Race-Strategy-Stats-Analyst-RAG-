import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  getEvents,
  getDriverCount,
  getConstructorCount,
  getConstructorStandings,
  getDriverWins,
} from "../services/api";
import type { EventSummary, ConstructorStanding, DriverWin } from "../services/api";
import {
  ArrowRight,
  Bot,
  CalendarDays,
  Flag,
  Gauge,
  Trophy,
  Users,
} from "lucide-react";
import StatCard from "../components/StatCard";
import LoadingSpinner from "../components/LoadingSpinner";

// F1 constructor colors
const CONSTRUCTOR_COLORS: Record<string, string> = {
  "Red Bull Racing": "#3671C6",
  "Mercedes":        "#27F4D2",
  "Ferrari":         "#E8002D",
  "McLaren":         "#FF8000",
  "Aston Martin":    "#358C75",
  "Alpine":          "#FF87BC",
  "Williams":        "#64C4FF",
  "AlphaTauri":      "#5E8FAA",
  "Alfa Romeo":      "#C92D4B",
  "Haas F1 Team":    "#B6BABD",
};

function formatDate(d: string | null): string {
  if (!d) return "—";
  return new Date(d).toLocaleDateString("en-GB", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

export default function Dashboard() {
  const navigate = useNavigate();

  // Stat counts
  const [raceCount, setRaceCount] = useState(0);
  const [driverCount, setDriverCount] = useState(0);
  const [constructorCount, setConstructorCount] = useState(0);
  const [statsLoading, setStatsLoading] = useState(true);

  // Race schedule panel
  const [events, setEvents] = useState<EventSummary[]>([]);
  const [eventsLoading, setEventsLoading] = useState(true);

  // Constructor standings panel
  const [standings, setStandings] = useState<ConstructorStanding[]>([]);
  const [standingsLoading, setStandingsLoading] = useState(true);

  // Driver wins panel
  const [driverWins, setDriverWins] = useState<DriverWin[]>([]);
  const [winsLoading, setWinsLoading] = useState(true);

  useEffect(() => {
    // Stat cards
    Promise.all([
      getEvents(2023, 1, 0),
      getDriverCount(2023),
      getConstructorCount(2023),
    ])
      .then(([evData, drData, ctData]) => {
        setRaceCount(evData.total);
        setDriverCount(drData.count);
        setConstructorCount(ctData.count);
      })
      .finally(() => setStatsLoading(false));

    // Race schedule (first 6)
    getEvents(2023, 6, 0)
      .then((d) => setEvents(d.items))
      .finally(() => setEventsLoading(false));

    // Constructor standings (top 5)
    getConstructorStandings(2023)
      .then((d) => setStandings(d.slice(0, 5)))
      .finally(() => setStandingsLoading(false));

    // Driver wins (top 5)
    getDriverWins(2023)
      .then((d) => setDriverWins(d.slice(0, 5)))
      .finally(() => setWinsLoading(false));
  }, []);

  const maxWins = driverWins[0]?.wins ?? 1;
  const maxPts = standings[0]?.total_points ?? 1;

  return (
    <div className="dashboard">
      {/* ── Heading ──────────────────────────────────────────────────── */}
      <section className="page-heading">
        <div>
          <span className="eyebrow">2023 SEASON</span>
          <h2>Race Intelligence</h2>
          <p>Monitor race performance, driver statistics and strategy insights.</p>
        </div>
        <div className="heading-badge">
          <CalendarDays size={14} />
          2023 Season
        </div>
      </section>

      {/* ── Stat cards ───────────────────────────────────────────────── */}
      <section className="stats-grid">
        <StatCard
          label="Races"
          value={raceCount}
          subtext="2023 season"
          icon={Flag}
          loading={statsLoading}
        />
        <StatCard
          label="Drivers"
          value={driverCount}
          subtext="Active competitors"
          icon={Users}
          loading={statsLoading}
        />
        <StatCard
          label="Constructors"
          value={constructorCount}
          subtext="Teams entered"
          icon={Trophy}
          loading={statsLoading}
        />
        <StatCard
          label="Lap Records"
          value="24,420"
          subtext="Lap times logged"
          icon={Gauge}
          loading={false}
        />
      </section>

      {/* ── Main panels ──────────────────────────────────────────────── */}
      <section className="dashboard-grid">

        {/* Race schedule */}
        <div className="panel">
          <div className="panel-header">
            <div>
              <span className="eyebrow">SEASON OVERVIEW</span>
              <h3>Race Schedule</h3>
            </div>
            <button className="text-button" onClick={() => navigate("/races")}>
              View all
            </button>
          </div>

          {eventsLoading ? (
            <div className="panel-loading">
              <LoadingSpinner />
            </div>
          ) : (
            <div className="race-list">
              {events.map((ev) => (
                <div
                  className="race-row"
                  key={ev.event_id}
                  onClick={() => navigate(`/races/${ev.event_id}`)}
                  style={{ cursor: "pointer" }}
                  id={`dash-race-${ev.event_id}`}
                >
                  <div className="race-round">R{String(ev.round).padStart(2, "0")}</div>
                  <div className="race-info">
                    <strong>{ev.event_name}</strong>
                    <span>{ev.circuit_name ?? "—"}</span>
                  </div>
                  <div className="race-date">{formatDate(ev.event_date)}</div>
                  <ArrowRight size={15} className="row-arrow" />
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Right column */}
        <div className="right-col">
          {/* Constructor standings mini-panel */}
          <div className="panel" style={{ marginBottom: 18 }}>
            <div className="panel-header">
              <div>
                <span className="eyebrow">CHAMPIONSHIP</span>
                <h3>Constructor Points</h3>
              </div>
              <button className="text-button" onClick={() => navigate("/standings")}>
                Full table
              </button>
            </div>

            {standingsLoading ? (
              <div className="panel-loading">
                <LoadingSpinner />
              </div>
            ) : (
              <div className="mini-list">
                {standings.map((c, i) => {
                  const color = CONSTRUCTOR_COLORS[c.name] ?? "#555961";
                  return (
                    <div className="mini-row" key={c.name}>
                      <span className="rank-num" style={{ color }}>{i + 1}</span>
                      <div className="mini-row-info">
                        <span
                          className="constructor-dot"
                          style={{ background: color }}
                        />
                        <span className="mini-row-name">{c.name}</span>
                      </div>
                      <div className="mini-bar-wrap">
                        <div
                          className="mini-bar-fill"
                          style={{
                            width: `${(c.total_points / maxPts) * 100}%`,
                            background: color,
                          }}
                        />
                      </div>
                      <span className="mini-row-val">{c.total_points}</span>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Driver wins mini-panel */}
          <div className="panel" style={{ marginBottom: 18 }}>
            <div className="panel-header">
              <div>
                <span className="eyebrow">DRIVER WINS</span>
                <h3>Top Winners</h3>
              </div>
              <button className="text-button" onClick={() => navigate("/standings")}>
                Full table
              </button>
            </div>

            {winsLoading ? (
              <div className="panel-loading">
                <LoadingSpinner />
              </div>
            ) : (
              <div className="mini-list">
                {driverWins.map((d, i) => (
                  <div className="mini-row" key={d.full_name}>
                    <span className="rank-num">{i + 1}</span>
                    <span className="mini-row-name" style={{ flex: 1 }}>
                      {d.full_name}
                    </span>
                    <div className="mini-bar-wrap">
                      <div
                        className="mini-bar-fill"
                        style={{ width: `${(d.wins / maxWins) * 100}%` }}
                      />
                    </div>
                    <span className="mini-row-val">{d.wins}W</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* AI Analyst CTA */}
          <div className="panel analyst-panel">
            <div className="panel-header">
              <div>
                <span className="eyebrow">AI ANALYST</span>
                <h3>Race Strategy Assistant</h3>
              </div>
            </div>
            <div className="analyst-content">
              <div className="analyst-orb">
                <Bot size={25} strokeWidth={1.4} />
              </div>
              <p>
                Ask questions about race pace, tyre strategy, driver performance,
                pit stops and historical F1 data.
              </p>
              <button className="analyst-button" onClick={() => navigate("/analyst")}>
                Open AI Analyst
                <ArrowRight size={16} />
              </button>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}