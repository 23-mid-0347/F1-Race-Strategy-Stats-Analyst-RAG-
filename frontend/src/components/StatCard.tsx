import type { LucideIcon } from "lucide-react";

interface StatCardProps {
  label: string;
  value: string | number;
  subtext?: string;
  icon: LucideIcon;
  loading?: boolean;
  accent?: boolean;
}

export default function StatCard({
  label,
  value,
  subtext,
  icon: Icon,
  loading = false,
  accent = false,
}: StatCardProps) {
  return (
    <div className={`stat-card${accent ? " stat-card--accent" : ""}`}>
      <div className="stat-card-top">
        <div className="stat-icon">
          <Icon size={19} strokeWidth={1.8} />
        </div>
        <span className="stat-label-top">{label}</span>
      </div>

      {loading ? (
        <>
          <div className="skeleton" style={{ height: 34, width: "60%", marginTop: 18 }} />
          <div className="skeleton" style={{ height: 12, width: "40%", marginTop: 8 }} />
        </>
      ) : (
        <>
          <div className="stat-value">{value}</div>
          {subtext && <div className="stat-subtext">{subtext}</div>}
        </>
      )}
    </div>
  );
}
