export function ChartSkeleton() {
  return <div className="skeleton skeleton-chart" aria-hidden="true" />;
}

export function CardsSkeleton() {
  return (
    <div className="cards">
      {[0, 1, 2, 3].map((i) => (
        <div key={i} className="skeleton skeleton-card" aria-hidden="true" />
      ))}
    </div>
  );
}

export function EmptyState({ reason }: { reason: string }) {
  const text =
    reason === "no_data_in_range"
      ? "No usage recorded in this date range."
      : reason === "insufficient_history"
        ? "Not enough history yet for this view."
        : reason;
  return (
    <div className="empty-state" role="status">
      {text}
    </div>
  );
}

export function ErrorState({ message }: { message: string }) {
  return (
    <div className="error-state" role="alert">
      Could not load data: {message}
    </div>
  );
}
