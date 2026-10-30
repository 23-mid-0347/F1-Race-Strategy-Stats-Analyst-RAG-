import { useEffect, useState } from "react";
import { Users } from "lucide-react";
import LoadingSpinner from "../components/LoadingSpinner";
import { getDrivers } from "../services/api";
import type { DriverRow } from "../services/api";
import { useActiveSeason } from "../hooks/useActiveSeason";

export default function Drivers() {
  const season = useActiveSeason();
  const [drivers, setDrivers] = useState<DriverRow[]>([]);
  const [loadedSeason, setLoadedSeason] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const loading = loadedSeason !== season;

  useEffect(() => {
    let cancelled = false;
    getDrivers(season)
      .then((rows) => {
        if (cancelled) return;
        setDrivers(rows);
        setError(null);
        setLoadedSeason(season);
      })
      .catch(() => {
        if (cancelled) return;
        setDrivers([]);
        setError("Could not load driver data. Check that the backend is running and that this season has result records in PostgreSQL.");
        setLoadedSeason(season);
      });
    return () => { cancelled = true; };
  }, [season]);

  return (
    <div className="page-inner">
      <section className="page-heading">
        <div>
          <span className="eyebrow">DRIVER PERFORMANCE · {season}</span>
          <h2>Drivers</h2>
          <p>Season-level performance derived from the results currently loaded in your database.</p>
        </div>
        <div className="heading-badge"><Users size={14} /> {drivers.length} drivers</div>
      </section>
      <div className="page-note">
        Points, wins and podiums are calculated from loaded race result rows. If a season has only partial ingestion, the numbers are partial too.
      </div>
      {loading ? <div className="panel-loading"><LoadingSpinner size={36} /></div>
       : error ? <div className="panel page-error">{error}</div>
       : drivers.length === 0 ? <div className="panel empty-state">No driver results are loaded for {season} yet. Load that season’s results, then refresh this page.</div>
       : <>
          <section className="driver-card-grid">
            {drivers.slice(0, 3).map((driver, index) => (
              <article className="driver-card" key={driver.driver_id}>
                <span className="eyebrow">{index === 0 ? "TOP POINTS" : index === 1 ? "NEXT IN POINTS" : "THIRD IN POINTS"}</span>
                <h3>{driver.full_name} <span className="driver-code-tag">{driver.driver_code}</span></h3>
                <p>{driver.nationality || "Nationality unavailable"}</p>
                <div className="metric-grid">
                  <div className="metric-box"><span>Points</span><strong>{Number(driver.points).toLocaleString()}</strong></div>
                  <div className="metric-box"><span>Wins</span><strong>{driver.wins}</strong></div>
                  <div className="metric-box"><span>Podiums</span><strong>{driver.podiums}</strong></div>
                  <div className="metric-box"><span>Avg finish</span><strong>{driver.avg_finish ?? "—"}</strong></div>
                </div>
              </article>
            ))}
          </section>
          <div className="panel">
            <div className="panel-header">
              <div><span className="eyebrow">SEASON TABLE</span><h3>{season} Driver Performance</h3></div>
              <span className="stat-muted">{drivers.length} records</span>
            </div>
            <div className="table-scroll">
              <table className="data-table" id="drivers-table">
                <thead><tr><th>#</th><th>Driver</th><th>Nation</th><th>Races</th><th>Wins</th><th>Podiums</th><th>Points</th><th>Avg finish</th></tr></thead>
                <tbody>
                  {drivers.map((driver, index) => (
                    <tr key={driver.driver_id}>
                      <td>{index + 1}</td>
                      <td><div className="driver-cell"><span className="driver-code-tag">{driver.driver_code}</span><strong className="table-primary">{driver.full_name}</strong></div></td>
                      <td>{driver.nationality || "—"}</td><td>{driver.races}</td><td>{driver.wins}</td><td>{driver.podiums}</td>
                      <td><strong className="points-val points-positive">{Number(driver.points).toLocaleString()}</strong></td><td>{driver.avg_finish ?? "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>}
    </div>
  );
}
