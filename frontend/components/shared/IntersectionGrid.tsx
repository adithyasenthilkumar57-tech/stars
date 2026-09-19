'use client';
export default function IntersectionGrid({ intersections }: { intersections: Record<string, unknown>[] }) {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 10 }}>
      {intersections.map(i => {
        const score = (i.congestion_score as number) || 0;
        return (
          <div key={i.id as string} style={{ padding: 10, background: 'var(--bg-secondary)', borderRadius: 8, textAlign: 'center' }}>
            <div style={{ fontWeight: 800, color: score > 0.7 ? 'var(--status-critical)' : score > 0.5 ? 'var(--accent-amber)' : 'var(--accent-emerald)' }}>{i.label as string}</div>
            <div style={{ fontSize: 11, color: 'var(--text-secondary)' }}>{(score * 100).toFixed(0)}%</div>
          </div>
        );
      })}
    </div>
  );
}
