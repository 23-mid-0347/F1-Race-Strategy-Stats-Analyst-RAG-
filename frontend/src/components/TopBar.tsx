import { useEffect, useState, useRef } from "react";
import { Bell, CircleUserRound, Search } from "lucide-react";
import { getHealth } from "../services/api";

type ApiStatus = "checking" | "online" | "offline";

const POLL_INTERVAL_MS = 30_000;

export default function TopBar() {
  const [status, setStatus] = useState<ApiStatus>("checking");
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const checkHealth = () => {
    getHealth()
      .then(() => setStatus("online"))
      .catch(() => setStatus("offline"));
  };

  useEffect(() => {
    checkHealth();
    intervalRef.current = setInterval(checkHealth, POLL_INTERVAL_MS);
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, []);

  const dotClass =
    status === "online"
      ? "status-dot status-dot--online"
      : status === "offline"
        ? "status-dot status-dot--offline"
        : "status-dot status-dot--checking";

  const label =
    status === "online" ? "API Online" : status === "offline" ? "API Offline" : "Checking…";

  return (
    <header className="topbar">
      <div className="topbar-search">
        <Search size={18} />
        <input
          id="topbar-search-input"
          type="text"
          placeholder="Search drivers, races, circuits..."
        />
        <span className="search-shortcut">⌘ K</span>
      </div>

      <div className="topbar-actions">
        <div className="system-status" id="api-status-indicator">
          <span className={dotClass} />
          <span>{label}</span>
        </div>

        <button className="icon-button" aria-label="Notifications" id="btn-notifications">
          <Bell size={19} />
        </button>

        <div className="profile">
          <CircleUserRound size={27} />
          <div>
            <strong>F1 Analyst</strong>
            <span>Race Strategy</span>
          </div>
        </div>
      </div>
    </header>
  );
}