'use client';
import { AppState } from '@/app/page';
import { NavPage } from '@/app/page';
import { useState, useEffect } from 'react';
import api from '@/lib/api';
import CongestionBar from '@/components/shared/CongestionBar';
import IntersectionGrid from '@/components/shared/IntersectionGrid';

interface Props {
  appState: AppState;
  updateOptimization: (opt: Record<string, unknown>) => void;
  updateEmergency: (em: Record<string, unknown>) => void;
  setCurrentPage: (p: NavPage) => void;
}

export default function Dashboard({ appState, updateOptimization, updateEmergency, setCurrentPage }: Props) {
  const { intersections, networkSummary, latestOptimization, emergency, dataMode } = appState;
  const [isOptimizing, setIsOptimizing] = useState(false);
  const [history, setHistory] = useState<Record<string, unknown>[]>([]);

  useEffect(() => {
    api.getTrafficHistory(6).then(d => setHistory(d.history || [])).catch(() => {});
  }, []);

  const handleQuickOptimize = async () => {
    setIsOptimizing(true);
    try {
      const result = await api.runOptimization('hybrid_quantum');
      updateOptimization(result);
    } finally {
      setIsOptimizing(false);
    }
  };

  const avgCongestion = intersections.length > 0
    ? intersections.reduce((s, i) => s + ((i as Record<string, unknown>).congestion_score as number || 0), 0) / intersections.length
    : 0;

  const totalVehicles = (networkSummary?.total_vehicles as number) ?? 0;
  const avgWait = (networkSummary?.avg_waiting_seconds as number) ?? 0;
  const emergencyActive = !!(emergency as Record<string, unknown>)?.active;
  const corridorStatus = (emergency as Record<string, unknown>)?.corridor_status as string;

  const worstJunction = intersections.reduce((worst: Record<string, unknown>, i) => {
    const ic = (i as Record<string, unknown>).congestion_score as number;
    const wc = worst.congestion_score as number;
    return ic > (wc || 0) ? i as Record<string, unknown> : worst;
  }, {} as Record<string, unknown>);

  return (
    <div className="page animate-fade-in">
      {/* Page header */}
      <div className="page-header">
        <div>
          <h2 className="page-title">Network Command Center</h2>
          <p className="page-subtitle">
            Tiruppur Urban Traffic Network — 6 Junctions — Monitoring Active
            <span className="data-label data-label-demo" style={{ marginLeft: 8 }}>DEMO</span>
          </p>
        </div>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          <button
            className="btn btn-quantum"
            onClick={handleQuickOptimize}
            disabled={isOptimizing}
          >
            <span>{isOptimizing ? '⟳' : '⚛'}</span>
            {isOptimizing ? 'Optimizing...' : 'Quick Optimize'}
          </button>
          <button className="btn btn-ghost" onClick={() => setCurrentPage('simulation')}>
            ▶ Run Simulation
          </button>
          <button
            className={`btn ${emergencyActive ? 'btn-danger' : 'btn-ghost'}`}
            onClick={() => setCurrentPage('emergency-corridor')}
          >
            {emergencyActive ? '🚨 Corridor Active' : '🚑 Emergency'}
          </button>
        </div>
      </div>

      {/* Emergency banner */}
      {emergencyActive && (
        <div className="alert-banner critical animate-fade-in" style={{ cursor: 'pointer' }}
             onClick={() => setCurrentPage('emergency-corridor')}>
          <span style={{ fontSize: 18 }}>🚨</span>
          <div>
            <strong>Emergency Green Corridor Active</strong> —{' '}
            Status: {corridorStatus?.replace(/_/g, ' ').toUpperCase()}.{' '}
            Click to monitor.
          </div>
          <span className="badge badge-rose" style={{ marginLeft: 'auto' }}>SIMULATED</span>
        </div>
      )}

      {/* KPI Cards */}
      <div className="grid-4">
        <KPICard
          label="Network Congestion"
          value={`${(avgCongestion * 100).toFixed(0)}%`}
          sub={avgCongestion > 0.7 ? '⚠ High congestion detected' : '✓ Within normal range'}
          color={avgCongestion > 0.7 ? 'var(--status-critical)' : avgCongestion > 0.5 ? 'var(--accent-amber)' : 'var(--accent-emerald)'}
          icon="◉"
          trend={avgCongestion > 0.6 ? 'up' : 'stable'}
        />
        <KPICard
          label="Active Vehicles"
          value={totalVehicles.toLocaleString()}
          sub="Across all junctions"
          color="var(--accent-cyan)"
          icon="⬡"
          badge="DEMO"
        />
        <KPICard
          label="Avg Wait Time"
          value={`${avgWait.toFixed(0)}s`}
          sub={latestOptimization ? `↓ ${((latestOptimization as Record<string, unknown>).improvement_pct as number || 0).toFixed(1)}% after optimization` : 'No optimization run yet'}
          color="var(--accent-purple)"
          icon="◌"
        />
        <KPICard
          label="Worst Junction"
          value={(worstJunction?.label as string) || '—'}
          sub={worstJunction?.congestion_score ? `${((worstJunction.congestion_score as number) * 100).toFixed(0)}% congestion` : 'No data'}
          color="var(--accent-amber)"
          icon="◇"
          badge={(worstJunction?.congestion_level as string)?.toUpperCase()}
        />
      </div>

      {/* Optimization result */}
      {latestOptimization && (
        <div className="quantum-panel" style={{ padding: 20 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
            <span style={{ fontSize: 18 }}>⚛</span>
            <div>
              <div style={{ fontWeight: 700, fontSize: 15 }}>Latest Optimization Result</div>
              <div style={{ fontSize: 11, color: 'var(--text-secondary)' }}>
                Method: {(latestOptimization as Record<string, unknown>).method as string} —
                <span className="badge badge-quantum" style={{ marginLeft: 6 }}>
                  {(latestOptimization as Record<string, unknown>).simulator_status as string || 'QUANTUM SIMULATOR'}
                </span>
              </div>
            </div>
            <span className="badge badge-quantum" style={{ marginLeft: 'auto' }}>QUANTUM SIMULATION</span>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12 }}>
            {[
              { label: 'Cost Before', value: `${((latestOptimization as Record<string, unknown>).cost_before as number)?.toFixed(1)}` },
              { label: 'Cost After', value: `${((latestOptimization as Record<string, unknown>).cost_after as number)?.toFixed(1)}` },
              { label: 'Improvement', value: `${((latestOptimization as Record<string, unknown>).improvement_pct as number)?.toFixed(1)}%`, highlight: true },
              { label: 'Exec Time', value: `${((latestOptimization as Record<string, unknown>).execution_time_ms as number)?.toFixed(0)}ms` },
            ].map(({ label, value, highlight }) => (
              <div key={label} style={{ textAlign: 'center', padding: 12, background: 'rgba(0,212,255,0.05)', borderRadius: 8 }}>
                <div style={{ fontSize: 20, fontWeight: 800, color: highlight ? 'var(--accent-emerald)' : 'var(--accent-cyan)' }}>
                  {value}
                </div>
                <div style={{ fontSize: 10, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.06em', marginTop: 4 }}>{label}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Main content grid */}
      <div className="grid-2">
        {/* Junction status */}
        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
            <div style={{ fontWeight: 700, fontSize: 14 }}>Junction Status</div>
            <button className="btn btn-ghost" style={{ fontSize: 12, padding: '4px 10px' }} onClick={() => setCurrentPage('live-monitor')}>
              View All →
            </button>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {intersections.slice(0, 6).map((inter) => {
              const i = inter as Record<string, unknown>;
              const score = (i.congestion_score as number) || 0;
              const level = (i.congestion_level as string) || 'low';
              return (
                <div key={i.id as string} style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                  <div style={{
                    width: 32, height: 32,
                    background: score > 0.7 ? 'rgba(244,63,94,0.15)' : score > 0.5 ? 'rgba(245,158,11,0.15)' : 'rgba(16,185,129,0.15)',
                    borderRadius: 8,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontWeight: 800, fontSize: 12,
                    color: score > 0.7 ? 'var(--status-critical)' : score > 0.5 ? 'var(--accent-amber)' : 'var(--accent-emerald)',
                  }}>{i.label as string}</div>
                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                      <span style={{ fontSize: 12, fontWeight: 600 }}>{i.name as string}</span>
                      <span style={{ fontSize: 12, fontWeight: 700, color: score > 0.7 ? 'var(--status-critical)' : score > 0.5 ? 'var(--accent-amber)' : 'var(--accent-emerald)' }}>
                        {(score * 100).toFixed(0)}%
                      </span>
                    </div>
                    <CongestionBar score={score} level={level} />
                  </div>
                  <div style={{ fontSize: 11, color: 'var(--text-secondary)', textAlign: 'right', minWidth: 60 }}>
                    <div>{i.vehicle_count as number}v</div>
                    <div>{(i.waiting_time_seconds as number)?.toFixed(0)}s wait</div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Traffic history sparkline */}
        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
            <div style={{ fontWeight: 700, fontSize: 14 }}>6-Hour Traffic Trend</div>
            <span className="badge badge-simulated">SIMULATED HISTORICAL</span>
          </div>
          {history.length > 0 ? (
            <MiniSparkline data={history} />
          ) : (
            <div style={{ height: 160, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', fontSize: 12 }}>
              Loading historical data...
            </div>
          )}
          <div style={{ marginTop: 12, display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 8 }}>
            {[
              { label: 'Peak Hour', value: history.length > 0 ? `${(history[history.length-1]?.hour as number) ?? '--'}:00` : '--' },
              { label: 'Max Congestion', value: history.length > 0 ? `${((Math.max(...history.map(h => h.avg_congestion as number || 0))) * 100).toFixed(0)}%` : '--' },
              { label: 'Data Points', value: history.length.toString() },
            ].map(({ label, value }) => (
              <div key={label} style={{ textAlign: 'center', padding: 8, background: 'var(--bg-secondary)', borderRadius: 6 }}>
                <div style={{ fontWeight: 700, color: 'var(--accent-cyan)', fontSize: 14 }}>{value}</div>
                <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>{label}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Quick action grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12 }}>
        {[
          { icon: '⚛', label: 'Quantum Optimize', desc: 'Run QAOA signal optimization', page: 'quantum-optimizer', color: 'var(--accent-cyan)' },
          { icon: '🚨', label: 'Emergency Corridor', desc: 'Activate green corridor', page: 'emergency-corridor', color: 'var(--status-critical)' },
          { icon: '🔊', label: 'Siren Detection', desc: 'Test audio detection', page: 'siren-detection', color: 'var(--accent-amber)' },
          { icon: '▶', label: 'Run Simulation', desc: 'Traffic scenario test', page: 'simulation', color: 'var(--accent-purple)' },
        ].map(({ icon, label, desc, page, color }) => (
          <button
            key={page}
            onClick={() => setCurrentPage(page as NavPage)}
            style={{
              background: 'var(--bg-card)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 12,
              padding: 16,
              cursor: 'pointer',
              textAlign: 'left',
              transition: 'all 0.15s',
              display: 'flex',
              gap: 12,
              alignItems: 'flex-start',
            }}
            onMouseEnter={e => { (e.currentTarget as HTMLElement).style.borderColor = color; (e.currentTarget as HTMLElement).style.transform = 'translateY(-2px)'; }}
            onMouseLeave={e => { (e.currentTarget as HTMLElement).style.borderColor = 'var(--border-subtle)'; (e.currentTarget as HTMLElement).style.transform = 'none'; }}
          >
            <span style={{ fontSize: 22, marginTop: 2 }}>{icon}</span>
            <div>
              <div style={{ fontWeight: 700, fontSize: 13, color: 'var(--text-primary)', marginBottom: 3 }}>{label}</div>
              <div style={{ fontSize: 11, color: 'var(--text-secondary)' }}>{desc}</div>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}

function KPICard({ label, value, sub, color, icon, badge, trend }: {
  label: string; value: string; sub: string; color: string; icon: string; badge?: string; trend?: string;
}) {
  return (
    <div className="metric-card">
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
        <span style={{ fontSize: 18, color }}>{icon}</span>
        {badge && <span className="badge badge-simulated">{badge}</span>}
      </div>
      <div className="metric-value" style={{ color }}>{value}</div>
      <div className="metric-label" style={{ marginTop: 4 }}>{label}</div>
      <div style={{ fontSize: 11, color: 'var(--text-secondary)', marginTop: 6 }}>
        {trend === 'up' && <span style={{ color: 'var(--status-critical)' }}>▲ </span>}
        {trend === 'down' && <span style={{ color: 'var(--accent-emerald)' }}>▼ </span>}
        {sub}
      </div>
    </div>
  );
}

function MiniSparkline({ data }: { data: Record<string, unknown>[] }) {
  const values = data.map(d => (d.avg_congestion as number) || 0);
  const max = Math.max(...values, 0.01);
  const width = 600;
  const height = 140;
  const points = values.map((v, i) => `${(i / Math.max(values.length - 1, 1)) * width},${height - (v / max) * height * 0.85 - 10}`).join(' ');

  return (
    <div style={{ width: '100%', overflow: 'hidden' }}>
      <svg viewBox={`0 0 ${width} ${height}`} style={{ width: '100%', height: 140 }}>
        <defs>
          <linearGradient id="sg" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="var(--accent-cyan)" stopOpacity="0.3" />
            <stop offset="100%" stopColor="var(--accent-cyan)" stopOpacity="0" />
          </linearGradient>
        </defs>
        <polyline fill="none" stroke="var(--accent-cyan)" strokeWidth="2" points={points} />
        <polygon fill="url(#sg)" points={`0,${height} ${points} ${width},${height}`} />
        {values.map((v, i) => (
          <circle key={i} cx={(i / Math.max(values.length - 1, 1)) * width} cy={height - (v / max) * height * 0.85 - 10}
            r="3" fill="var(--accent-cyan)" />
        ))}
      </svg>
    </div>
  );
}
