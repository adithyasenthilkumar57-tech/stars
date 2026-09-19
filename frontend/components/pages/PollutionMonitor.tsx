'use client';
import { useState, useEffect } from 'react';
import { AppState, NavPage } from '@/app/page';
import api from '@/lib/api';

interface Props { appState: AppState; updateOptimization: (o: Record<string, unknown>) => void; updateEmergency: (e: Record<string, unknown>) => void; setCurrentPage: (p: NavPage) => void; }

const AQI_COLORS: Record<string, string> = { 'Good': 'var(--accent-emerald)', 'Moderate': 'var(--accent-cyan)', 'Unhealthy for Sensitive Groups': 'var(--accent-amber)', 'Unhealthy': 'var(--accent-orange)', 'Very Unhealthy': 'var(--status-critical)', 'Hazardous': '#9c1c2e' };

export default function PollutionMonitor({ appState }: Props) {
  const [estimates, setEstimates] = useState<Record<string, unknown>[]>([]);
  const [totals, setTotals] = useState<Record<string, unknown>>({});
  const [trend, setTrend] = useState<Record<string, unknown>[]>([]);
  const [selectedId, setSelectedId] = useState<string>('J1');

  useEffect(() => {
    api.getPollutionEstimates().then(d => {
      setEstimates(d.estimates || []);
      setTotals(d.network_totals || {});
    }).catch(() => {});
  }, [appState.intersections]);

  useEffect(() => {
    if (selectedId) {
      api.getPollutionTrend(selectedId, 12).then(d => setTrend(d.trend || [])).catch(() => {});
    }
  }, [selectedId]);

  return (
    <div className="page animate-fade-in">
      <div className="page-header">
        <div>
          <h2 className="page-title">Pollution Monitor</h2>
          <p className="page-subtitle">
            Emission estimates from vehicle count × type factors — AQI computed
            <span className="badge badge-estimated" style={{ marginLeft: 6 }}>ESTIMATED</span>
            <span className="badge badge-simulated" style={{ marginLeft: 4 }}>NOT MEASURED</span>
          </p>
        </div>
      </div>

      {/* Network totals */}
      <div className="grid-4">
        {[
          { label: 'CO₂ (Network)', value: `${(totals.co2_kg_per_hour as number)?.toFixed(2)} kg/hr`, color: 'var(--accent-amber)', icon: '☁' },
          { label: 'NOx (Network)', value: `${(totals.nox_g_per_hour as number)?.toFixed(2)} g/hr`, color: 'var(--accent-orange)', icon: '◌' },
          { label: 'PM2.5 (Network)', value: `${(totals.pm25_g_per_hour as number)?.toFixed(4)} g/hr`, color: 'var(--status-critical)', icon: '●' },
          { label: 'Avg AQI', value: String(totals.avg_aqi ?? '--'), color: AQI_COLORS['Moderate'], icon: '◈' },
        ].map(({ label, value, color, icon }) => (
          <div key={label} className="metric-card">
            <div style={{ fontSize: 20, color, marginBottom: 6 }}>{icon}</div>
            <div className="metric-value" style={{ color }}>{value}</div>
            <div className="metric-label">{label}</div>
            <div style={{ fontSize: 9, color: 'var(--text-muted)', marginTop: 4 }}>ESTIMATED — NOT MEASURED</div>
          </div>
        ))}
      </div>

      <div className="grid-2">
        {/* Per-junction estimates */}
        <div className="card">
          <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 12 }}>Emission Estimates by Junction <span className="badge badge-estimated">ESTIMATED</span></div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {(estimates.length > 0 ? estimates : appState.intersections.slice(0, 6).map(i => ({ ...(i as Record<string, unknown>), junction_label: (i as Record<string, unknown>).label }))).map((est) => {
              const aqi = est.aqi_estimate as number || 0;
              const cat = est.aqi_category as string || 'Unknown';
              const color = AQI_COLORS[cat] || 'var(--text-muted)';
              return (
                <div key={est.intersection_id as string || est.id as string}
                  style={{ padding: 12, background: selectedId === (est.intersection_id as string || est.id as string) ? 'rgba(0,212,255,0.05)' : 'var(--bg-secondary)', borderRadius: 8, cursor: 'pointer', border: `1px solid ${selectedId === (est.intersection_id as string || est.id as string) ? 'rgba(0,212,255,0.3)' : 'transparent'}` }}
                  onClick={() => setSelectedId(est.intersection_id as string || est.id as string)}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 6 }}>
                    <strong style={{ color: 'var(--accent-cyan)' }}>{est.junction_label as string}</strong>
                    <div style={{ display: 'flex', align: 'center', gap: 8 }}>
                      <span style={{ fontWeight: 700, color, fontSize: 12 }}>AQI {aqi}</span>
                      <span style={{ fontSize: 10, color, padding: '1px 6px', background: `${color}22`, borderRadius: 4 }}>{cat}</span>
                    </div>
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 6, fontSize: 11, color: 'var(--text-secondary)' }}>
                    <span>CO₂: {(est.co2_kg_per_hour as number)?.toFixed(3)} kg/hr</span>
                    <span>NOx: {(est.nox_g_per_hour as number)?.toFixed(3)} g/hr</span>
                    <span>Fuel: {(est.fuel_liters_per_hour as number)?.toFixed(2)} L/hr</span>
                  </div>
                  {est.ai_insight && (
                    <div style={{ marginTop: 6, fontSize: 11, color: 'var(--text-secondary)', borderTop: '1px solid var(--border-subtle)', paddingTop: 6 }}>
                      💡 {est.ai_insight as string}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* 12-hour trend */}
        <div className="card">
          <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 12 }}>
            12-Hour CO₂ Trend — Junction {selectedId}
            <span className="badge badge-estimated" style={{ marginLeft: 6 }}>ESTIMATED HISTORICAL</span>
          </div>
          {trend.length > 0 ? (
            <TrendChart data={trend} />
          ) : (
            <div className="skeleton" style={{ height: 200 }} />
          )}
        </div>
      </div>
    </div>
  );
}

function TrendChart({ data }: { data: Record<string, unknown>[] }) {
  const values = data.map(d => d.co2_kg_per_hour as number || 0);
  const max = Math.max(...values, 0.01);
  const W = 600; const H = 180;
  const pts = values.map((v, i) => `${(i / Math.max(values.length - 1, 1)) * W},${H - (v / max) * H * 0.8 - 10}`).join(' ');
  return (
    <div>
      <svg viewBox={`0 0 ${W} ${H}`} style={{ width: '100%', height: 180 }}>
        <defs>
          <linearGradient id="cg" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="var(--accent-purple)" stopOpacity="0.4" />
            <stop offset="100%" stopColor="var(--accent-purple)" stopOpacity="0" />
          </linearGradient>
        </defs>
        <polyline fill="none" stroke="var(--accent-purple)" strokeWidth="2" points={pts} />
        <polygon fill="url(#cg)" points={`0,${H} ${pts} ${W},${H}`} />
        {values.map((v, i) => (
          <circle key={i} cx={(i / Math.max(values.length - 1, 1)) * W} cy={H - (v / max) * H * 0.8 - 10} r="3" fill="var(--accent-purple)" />
        ))}
      </svg>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, color: 'var(--text-muted)' }}>
        {data.filter((_, i) => i % 3 === 0).map((d, i) => (
          <span key={i}>{d.hour as number}:00</span>
        ))}
      </div>
    </div>
  );
}
