'use client';
import { useState, useEffect } from 'react';
import { AppState, NavPage } from '@/app/page';
import api from '@/lib/api';

interface Props { appState: AppState; updateOptimization: (o: Record<string, unknown>) => void; updateEmergency: (e: Record<string, unknown>) => void; setCurrentPage: (p: NavPage) => void; }

const SEV_ORDER = ['critical', 'high', 'medium', 'low', 'info'];
const SEV_COLOR: Record<string, string> = { critical: 'var(--status-critical)', high: 'var(--accent-orange)', medium: 'var(--accent-amber)', low: 'var(--accent-emerald)', info: 'var(--accent-blue)' };

const EVENT_TYPES = [
  { id: 'accident', label: '🚧 Accident', desc: 'Simulate a road accident' },
  { id: 'heavy_traffic', label: '🚗 Heavy Traffic', desc: 'Surge in vehicle volume' },
  { id: 'road_closure', label: '🚫 Road Closure', desc: 'Block a road segment' },
  { id: 'pedestrian_surge', label: '🚶 Pedestrian Surge', desc: 'Large crowd crossing' },
  { id: 'emergency_vehicle', label: '🚑 Emergency Vehicle', desc: 'Trigger green corridor' },
];

export default function AlertsCenter({ appState, setCurrentPage }: Props) {
  const [alerts, setAlerts] = useState<Record<string, unknown>[]>([]);
  const [selectedJunction, setSelectedJunction] = useState('J1');
  const [triggering, setTriggering] = useState<string | null>(null);
  const [aiResponse, setAiResponse] = useState<Record<string, unknown> | null>(null);

  const loadAlerts = async () => {
    try {
      const data = await api.getLiveTraffic();
      // Build alerts from high-congestion intersections
      const generated: Record<string, unknown>[] = (data.intersections || []).filter((i: Record<string, unknown>) => (i.congestion_score as number) > 0.5).map((i: Record<string, unknown>) => ({
        id: `alert-${i.id}`,
        type: (i.congestion_score as number) > 0.8 ? 'severe_congestion' : 'queue_growth',
        severity: (i.congestion_score as number) > 0.8 ? 'critical' : 'medium',
        title: `${(i.congestion_score as number) > 0.8 ? 'Severe Congestion' : 'Queue Growth'} — ${i.label}`,
        message: `Junction ${i.label} (${i.name}) at ${((i.congestion_score as number) * 100).toFixed(0)}% congestion. ${i.queue_length} vehicles queued.`,
        junction_label: i.label,
        created_at: new Date().toISOString(),
        is_active: true,
        data_source: 'DEMO',
      }));
      setAlerts(generated);
    } catch {}
  };

  useEffect(() => { loadAlerts(); }, [appState.intersections]);

  const handleTriggerEvent = async (eventType: string) => {
    setTriggering(eventType); setAiResponse(null);
    try {
      const r = await api.triggerEvent(eventType, selectedJunction);
      setAiResponse(r.ai_response as Record<string, unknown>);
      await loadAlerts();
      if (eventType === 'emergency_vehicle') setCurrentPage('emergency-corridor');
    } finally {
      setTriggering(null);
    }
  };

  const sortedAlerts = [...alerts].sort((a, b) => SEV_ORDER.indexOf(a.severity as string) - SEV_ORDER.indexOf(b.severity as string));

  return (
    <div className="page animate-fade-in">
      <div className="page-header">
        <div>
          <h2 className="page-title">Alerts Center</h2>
          <p className="page-subtitle">Live notifications from backend — trigger demo events to see AI responses <span className="badge badge-demo">DEMO</span></p>
        </div>
        <button className="btn btn-ghost" onClick={loadAlerts}>⟳ Refresh</button>
      </div>

      <div className="grid-2">
        {/* Active alerts */}
        <div>
          <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 12 }}>
            Active Alerts ({sortedAlerts.length})
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {sortedAlerts.length === 0 ? (
              <div className="card" style={{ textAlign: 'center', color: 'var(--text-muted)', padding: 40 }}>
                <div style={{ fontSize: 32, marginBottom: 8 }}>✓</div>
                No active alerts
              </div>
            ) : sortedAlerts.map((alert) => {
              const sev = alert.severity as string;
              const color = SEV_COLOR[sev] || 'var(--text-muted)';
              return (
                <div key={alert.id as string} className={`alert-banner ${sev}`}>
                  <div style={{ width: 10, height: 10, borderRadius: '50%', background: color, flexShrink: 0 }} />
                  <div style={{ flex: 1 }}>
                    <div style={{ fontWeight: 700, fontSize: 13 }}>{alert.title as string}</div>
                    <div style={{ fontSize: 12, opacity: 0.85, marginTop: 2 }}>{alert.message as string}</div>
                    <div style={{ fontSize: 10, opacity: 0.6, marginTop: 4 }}>
                      {new Date(alert.created_at as string).toLocaleTimeString()} •
                      <span className="data-label data-label-demo" style={{ marginLeft: 4 }}>{alert.data_source as string}</span>
                    </div>
                  </div>
                  <span className="badge" style={{ background: `${color}22`, color, border: `1px solid ${color}44`, fontSize: 9, marginLeft: 'auto' }}>
                    {sev.toUpperCase()}
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Event trigger panel */}
        <div className="card">
          <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 16 }}>Trigger Demo Events</div>
          <div style={{ marginBottom: 12 }}>
            <label style={{ fontSize: 11, color: 'var(--text-secondary)', display: 'block', marginBottom: 5, textTransform: 'uppercase', letterSpacing: '0.06em' }}>Target Junction</label>
            <select className="select" value={selectedJunction} onChange={e => setSelectedJunction(e.target.value)}>
              {['J1','J2','J3','J4','J5','J6'].map(j => <option key={j} value={j}>{j}</option>)}
            </select>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {EVENT_TYPES.map(({ id, label, desc }) => (
              <button key={id} className="btn btn-ghost"
                style={{ justifyContent: 'flex-start', padding: '10px 14px', textAlign: 'left', flexDirection: 'column', alignItems: 'flex-start', height: 'auto', gap: 2 }}
                onClick={() => handleTriggerEvent(id)}
                disabled={triggering !== null}>
                <div style={{ fontWeight: 700, fontSize: 13 }}>
                  {triggering === id ? '⟳ Triggering...' : label}
                </div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', fontWeight: 400 }}>{desc}</div>
              </button>
            ))}
          </div>

          {/* AI response */}
          {aiResponse && (
            <div className="animate-fade-in" style={{ marginTop: 16, padding: 12, background: 'rgba(16,185,129,0.08)', borderRadius: 10 }}>
              <div style={{ fontWeight: 700, fontSize: 12, color: 'var(--accent-emerald)', marginBottom: 8 }}>🤖 AI Response Pipeline</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                {((aiResponse.steps as string[]) || []).map((step, i) => (
                  <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12, animation: `fadeIn 0.3s ${i * 0.1}s ease both` }}>
                    <span style={{ color: 'var(--accent-emerald)', fontWeight: 700, width: 14 }}>{i + 1}.</span>
                    <span style={{ color: 'var(--text-secondary)' }}>{step}</span>
                  </div>
                ))}
              </div>
              <span className="badge badge-simulated" style={{ marginTop: 10, display: 'inline-block' }}>{aiResponse.data_source as string}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
