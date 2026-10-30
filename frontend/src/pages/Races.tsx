import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowRight, CalendarDays } from "lucide-react";
import { getEvents } from "../services/api";
import type { EventSummary } from "../services/api";
import LoadingSpinner from "../components/LoadingSpinner";
import { useActiveSeason } from "../hooks/useActiveSeason";

function formatDate(dateStr: string | null): string {
  if (!dateStr) return "—";
  return new Date(dateStr).toLocaleDateString("en-GB", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

export default function Races() {
  const season = useActiveSeason();
  const [events, setEvents] = useState<EventSummary[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [total, setTotal] = useState(0);
  const [loadedSeason, setLoadedSeason] = useState<number | null>(null);
  const loading = loadedSeason !== season;
  const navigate = useNavigate();

  useEffect(() => {
    let cancelled = false;
    getEvents(season, 100, 0)
      .then((data) => {
        if (cancelled) return;
        setEvents(data.items);
        setTotal(data.total);
        setError(null);
        setLoadedSeason(season);
      })
      .catch(() => {
        if (cancelled) return;
        setEvents([]);
        setTotal(0);
        setError("Could not load races. Check the backend connection.");
        setLoadedSeason(season);
      });
    return () => { cancelled = true; };
  }, [season]);

  return (
    <div className="page-inner">
      <section className="page-heading">
        <div>
          <span className="eyebrow">{season} SEASON</span>
          <h2>Race Calendar</h2>
          <p>{total} scheduled events in the {season} Formula 1 season.</p>
        </div>
        <div className="heading-badge">
          <CalendarDays size={14} />
          {total} Races
        </div>
      </section>

      <div className="panel">
        <div className="panel-header">
          <div>
            <span className="eyebrow">SCHEDULE</span>
            <h3>{season} Grand Prix Calendar</h3>
          </div>
        </div>

        {loading ? (
          <div className="panel-loading">
            <LoadingSpinner />
          </div>
        ) : error ? (
          <div className="page-error">{error}</div>
        ) : events.length === 0 ? (
          <div className="empty-state">No events are loaded for {season}. Load the season schedule first.</div>
        ) : (
          <table className="data-table" id="race-calendar-table">
            <thead>
              <tr>
                <th>Rd</th>
                <th>Grand Prix</th>
                <th>Circuit</th>
                <th>Date</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {events.map((ev) => (
                <tr
                  key={ev.event_id}
                  className="table-row-clickable"
                  onClick={() => navigate(`/races/${ev.event_id}`)}
                  id={`race-row-${ev.event_id}`}
                >
                  <td>
                    <span className="round-badge">R{String(ev.round).padStart(2, "0")}</span>
                  </td>
                  <td className="table-primary">{ev.event_name}</td>
                  <td className="table-secondary">{ev.circuit_name ?? "—"}</td>
                  <td className="table-secondary">{formatDate(ev.event_date)}</td>
                  <td>
                    <ArrowRight size={15} className="row-arrow" />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
