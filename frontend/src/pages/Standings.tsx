import { useEffect, useState } from "react";
import {
  getConstructorStandings,
  getDriverWins,
  getDriverPodiums,
} from "../services/api";
import type {
  ConstructorStanding,
  DriverWin,
  DriverPodium,
} from "../services/api";
import ConstructorChart from "../components/ConstructorChart";
import LoadingSpinner from "../components/LoadingSpinner";
import { Medal, Trophy, BarChart2 } from "lucide-react";
import { useActiveSeason } from "../hooks/useActiveSeason";

type Tab = "constructors" | "drivers";

// F1 constructor colors for the standings table rank indicator
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

export default function Standings() {
  const season = useActiveSeason();
  const [tab, setTab] = useState<Tab>("constructors");
  const [error, setError] = useState<string | null>(null);
  const [standings, setStandings] = useState<ConstructorStanding[]>([]);
  const [wins, setWins] = useState<DriverWin[]>([]);
  const [podiums, setPodiums] = useState<DriverPodium[]>([]);
  const [loadedSeason, setLoadedSeason] = useState<number | null>(null);
  const loading = loadedSeason !== season;

  useEffect(() => {
    let cancelled = false;
    Promise.all([
      getConstructorStandings(season),
      getDriverWins(season),
      getDriverPodiums(season),
    ])
      .then(([s, w, p]) => {
        if (cancelled) return;
        setStandings(s);
        setWins(w);
        setPodiums(p);
        setError(null);
        setLoadedSeason(season);
      })
      .catch(() => {
        if (cancelled) return;
        setStandings([]);
        setWins([]);
        setPodiums([]);
        setError("Could not load standings. Check the backend connection and whether this season results have been ingested.");
        setLoadedSeason(season);
      });
    return () => { cancelled = true; };
  }, [season]);

  const maxPoints = standings[0]?.total_points ?? 1;
  const maxWins = wins[0]?.wins ?? 1;

  return (
    <div className="page-inner">
      <section className="page-heading">
        <div>
          <span className="eyebrow">{season} SEASON</span>
          <h2>Championship Standings</h2>
          <p>Official points standings for constructors and drivers.</p>
        </div>
      </section>

      {/* Tab switcher */}
      <div className="tab-bar" id="standings-tab-bar">
        <button
          className={`tab-btn${tab === "constructors" ? " tab-btn--active" : ""}`}
          onClick={() => setTab("constructors")}
          id="tab-constructors"
        >
          <BarChart2 size={15} />
          Constructors
        </button>
        <button
          className={`tab-btn${tab === "drivers" ? " tab-btn--active" : ""}`}
          onClick={() => setTab("drivers")}
          id="tab-drivers"
        >
          <Trophy size={15} />
          Drivers
        </button>
      </div>

      {loading ? (
        <div className="panel-loading" style={{ minHeight: 400 }}>
          <LoadingSpinner size={36} />
        </div>
      ) : error ? (
        <div className="panel page-error">{error}</div>
      ) : standings.length === 0 && wins.length === 0 && podiums.length === 0 ? (
        <div className="panel empty-state">No standings data exists for {season} yet. Load this season results first.</div>
      ) : tab === "constructors" ? (
        /* ─── Constructors Tab ─────────────────────────────────────────── */
        <>
          {/* Chart */}
          <div className="panel" style={{ marginBottom: 18 }}>
            <div className="panel-header">
              <div>
                <span className="eyebrow">POINTS CHART</span>
                <h3>Constructor Championship</h3>
              </div>
            </div>
            <div style={{ padding: "16px 20px 8px" }}>
              <ConstructorChart data={standings} />
            </div>
          </div>

          {/* Table */}
          <div className="panel">
            <div className="panel-header">
              <div>
                <span className="eyebrow">FULL TABLE</span>
                <h3>{season} Constructor Standings</h3>
              </div>
            </div>
            <table className="data-table" id="constructor-standings-table">
              <thead>
                <tr>
                  <th>#</th>
                  <th>Constructor</th>
                  <th style={{ textAlign: "right" }}>Points</th>
                  <th style={{ textAlign: "right" }}>Share</th>
                </tr>
              </thead>
              <tbody>
                {standings.map((c, i) => {
                  const color = CONSTRUCTOR_COLORS[c.name] ?? "#555961";
                  const pct = ((c.total_points / maxPoints) * 100).toFixed(1);
                  return (
                    <tr key={c.name} id={`constructor-row-${i + 1}`}>
                      <td>
                        <span className="rank-num" style={{ color }}>{i + 1}</span>
                      </td>
                      <td>
                        <div className="constructor-cell">
                          <span
                            className="constructor-dot"
                            style={{ background: color }}
                          />
                          <span className="table-primary">{c.name}</span>
                        </div>
                      </td>
                      <td style={{ textAlign: "right" }}>
                        <span className="points-val points-positive">{c.total_points}</span>
                      </td>
                      <td style={{ textAlign: "right" }}>
                        <div className="progress-cell">
                          <div className="progress-bar-wrap">
                            <div
                              className="progress-bar-fill"
                              style={{ width: `${pct}%`, background: color }}
                            />
                          </div>
                          <span className="table-secondary" style={{ minWidth: 36 }}>
                            {pct}%
                          </span>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </>
      ) : (
        /* ─── Drivers Tab ──────────────────────────────────────────────── */
        <div className="two-col-grid">
          {/* Driver Wins */}
          <div className="panel">
            <div className="panel-header">
              <div>
                <span className="eyebrow">RACE WINS</span>
                <h3>Driver Wins</h3>
              </div>
            </div>
            <table className="data-table" id="driver-wins-table">
              <thead>
                <tr>
                  <th>#</th>
                  <th>Driver</th>
                  <th style={{ textAlign: "right" }}>Wins</th>
                </tr>
              </thead>
              <tbody>
                {wins.map((d, i) => (
                  <tr key={d.full_name} id={`wins-row-${i + 1}`}>
                    <td>
                      <span className="rank-num">{i + 1}</span>
                    </td>
                    <td className="table-primary">{d.full_name}</td>
                    <td style={{ textAlign: "right" }}>
                      <div className="bar-inline-wrap">
                        <div
                          className="bar-inline"
                          style={{ width: `${(d.wins / maxWins) * 100}%` }}
                        />
                        <span className="points-val points-positive">{d.wins}</span>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Driver Podiums */}
          <div className="panel">
            <div className="panel-header">
              <div>
                <span className="eyebrow">TOP 3 FINISHES</span>
                <h3>
                  <Medal size={16} style={{ marginRight: 6, verticalAlign: "middle" }} />
                  Driver Podiums
                </h3>
              </div>
            </div>
            <table className="data-table" id="driver-podiums-table">
              <thead>
                <tr>
                  <th>#</th>
                  <th>Driver</th>
                  <th style={{ textAlign: "right" }}>Podiums</th>
                </tr>
              </thead>
              <tbody>
                {podiums.map((d, i) => (
                  <tr key={d.full_name} id={`podiums-row-${i + 1}`}>
                    <td>
                      <span className="rank-num">{i + 1}</span>
                    </td>
                    <td className="table-primary">{d.full_name}</td>
                    <td style={{ textAlign: "right" }}>
                      <span className="points-val points-positive">{d.podiums}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
