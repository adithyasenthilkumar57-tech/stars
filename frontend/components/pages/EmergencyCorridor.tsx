'use client';
import { useState, useEffect } from 'react';
import { AppState, NavPage } from '@/app/page';
import api from '@/lib/api';

interface Props { appState: AppState; updateOptimization: (o: Record<string, unknown>) => void; updateEmergency: (e: Record<string, unknown>) => void; setCurrentPage: (p: NavPage) => void; }

const JUNCTIONS = ['J1', 'J2', 'J3', 'J4', 'J5', 'J6'];

export default function EmergencyCorridor({ appState, updateEmergency }: Props) {
  const [origin, setOrigin] = useState('J1');
  const [activating, setActivating] = useState(false);
  const [advancing, setAdvancing] = useState(false);
  const [status, setStatus] = useState<Record<string, unknown> | null>(null);

  useEffect(() => {
    api.getEmergencyStatus().then(setStatus).catch(() => {});
  }, []);

  useEffect(() => {
    if (appState.emergency && Object.keys(appState.emergency).length) {
      setStatus(appState.emergency as Record<string, unknown>);
    }
  }, [appState.emergency]);

  const active = !!(status?.active);
  const corridorStatus = (status?.corridor_status as string) || 'inactive';
  const route = status?.route as Record<string, unknown> | null;
  const vehicle = status?.emergency_vehicle as Record<string, unknown> | null;

  const handleActivate = async () => {
    setActivating(true);
    try {
      const r = await api.activateEmergency(origin);
      setStatus(r);
      updateEmergency(r);
    } finally {
      setActivating(false);
    }
  };

  const handleAdvance = async () => {
    setAdvancing(true);
    try {
      const r = await api.advanceCorridor();
      setStatus(r);
      updateEmergency(r);
    } finally {
      setAdvancing(false);
    }
  };

  const handleComplete = async () => {
    const r = await api.completeCorridor();
    setStatus(r);
    updateEmergency(r);
  };

  const handleReset = async () => {
    const r = await api.resetCorridor();
    setStatus(r);
    updateEmergency(r);
  };

  const progress = (status?.progress_pct as number) || 0;
  const routeIds: string[] = (route?.route_intersection_ids as string[]) || [];
  const currentIdx = (route?.current_junction_index as number) || 0;

  return (
    <div className="page animate-fade-in">
      <div className="page-header">
        <div>
          <h2 className="page-title">Emergency Green Corridor</h2>
          <p className="page-subtitle">
            AI-optimized ambulance routing via NetworkX Dijkstra — lifecycle: INACTIVE → DETECTED → CORRIDOR_ACTIVE → COMPLETE
            <span className="badge badge-simulated" style={{ marginLeft: 6 }}>SIMULATED</span>
          </p>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          {active ? (
            <>
              <button className="btn btn-success" onClick={handleAdvance} disabled={advancing}>
                {advancing ? '⟳' : '▶'} Advance Corridor
              </button>
              <button className="btn btn-ghost" onClick={handleComplete}>Complete</button>
              <button className="btn btn-danger" onClick={handleReset}>Reset</button>
            </>
          ) : (
            <button className="btn btn-danger" onClick={handleActivate} disabled={activating} style={{ minWidth: 180 }}>
              {activating ? '⟳' : '🚨'} {activating ? 'Activating...' : 'Activate Corridor'}
            </button>
          )}
        </div>
      </div>

      {/* Status banner */}
      <div className={`emergency-panel ${active ? 'active' : ''}`} style={{ padding: 20 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
          <span style={{ fontSize: 28 }}>{active ? '🚨' : '🚑'}</span>
          <div>
            <div style={{ fontWeight: 800, fontSize: 18, color: active ? 'var(--status-critical)' : 'var(--text-secondary)' }}>
              {corridorStatus.replace(/_/g, ' ').toUpperCase()}
            </div>
            <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
              {active ? `Emergency vehicle en route — ${progress.toFixed(0)}% complete` : 'No active emergency corridor'}
            </div>
          </div>
          <span className="badge badge-simulated" style={{ marginLeft: 'auto' }}>SIMULATED</span>
        </div>

        {/* Progress bar */}
        {active && (
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6, fontSize: 12 }}>
              <span style={{ color: 'var(--text-secondary)' }}>Corridor Progress</span>
              <span style={{ color: 'var(--accent-emerald)', fontWeight: 700 }}>{progress.toFixed(0)}%</span>
            </div>
            <div className="progress-bar" style={{ height: 8 }}>
              <div className="progress-fill" style={{ width: `${progress}%`, background: 'var(--status-critical)', boxShadow: '0 0 10px var(--status-critical)' }} />
            </div>
          </div>
        )}
      </div>

      <div className="grid-2">
        {/* Activation form */}
        {!active && (
          <div className="card">
            <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 16 }}>Corridor Configuration</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <div>
                <label style={{ fontSize: 11, color: 'var(--text-secondary)', display: 'block', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.06em' }}>Origin Junction</label>
                <select className="select" value={origin} onChange={e => setOrigin(e.target.value)}>
                  {JUNCTIONS.map(j => <option key={j} value={j}>{j}</option>)}
                </select>
              </div>
              <div>
                <label style={{ fontSize: 11, color: 'var(--text-secondary)', display: 'block', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.06em' }}>Destination</label>
                <div className="input" style={{ color: 'var(--text-secondary)', cursor: 'default' }}>City Hospital (J6) — Fixed</div>
              </div>
              <div style={{ padding: 12, background: 'rgba(244,63,94,0.06)', borderRadius: 8, fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                <strong style={{ color: 'var(--status-critical)' }}>What happens:</strong> System calculates shortest path via NetworkX Dijkstra, activates green phases along the route, dispatches signal overrides to all corridor junctions, and tracks ambulance progress.
              </div>
            </div>
          </div>
        )}

        {/* Route visualization */}
        {route && routeIds.length > 0 && (
          <div className="card">
            <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 16 }}>Corridor Route</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {routeIds.map((jid, idx) => {
                const isPassed = idx < currentIdx;
                const isCurrent = idx === currentIdx;
                const isAhead = idx > currentIdx;
                return (
                  <div key={jid} style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                    <div style={{
                      width: 32, height: 32, borderRadius: '50%',
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      fontWeight: 900, fontSize: 12,
                      background: isPassed ? 'var(--accent-emerald)' : isCurrent ? 'var(--status-critical)' : 'var(--bg-secondary)',
                      color: isPassed || isCurrent ? '#000' : 'var(--text-muted)',
                      border: isCurrent ? '3px solid var(--status-critical)' : 'none',
                      animation: isCurrent ? 'pulse-red 1s infinite' : 'none',
                    }}>
                      {isPassed ? '✓' : jid}
                    </div>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontWeight: 600, fontSize: 13, color: isCurrent ? 'var(--status-critical)' : isPassed ? 'var(--accent-emerald)' : 'var(--text-secondary)' }}>
                        Junction {jid} {isCurrent ? '← 🚨 HERE' : isPassed ? '— Cleared' : isAhead ? '— Green Pending' : ''}
                      </div>
                      {isCurrent && (
                        <div style={{ fontSize: 11, color: 'var(--status-critical)' }}>EMERGENCY OVERRIDE ACTIVE — all green</div>
                      )}
                    </div>
                  </div>
                );
              })}
              {/* Destination */}
              <div style={{ display: 'flex', alignItems: 'center', gap: 12, paddingTop: 8, borderTop: '1px solid var(--border-subtle)' }}>
                <div style={{ width: 32, height: 32, borderRadius: '50%', background: progress >= 100 ? 'var(--accent-emerald)' : 'var(--bg-secondary)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 14 }}>🏥</div>
                <div style={{ fontWeight: 700, color: progress >= 100 ? 'var(--accent-emerald)' : 'var(--text-secondary)' }}>
                  City Hospital — {progress >= 100 ? 'ARRIVED' : 'Destination'}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Travel time comparison */}
        {route && (
          <div className="card">
            <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 16 }}>Travel Time Comparison</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <CompareBar
                label="Classical (Red Lights)"
                value={route.estimated_travel_time_classical as number}
                max={Math.max(route.estimated_travel_time_classical as number, 600)}
                color="var(--status-critical)"
              />
              <CompareBar
                label="AI Green Corridor"
                value={route.estimated_travel_time_optimized as number}
                max={Math.max(route.estimated_travel_time_classical as number, 600)}
                color="var(--accent-emerald)"
              />
              <div style={{ padding: 12, background: 'rgba(16,185,129,0.08)', borderRadius: 8, textAlign: 'center' }}>
                <span style={{ fontSize: 24, fontWeight: 900, color: 'var(--accent-emerald)' }}>
                  {(route.improvement_pct as number)?.toFixed(1)}%
                </span>
                <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>Faster than classical routing</div>
                <span className="badge badge-simulated" style={{ marginTop: 6, display: 'inline-block' }}>SIMULATED</span>
              </div>
              <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                ETA remaining: {(route.eta_seconds as number)?.toFixed(0)}s •
                Distance: {(route.total_distance_meters as number)?.toFixed(0)}m
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function CompareBar({ label, value, max, color }: { label: string; value: number; max: number; color: string }) {
  const pct = (value / max) * 100;
  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4, fontSize: 12 }}>
        <span style={{ color: 'var(--text-secondary)' }}>{label}</span>
        <span style={{ fontWeight: 700, color }}>{value?.toFixed(0)}s</span>
      </div>
      <div className="progress-bar" style={{ height: 12 }}>
        <div className="progress-fill" style={{ width: `${pct}%`, background: color, transition: 'width 1s ease' }} />
      </div>
    </div>
  );
}
