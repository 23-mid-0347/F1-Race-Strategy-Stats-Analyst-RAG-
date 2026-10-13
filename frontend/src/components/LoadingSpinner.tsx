export default function LoadingSpinner({ size = 32 }: { size?: number }) {
  return (
    <div className="spinner-wrap" style={{ "--sz": `${size}px` } as React.CSSProperties}>
      <div className="spinner" />
    </div>
  );
}
