import {
  BarChart3,
  Bot,
  Flag,
  Gauge,
  Home,
  Settings,
  Trophy,
  Users,
} from "lucide-react";
import { NavLink } from "react-router-dom";
import { useEffect, useState } from "react";
import { getSeasons } from "../services/api";

const navigationItems = [
  { label: "Dashboard",   icon: Home,     path: "/" },
  { label: "Races",       icon: Flag,     path: "/races" },
  { label: "Drivers",     icon: Users,    path: "/drivers" },
  { label: "Standings",   icon: BarChart3, path: "/standings" },
  { label: "Strategy",    icon: Gauge,    path: "/strategy" },
  { label: "Compare",     icon: Trophy,   path: "/compare" },
  { label: "AI Analyst",  icon: Bot,      path: "/analyst" },
];

export default function Sidebar() {
  const [seasons, setSeasons] = useState<number[]>([]);
  const [season, setSeason] = useState<number>(2023);

  useEffect(() => {
    getSeasons().then((available) => {
      setSeasons(available);
      if (available.length) setSeason((current) => available.includes(current) ? current : available[0]);
    }).catch(() => setSeasons([]));
  }, []);

  useEffect(() => {
    const onSeasonChange = (event: Event) => setSeason((event as CustomEvent<number>).detail);
    window.addEventListener("f1-season-change", onSeasonChange);
    return () => window.removeEventListener("f1-season-change", onSeasonChange);
  }, []);

  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <div className="logo-mark">F1</div>
        <div>
          <h1>RaceLab</h1>
          <span>Analytics Platform</span>
        </div>
      </div>

      <nav className="sidebar-nav">
        <div className="nav-section-title">MAIN</div>

        {navigationItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.label}
              to={item.path}
              end={item.path === "/"}
              className={({ isActive }) => `nav-item${isActive ? " active" : ""}`}
              id={`nav-${item.label.toLowerCase().replace(" ", "-")}`}
            >
              <Icon size={19} strokeWidth={1.8} />
              <span>{item.label}</span>
            </NavLink>
          );
        })}
      </nav>

      <div className="sidebar-bottom">
        <button className="nav-item" id="nav-settings">
          <Settings size={19} strokeWidth={1.8} />
          <span>Settings</span>
        </button>

        <div className="season-selector">
          <label htmlFor="sidebar-season">ACTIVE SEASON</label>
          <select
            id="sidebar-season"
            aria-label="Select active season"
            value={seasons.includes(season) ? season : (seasons[0] ?? 2023)}
            onChange={(event) => {
              const next = Number(event.target.value);
              setSeason(next);
              window.dispatchEvent(new CustomEvent("f1-season-change", { detail: next }));
            }}
          >
            {(seasons.length ? seasons : [2023]).map((year) => (
              <option key={year} value={year}>{year}</option>
            ))}
          </select>
        </div>
      </div>
    </aside>
  );
}