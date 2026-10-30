import { useEffect, useMemo, useState } from "react";
import { Flag, Gauge, Timer, Waves } from "lucide-react";
import LoadingSpinner from "../components/LoadingSpinner";
import { getEvents, getEventStrategy } from "../services/api";
import type { EventSummary, EventStrategy } from "../services/api";
import { useActiveSeason } from "../hooks/useActiveSeason";

function lapTime(ms: number | null): string {
  if (ms == null || !Number.isFinite(Number(ms))) return "—";
  const total = Number(ms);
  const minutes = Math.floor(total / 60000);
  const seconds = Math.floor((total % 60000) / 1000);
  const millis = Math.round(total % 1000);
  return minutes > 0 ? minutes + ":" + String(seconds).padStart(2, "0") + "." + String(millis).padStart(3, "0") : (total / 1000).toFixed(3) + " s";
}

export default function Strategy() {
  const season = useActiveSeason();
  const [events, setEvents] = useState<EventSummary[]>([]);
  const [eventId, setEventId] = useState<number | null>(null);
  const [strategy, setStrategy] = useState<EventStrategy | null>(null);
  const [loadingEvents, setLoadingEvents] = useState(true);
  const [loadingStrategy, setLoadingStrategy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoadingEvents(true); setError(null); setStrategy(null); setEventId(null);
    getEvents(season, 100, 0).then((data) => {
      if (cancelled) return;
      setEvents(data.items);
      setEventId(data.items[0]?.event_id ?? null);
    }).catch(() => { if (!cancelled) setError("Could not load this season's event calendar."); })
      .finally(() => { if (!cancelled) setLoadingEvents(false); });
    return () => { cancelled = true; };
  }, [season]);

  useEffect(() => {
    if (eventId == null) { setStrategy(null); return; }
    let cancelled = false;
    setLoadingStrategy(true); setStrategy(null);
    setError(null);
    getEventStrategy(eventId).then((data) => { if (!cancelled) setStrategy(data); })
      .catch(() => { if (!cancelled) setError("Could not load strategy details for this race."); })
      .finally(() => { if (!cancelled) setLoadingStrategy(false); });
    return () => { cancelled = true; };
  }, [eventId]);

  const groupedStints = useMemo(() => {
    const map = new Map<string, EventStrategy["stints"]>();
    for (const stint of strategy?.stints ?? []) {
      const current = map.get(stint.full_name) ?? [];
      current.push(stint); map.set(stint.full_name, current);
    }
    return Array.from(map.entries());
  }, [strategy]);
  const selectedEvent = events.find((event) => event.event_id === eventId);

  return <div className="page-inner">
    <section className="page-heading"><div><span className="eyebrow">RACE STRATEGY · {season}</span><h2>Strategy Explorer</h2><p>Explore recorded tyre stints, pit stops and lap performance from the selected race.</p></div></section>
    <div className="control-row"><label className="control-group">Race
      <select className="control-select" value={eventId ?? ""} onChange={(event) => setEventId(Number(event.target.value))} disabled={loadingEvents || !events.length}>
        {events.map((event) => <option value={event.event_id} key={event.event_id}>R{event.round} · {event.event_name}</option>)}
      </select></label><span className="stat-muted">{selectedEvent?.event_date ?? ""}</span></div>
    {loadingEvents || loadingStrategy ? <div className="panel-loading"><LoadingSpinner size={36}/></div>
     : error ? <div className="panel page-error">{error}</div>
     : !strategy ? <div className="panel empty-state">No race selected.</div>
     : <>
        <div className="page-note">{strategy.available ? "Showing database-recorded values only." : (strategy.message ?? "Strategy data unavailable.")} A scheduled event may exist without imported race data.</div>
        <section className="stats-grid">
          <div className="stat-card"><div className="stat-card-top"><span>Lap records</span><span className="stat-icon"><Gauge size={18}/></span></div><div className="stat-value">{strategy.lap_count.toLocaleString()}</div><div className="stat-subtext">Rows stored for this race</div></div>
          <div className="stat-card"><div className="stat-card-top"><span>Pit stops</span><span className="stat-icon"><Flag size={18}/></span></div><div className="stat-value">{strategy.pit_stops.length}</div><div className="stat-subtext">Recorded pit-stop events</div></div>
          <div className="stat-card"><div className="stat-card-top"><span>Tyre stints</span><span className="stat-icon"><Timer size={18}/></span></div><div className="stat-value">{strategy.stints.length}</div><div className="stat-subtext">Recorded stints</div></div>
          <div className="stat-card"><div className="stat-card-top"><span>Weather rows</span><span className="stat-icon"><Waves size={18}/></span></div><div className="stat-value">{strategy.weather_count}</div><div className="stat-subtext">Weather readings stored</div></div>
        </section>
        <div className="panel" style={{marginBottom:18}}>
          <div className="panel-header"><div><span className="eyebrow">DRIVER PACE & RESULTS</span><h3>{strategy.event.event_name} · {season}</h3></div><span className="stat-muted">{strategy.drivers.length} driver rows</span></div>
          {!strategy.drivers.length ? <div className="empty-state">No results or pace records stored for this event.</div>
           : <div className="table-scroll"><table className="data-table"><thead><tr><th>Driver</th><th>Finish</th><th>Grid</th><th>Points</th><th>Laps recorded</th><th>Pit stops</th><th>Avg lap</th><th>Best lap</th></tr></thead><tbody>
            {strategy.drivers.map((driver) => <tr key={driver.driver_id}><td><span className="driver-code-tag">{driver.driver_code}</span> <strong className="table-primary">{driver.full_name}</strong></td><td>{driver.finish_position ?? "—"}</td><td>{driver.grid_position ?? "—"}</td><td>{driver.points}</td><td>{driver.laps_recorded}</td><td>{driver.pit_stops}</td><td>{lapTime(driver.avg_lap_ms)}</td><td>{lapTime(driver.best_lap_ms)}</td></tr>)}
           </tbody></table></div>}
        </div>
        <div className="two-col-grid">
          <div className="panel"><div className="panel-header"><div><span className="eyebrow">TYRE STRATEGY</span><h3>Recorded stints by driver</h3></div></div>
            {!groupedStints.length ? <div className="empty-state">No tyre stint rows are loaded for this race. Run the stint ingestion script for this round.</div>
             : <div className="strategy-visual">{groupedStints.map(([name, stints]) => <div className="strategy-mini" key={name}><h4>{name}</h4>{stints.map((stint) => <span className="stint-pill" key={stint.stint_number}>{stint.compound ?? "Unknown"} · L{stint.lap_start ?? "?"}–{stint.lap_end ?? "?"}</span>)}</div>)}</div>}
          </div>
          <div className="panel"><div className="panel-header"><div><span className="eyebrow">PIT STOPS</span><h3>Recorded pit-stop timeline</h3></div></div>
            {!strategy.pit_stops.length ? <div className="empty-state">No pit-stop data loaded for this race.</div>
             : <div className="table-scroll"><table className="data-table"><thead><tr><th>Lap</th><th>Driver</th><th>Stop</th><th>Duration</th></tr></thead><tbody>{strategy.pit_stops.map((stop, index) => <tr key={stop.driver_code + "-" + stop.stop_number + "-" + index}><td>{stop.lap ?? "—"}</td><td>{stop.full_name} ({stop.driver_code})</td><td>{stop.stop_number}</td><td>{stop.duration_ms == null ? "—" : (stop.duration_ms / 1000).toFixed(2) + " s"}</td></tr>)}</tbody></table></div>}
          </div>
        </div>
      </>}
  </div>;
}
