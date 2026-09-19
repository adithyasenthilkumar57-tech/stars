'use client';
import { useState, useEffect } from 'react';
import { AppState, NavPage } from '@/app/page';
import api from '@/lib/api';
import CongestionBar from '@/components/shared/CongestionBar';

interface Props { appState: AppState; updateOptimization: (o: Record<string, unknown>) => void; updateEmergency: (e: Record<string, unknown>) => void; setCurrentPage: (p: NavPage) => void; }

export default function LiveMonitor({ appState, setCurrentPage }: Props) {
  const { intersections } = appState;
  const [selected, setSelected] = useState<string | null>(null);
  const [detail, setDetail] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!selected) return;
    setLoading(true);
    api.getIntersection(selected).then(setDetail).catch(() => setDetail(null)).finally(() => setLoading(false));
  }, [selected]);

  return (
    <div className="page animate-fade-in">
      <div className="page-header">
        <div>
          <h2 className="page-title">Live Traffic Monitor</h2>
          <p className="page-subtitle">Real-time intersection state — auto-refreshes via WebSocket <span className="badge badge-simulated">DEMO DATA</span></p>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: selected ? '1fr 380px' : '1fr', gap: 16, transition: 'all 0.3s' }}>
        {/* Junction grid */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12 }}>
          {intersections.length === 0 && [1,2,3,4,5,6].map(i => (
            <div key={i} className="skeleton" style={{ height: 180, borderRadius: 12 }} />
          ))}
          {intersections.map((inter) => {
            const i = inter as Record<string, unknown>;
            const score = (i.congestion_score as number) || 0;
            const level = (i.congestion_level as string) || 'low';
            const isSelected = selected === i.id;
            return (
              <div
                key={i.id as string}
                className="card"
                style={{
                  cursor: 'pointer',
                  borderColor: isSelected ? 'var(--accent-cyan)' : score > 0.7 ? 'rgba(244,63,94,0.3)' : 'var(--border-subtle)',
                  boxShadow: isSelected ? '0 0 20px rgba(0,212,255,0.2)' : score > 0.7 ? '0 0 15px rgba(244,63,94,0.15)' : 'none',
                  transition: 'all 0.2s',
                }}
                onClick={() => setSelected(isSelected ? null : i.id as string)}
              >
                <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 12 }}>
                  <div style={{
                    width: 40, height: 40, borderRadius: 10, fontWeight: 900, fontSize: 14,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    background: score > 0.7 ? 'rgba(244,63,94,0.15)' : score > 0.5 ? 'rgba(245,158,11,0.15)' : 'rgba(16,185,129,0.15)',
                    color: score > 0.7 ? 'var(--status-critical)' : score > 0.5 ? 'var(--accent-amber)' : 'var(--accent-emerald)',
                  }}>{i.label as string}</div>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontSize: 22, fontWeight: 900, color: score > 0.7 ? 'var(--status-critical)' : score > 0.5 ? 'var(--accent-amber)' : 'var(--accent-emerald)' }}>
                      {(score * 100).toFixed(0)}%
                    </div>
                    <div style={{ fontSize: 9, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>{level}</div>
                  </div>
                </div>
                <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 8, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                  {i.name as string}
                </div>
                <CongestionBar score={score} level={level} />
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 6, marginTop: 10 }}>
                  <Chip label="Vehicles" value={String(i.vehicle_count ?? 0)} />
                  <Chip label="Queue" value={String(i.queue_length ?? 0)} />
                  <Chip label="Wait" value={`${((i.waiting_time_seconds as number) || 0).toFixed(0)}s`} />
                </div>
                {/* Signal phase */}
                {(i.signal as Record<string, unknown>) && (
                  <div style={{ marginTop: 10, display: 'flex', alignItems: 'center', gap: 8 }}>
                    <PhaseIndicator phase={((i.signal as Record<string, unknown>).current_phase as string) || ''} />
                    <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>
                      {((i.signal as Record<string, unknown>).phase_remaining_seconds as number) || 0}s remaining
                    </span>
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Detail panel */}
        {selected && (
          <div className="card animate-slide-in" style={{ height: 'fit-content', position: 'sticky', top: 80 }}>
            {loading ? (
              <div className="skeleton" style={{ height: 300 }} />
            ) : detail ? (
              <IntersectionDetail detail={detail} onClose={() => setSelected(null)} />
            ) : null}
          </div>
        )}
      </div>
    </div>
  );
}

function Chip({ label, value }: { label: string; value: string }) {
  return (
    <div style={{ textAlign: 'center', padding: '4px 6px', background: 'var(--bg-secondary)', borderRadius: 6 }}>
      <div style={{ fontWeight: 700, fontSize: 12, color: 'var(--text-primary)' }}>{value}</div>
      <div style={{ fontSize: 9, color: 'var(--text-muted)', textTransform: 'uppercase' }}>{label}</div>
    </div>
  );
}

function PhaseIndicator({ phase }: { phase: string }) {
  const isNS = phase.includes('north_south') || phase.includes('ns');
  const isEW = phase.includes('east_west') || phase.includes('ew');
  const isEm = phase.includes('emergency');
  return (
    <div style={{ display: 'flex', gap: 4, alignItems: 'center' }}>
      <div style={{ width: 20, height: 10, borderRadius: 3, background: isNS ? 'var(--accent-emerald)' : 'rgba(255,255,255,0.1)', transition: 'all 0.3s' }} />
      <div style={{ width: 10, height: 20, borderRadius: 3, background: isEW ? 'var(--accent-emerald)' : 'rgba(255,255,255,0.1)', transition: 'all 0.3s' }} />
      {isEm && <span style={{ fontSize: 10, color: 'var(--status-critical)', fontWeight: 700 }}>EM</span>}
    </div>
  );
}

function IntersectionDetail({ detail, onClose }: { detail: Record<string, unknown>; onClose: () => void }) {
  const inter = (detail.intersection || detail) as Record<string, unknown>;
  const pred = detail.prediction as Record<string, unknown>;
  const poll = detail.pollution as Record<string, unknown>;

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
        <div>
          <div style={{ fontWeight: 800, fontSize: 16 }}>{inter.label as string} — {inter.name as string}</div>
          <div style={{ fontSize: 11, color: 'var(--text-secondary)' }}>{inter.latitude as number}, {inter.longitude as number}</div>
        </div>
        <button className="btn btn-ghost" style={{ fontSize: 10, padding: '4px 8px' }} onClick={onClose}>✕</button>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginBottom: 16 }}>
        {[
          { l: 'Congestion', v: `${((inter.congestion_score as number) * 100).toFixed(1)}%` },
          { l: 'Vehicles', v: String(inter.vehicle_count ?? 0) },
          { l: 'Queue', v: String(inter.queue_length ?? 0) },
          { l: 'Wait', v: `${((inter.waiting_time_seconds as number) || 0).toFixed(0)}s` },
          { l: 'Speed', v: `${((inter.average_speed_kmh as number) || 0).toFixed(0)} km/h` },
          { l: 'Throughput', v: `${inter.throughput_vph ?? 0} vph` },
        ].map(({ l, v }) => (
          <div key={l} style={{ padding: 8, background: 'var(--bg-secondary)', borderRadius: 8, textAlign: 'center' }}>
            <div style={{ fontWeight: 700, fontSize: 14, color: 'var(--accent-cyan)' }}>{v}</div>
            <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>{l}</div>
          </div>
        ))}
      </div>
      {poll && (
        <div style={{ padding: 12, background: 'rgba(139,92,246,0.08)', borderRadius: 8, marginBottom: 12 }}>
          <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--accent-purple)', marginBottom: 6 }}>ESTIMATED EMISSIONS</div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6, fontSize: 12 }}>
            <div>CO₂: <strong>{(poll.co2_kg_per_hour as number)?.toFixed(2)} kg/hr</strong></div>
            <div>NOx: <strong>{(poll.nox_g_per_hour as number)?.toFixed(2)} g/hr</strong></div>
            <div>AQI: <strong>{poll.aqi_estimate as number} ({poll.aqi_category as string})</strong></div>
            <div>PM2.5: <strong>{(poll.pm25_g_per_hour as number)?.toFixed(4)} g/hr</strong></div>
          </div>
        </div>
      )}
      {pred && (
        <div style={{ padding: 12, background: 'rgba(16,185,129,0.08)', borderRadius: 8 }}>
          <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--accent-emerald)', marginBottom: 6 }}>AI PREDICTION</div>
          <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
            Trend: <strong style={{ color: 'var(--text-primary)' }}>{pred.trend as string}</strong> —
            Overload risk: <strong style={{ color: pred.overload_risk ? 'var(--status-critical)' : 'var(--accent-emerald)' }}>
              {pred.overload_risk ? 'YES' : 'NO'}
            </strong>
          </div>
        </div>
      )}
      <div style={{ marginTop: 10, fontSize: 9, color: 'var(--text-muted)' }}>
        Source: {inter.data_source as string || 'DEMO'}
      </div>
    </div>
  );
}
