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

const navigationItems = [
  { label: "Dashboard", icon: Home, path: "/" },
  { label: "Races", icon: Flag, path: "/races" },
  { label: "Drivers", icon: Users, path: "/drivers" },
  { label: "Statistics", icon: BarChart3, path: "/statistics" },
  { label: "Strategy", icon: Gauge, path: "/strategy" },
  { label: "Compare", icon: Trophy, path: "/compare" },
  { label: "AI Analyst", icon: Bot, path: "/analyst" },
];

export default function Sidebar() {
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
              className={({ isActive }) =>
                `nav-item ${isActive ? "active" : ""}`
              }
            >
              <Icon size={19} strokeWidth={1.8} />
              <span>{item.label}</span>
            </NavLink>
          );
        })}
      </nav>

      <div className="sidebar-bottom">
        <button className="nav-item">
          <Settings size={19} strokeWidth={1.8} />
          <span>Settings</span>
        </button>

        <div className="season-selector">
          <span>ACTIVE SEASON</span>
          <strong>2023</strong>
        </div>
      </div>
    </aside>
  );
}