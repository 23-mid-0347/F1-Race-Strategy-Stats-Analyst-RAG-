import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { ArrowLeft, Trophy } from "lucide-react";
import { getEventResults } from "../services/api";
import type { EventResults, RaceResultRow } from "../services/api";
import LoadingSpinner from "../components/LoadingSpinner";

function positionClass(pos: number | null): string {
  if (pos === 1) return "pos-gold";
  if (pos === 2) return "pos-silver";
  if (pos === 3) return "pos-bronze";
  return "";
}

function statusChipClass(status: string | null): string {
  if (!status) return "";
  if (status === "Finished" || status.includes("Lap")) return "chip-finished";
  return "chip-dnf";
}

function msToLapTime(ms: number): string {
  const mins = Math.floor(ms / 60000);
  const secs = Math.floor((ms % 60000) / 1000);
  const millis = ms % 1000;
  return `${mins}:${String(secs).padStart(2, "0")}.${String(millis).padStart(3, "0")}`;
}

export default function RaceDetail() {
  const { eventId } = useParams<{ eventId: string }>();
  const navigate = useNavigate();
  const [data, setData] = useState<EventResults | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!eventId) return;
    getEventResults(Number(eventId))
      .then(setData)
      .catch(() => setError("Could not load race results."))
      .finally(() => setLoading(false));
  }, [eventId]);

  if (loading) {
    return (
      <div className="page-inner">
        <div className="panel-loading" style={{ minHeight: 400 }}>
          <LoadingSpinner size={40} />
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="page-inner">
        <div className="error-state">{error ?? "Race not found."}</div>
      </div>
    );
  }

  const winner = data.results.find((r) => r.finish_position === 1);

  return (
    <div className="page-inner">
      {/* Back button */}
      <button className="back-btn" onClick={() => navigate("/races")} id="btn-back-to-races">
        <ArrowLeft size={15} />
        All Races
      </button>

      {/* Page heading */}
      <section className="page-heading">
        <div>
          <span className="eyebrow">ROUND {data.round} · {data.season}</span>
          <h2>{data.event_name}</h2>
          {winner && (
            <p>
              <Trophy size={13} style={{ display: "inline", marginRight: 5, color: "#f59e0b" }} />
              Winner: <strong style={{ color: "#f4f4f5" }}>{winner.full_name}</strong>
              {" "}— {winner.constructor_name}
            </p>
          )}
        </div>
      </section>

      {/* Results table */}
      <div className="panel">
        <div className="panel-header">
          <div>
            <span className="eyebrow">RACE CLASSIFICATION</span>
            <h3>{data.results.length} Classified</h3>
          </div>
        </div>

        <table className="data-table" id="race-results-table">
          <thead>
            <tr>
              <th>Pos</th>
              <th>Driver</th>
              <th>Constructor</th>
              <th style={{ textAlign: "center" }}>Grid</th>
              <th style={{ textAlign: "right" }}>Points</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {data.results.map((row: RaceResultRow, idx) => (
              <tr key={idx} id={`result-row-${idx + 1}`}>
                <td>
                  <span className={`pos-badge ${positionClass(row.finish_position)}`}>
                    {row.finish_position ?? "—"}
                  </span>
                </td>
                <td>
                  <div className="driver-cell">
                    <span className="driver-code-tag">{row.driver_code}</span>
                    <span className="table-primary">{row.full_name}</span>
                  </div>
                </td>
                <td className="table-secondary">{row.constructor_name ?? "—"}</td>
                <td style={{ textAlign: "center" }} className="table-secondary">
                  {row.grid_position ?? "—"}
                </td>
                <td style={{ textAlign: "right" }}>
                  <span className={`points-val${row.points > 0 ? " points-positive" : ""}`}>
                    {row.points > 0 ? `+${row.points}` : row.points}
                  </span>
                </td>
                <td>
                  <span className={`status-chip ${statusChipClass(row.status)}`}>
                    {row.status ?? "—"}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
