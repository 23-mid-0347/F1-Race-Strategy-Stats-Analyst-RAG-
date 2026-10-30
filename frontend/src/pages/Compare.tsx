import { useEffect, useMemo, useState } from "react";
import { GitCompareArrows, Trophy } from "lucide-react";
import LoadingSpinner from "../components/LoadingSpinner";
import { getDrivers, getDriverComparison } from "../services/api";
import type { DriverRow, DriverComparison } from "../services/api";
import { useActiveSeason } from "../hooks/useActiveSeason";

export default function Compare() {
  const season = useActiveSeason();
  const [drivers, setDrivers] = useState<DriverRow[]>([]);
  const [selected, setSelected] = useState<number[]>([]);
  const [comparison, setComparison] = useState<DriverComparison[]>([]);
  const [loading, setLoading] = useState(true);
  const [comparing, setComparing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [comparisonError, setComparisonError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true); setError(null); setComparison([]); setSelected([]);
    getDrivers(season).then((rows) => {
      if (!cancelled) {
        setDrivers(rows);
        setSelected(rows.slice(0, 2).map((row) => row.driver_id));
      }
    }).catch(() => { if (!cancelled) setError("Could not load drivers for comparison. Ensure the API and season results are available."); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [season]);

  const selectedNames = useMemo(() => drivers.filter((driver) => selected.includes(driver.driver_id)).map((driver) => driver.full_name), [drivers, selected]);

  const toggle = (id: number) => {
    setComparison([]); setComparisonError(null);
    setSelected((current) => current.includes(id) ? current.filter((value) => value !== id) : current.length < 4 ? [...current, id] : current);
  };

  const runComparison = async () => {
    if (selected.length < 2) { setComparisonError("Choose at least two drivers."); return; }
    setComparing(true); setComparisonError(null);
    try { setComparison(await getDriverComparison(selected, season)); }
    catch { setComparisonError("Comparison failed. This can happen if selected drivers have no result rows for this season."); }
    finally { setComparing(false); }
  };

  return <div className="page-inner">
    <section className="page-heading"><div><span className="eyebrow">HEAD-TO-HEAD · {season}</span><h2>Driver Comparison</h2><p>Compare actual season results for two to four drivers.</p></div><div className="heading-badge"><GitCompareArrows size={14}/>{selected.length}/4 selected</div></section>
    <div className="page-note">The comparison uses stored results only. Tyre degradation, pace deltas and strategy impact are not inferred if the required lap-level data is missing.</div>
    {loading ? <div className="panel-loading"><LoadingSpinner size={36}/></div>
     : error ? <div className="panel page-error">{error}</div>
     : drivers.length === 0 ? <div className="panel empty-state">No drivers found for {season}; ingest race results first.</div>
     : <>
        <div className="panel" style={{ marginBottom: 18 }}>
          <div className="panel-header"><div><span className="eyebrow">SELECT DRIVERS</span><h3>Pick 2–4 drivers</h3></div><span className="stat-muted">{selectedNames.join(" · ") || "None selected"}</span></div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(180px,1fr))", gap: 8, padding: 16 }}>
            {drivers.map((driver) => <label key={driver.driver_id} style={{ display:"flex", gap:10, alignItems:"center", padding:"10px 12px", border:"1px solid #25272d", borderRadius:7, background:selected.includes(driver.driver_id) ? "#201416" : "#101216" }}>
              <input type="checkbox" checked={selected.includes(driver.driver_id)} onChange={() => toggle(driver.driver_id)} disabled={!selected.includes(driver.driver_id) && selected.length >= 4}/>
              <span><strong style={{ display:"block", fontSize:12 }}>{driver.full_name}</strong><small className="stat-muted">{driver.driver_code} · {driver.points} pts</small></span>
            </label>)}
          </div>
          <div style={{ padding:"0 16px 16px" }}><button className="primary-button" onClick={runComparison} disabled={selected.length < 2 || comparing}>{comparing ? "Comparing…" : "Compare selected drivers"}</button>{comparisonError && <p className="page-error">{comparisonError}</p>}</div>
        </div>
        {comparison.length > 0 && <div className="panel">
          <div className="panel-header"><div><span className="eyebrow">RESULTS</span><h3>Season comparison</h3></div><Trophy size={18} color="#e10600"/></div>
          <div className="table-scroll"><table className="data-table"><thead><tr><th>Driver</th><th>Team</th><th>Races</th><th>Wins</th><th>Podiums</th><th>Points</th><th>Avg finish</th><th>DNFs</th></tr></thead>
            <tbody>{comparison.map((driver) => <tr key={driver.driver_id}><td><span className="driver-code-tag">{driver.driver_code}</span> <strong className="table-primary">{driver.full_name}</strong></td><td>{driver.constructor_name ?? "—"}</td><td>{driver.races}</td><td>{driver.wins}</td><td>{driver.podiums}</td><td><strong className="points-val points-positive">{Number(driver.points).toLocaleString()}</strong></td><td>{driver.avg_finish ?? "—"}</td><td>{driver.dnfs}</td></tr>)}</tbody>
          </table></div>
        </div>}
      </>}
  </div>;
}
