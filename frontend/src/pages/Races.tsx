import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowRight, CalendarDays } from "lucide-react";
import { getEvents } from "../services/api";
import type { EventSummary } from "../services/api";
import LoadingSpinner from "../components/LoadingSpinner";

function formatDate(dateStr: string | null): string {
  if (!dateStr) return "—";
  return new Date(dateStr).toLocaleDateString("en-GB", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

export default function Races() {
  const [events, setEvents] = useState<EventSummary[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    getEvents(2023, 22, 0)
      .then((data) => {
        setEvents(data.items);
        setTotal(data.total);
      })
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="page-inner">
      <section className="page-heading">
        <div>
          <span className="eyebrow">2023 SEASON</span>
          <h2>Race Calendar</h2>
          <p>All {total} rounds of the 2023 Formula 1 World Championship.</p>
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
            <h3>2023 Grand Prix Calendar</h3>
          </div>
        </div>

        {loading ? (
          <div className="panel-loading">
            <LoadingSpinner />
          </div>
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
