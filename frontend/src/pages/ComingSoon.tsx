import { Construction } from "lucide-react";

interface ComingSoonProps {
  page: string;
}

export default function ComingSoon({ page }: ComingSoonProps) {
  return (
    <div className="coming-soon-wrap">
      <div className="coming-soon-card">
        <div className="coming-soon-icon">
          <Construction size={32} strokeWidth={1.4} />
        </div>
        <h2 className="coming-soon-title">{page}</h2>
        <p className="coming-soon-desc">
          This page is part of Phase 7–8 (Vector DB + RAG) and is coming soon.
          The API backend is fully ready — the UI will follow.
        </p>
        <div className="coming-soon-badge">PHASE 7–8</div>
      </div>
    </div>
  );
}
