import { Bell, CircleUserRound, Search } from "lucide-react";

export default function TopBar() {
  return (
    <header className="topbar">
      <div className="topbar-search">
        <Search size={18} />
        <input
          type="text"
          placeholder="Search drivers, races, circuits..."
        />
        <span className="search-shortcut">⌘ K</span>
      </div>

      <div className="topbar-actions">
        <div className="system-status">
          <span className="status-dot" />
          <span>API Online</span>
        </div>

        <button className="icon-button" aria-label="Notifications">
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