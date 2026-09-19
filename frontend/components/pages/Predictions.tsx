'use client';
import { useState, useEffect } from 'react';
import { AppState, NavPage } from '@/app/page';
import api from '@/lib/api';

interface Props { appState: AppState; updateOptimization: (o: Record<string, unknown>) => void; updateEmergency: (e: Record<string, unknown>) => void; setCurrentPage: (p: NavPage) => void; }

export default function Predictions({ appState }: Props) {
  const [predictions, setPredictions] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    try { setPredictions(await api.getPredictions()); } catch {} finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);

  const perJunction: Record<string, unknown>[] = (predictions?.predictions as Record<string, unknown>[]) || [];

  return (
    <div className="page animate-fade-in">
      <div className="page-header">
        <div>
          <h2 className="page-title">AI Traffic Predictions</h2>
          <p className="page-subtitle">
            Pattern-based forecasting +5/10/15/30 min ahead — labeled throughout
            <span className="badge badge-cyan" style={{ marginLeft: 6 }}>AI PREDICTION</span>
            <span className="badge badge-simulated" style={{ marginLeft: 4 }}>NOT REAL-TIME SENSOR DATA</span>
          </p>
        </div>
        <button className="btn btn-ghost" onClick={load}>⟳ Refresh</button>
      </div>

      {/* Network-level predictions */}
      {predictions?.network_summary && (
        <div className="card">
          <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 16 }}>Network Forecast <span className="badge badge-cyan">AI PREDICTION</span></div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12 }}>
            {(['5min', '10min', '15min', '30min'] as const).map(horizon => {
              const net = (predictions.network_summary as Record<string, unknown>)[horizon] as Record<string, unknown>;
              if (!net) return null;
              return (
                <div key={horizon} style={{ padding: 16, background: 'var(--bg-secondary)', borderRadius: 10, textAlign: 'center' }}>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 8, textTransform: 'uppercase', letterSpacing: '0.06em' }}>+{horizon}</div>
                  <div style={{ fontSize: 24, fontWeight: 900, color: (net.avg_congestion as number) > 0.7 ? 'var(--status-critical)' : (net.avg_congestion as number) > 0.5 ? 'var(--accent-amber)' : 'var(--accent-emerald)' }}>
                    {((net.avg_congestion as number) * 100).toFixed(0)}%
                  </div>
                  <div style={{ fontSize: 11, color: 'var(--text-secondary)', marginTop: 4 }}>Avg congestion</div>
                  <div style={{ fontSize: 11, color: 'var(--text-secondary)', marginTop: 2 }}>
                    {net.critical_junctions as number} critical
                  </div>
                  <span className="badge badge-cyan" style={{ marginTop: 8, display: 'inline-block' }}>AI PREDICTION</span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Per-junction predictions */}
      {loading ? (
        <div className="grid-3">{[1,2,3,4,5,6].map(i => <div key={i} className="skeleton" style={{ height: 200, borderRadius: 12 }} />)}</div>
      ) : (
        <div className="grid-3">
          {perJunction.map((p) => {
            const junction = (p.junction_label as string) || (p.junction_id as string);
            const horizons = p.horizons as Record<string, Record<string, unknown>>;
            const trend = p.trend as string;
            const risk = p.overload_risk as boolean;
            return (
              <div key={junction} className="card" style={{ borderColor: risk ? 'rgba(244,63,94,0.3)' : 'var(--border-subtle)' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
                  <div style={{ fontWeight: 800, fontSize: 16, color: 'var(--accent-cyan)' }}>{junction}</div>
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 4 }}>
                    <span style={{ fontSize: 11, fontWeight: 700, color: trend === 'increasing' ? 'var(--status-critical)' : trend === 'decreasing' ? 'var(--accent-emerald)' : 'var(--text-secondary)', textTransform: 'uppercase' }}>
                      {trend === 'increasing' ? '▲' : trend === 'decreasing' ? '▼' : '—'} {trend}
                    </span>
                    {risk && <span className="badge badge-rose">OVERLOAD RISK</span>}
                  </div>
                </div>
                {p.recommendation && (
                  <div style={{ padding: 8, background: 'rgba(16,185,129,0.08)', borderRadius: 6, fontSize: 11, color: 'var(--text-secondary)', marginBottom: 10, lineHeight: 1.5 }}>
                    💡 {p.recommendation as string}
                  </div>
                )}
                {horizons && (
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 6 }}>
                    {Object.entries(horizons).map(([h, data]) => (
                      <div key={h} style={{ padding: 8, background: 'var(--bg-secondary)', borderRadius: 6, textAlign: 'center' }}>
                        <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 2 }}>+{h}</div>
                        <div style={{ fontWeight: 800, fontSize: 15, color: (data.congestion_score as number) > 0.7 ? 'var(--status-critical)' : (data.congestion_score as number) > 0.5 ? 'var(--accent-amber)' : 'var(--accent-emerald)' }}>
                          {((data.congestion_score as number) * 100).toFixed(0)}%
                        </div>
                        <div style={{ fontSize: 9, color: 'var(--text-muted)' }}>{data.vehicles as number}v</div>
                        <span className="badge badge-cyan" style={{ marginTop: 4, display: 'inline-block', fontSize: 8 }}>AI</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
