'use client';
import { useState, useEffect } from 'react';
import { AppState, NavPage } from '@/app/page';
import api from '@/lib/api';

interface Props { appState: AppState; updateOptimization: (o: Record<string, unknown>) => void; updateEmergency: (e: Record<string, unknown>) => void; setCurrentPage: (p: NavPage) => void; }

const STATUS_COLORS: Record<string, string> = {
  monitoring: 'var(--text-muted)',
  detected: 'var(--accent-amber)',
  alert_dispatched: 'var(--status-critical)',
  officer_acknowledged: 'var(--accent-blue)',
  clearance_in_progress: 'var(--accent-orange)',
  path_clear: 'var(--accent-emerald)',
  complete: 'var(--accent-emerald)',
  false_positive: 'var(--text-muted)',
};

export default function SirenDetection({ appState }: Props) {
  const [statuses, setStatuses] = useState<Record<string, unknown>[]>([]);
  const [events, setEvents] = useState<Record<string, unknown>[]>([]);
  const [dispatches, setDispatches] = useState<Record<string, unknown>[]>([]);
  const [triggering, setTriggering] = useState<string | null>(null);
  const [pipeline, setPipeline] = useState<string[]>([]);

  const loadAll = async () => {
    const [s, e, d] = await Promise.allSettled([
      api.getSirenStatuses(), api.getSirenEvents(), api.getDispatches(),
    ]);
    if (s.status === 'fulfilled') setStatuses(s.value.statuses || []);
    if (e.status === 'fulfilled') setEvents(e.value.events || []);
    if (d.status === 'fulfilled') setDispatches(d.value.dispatches || []);
  };

  useEffect(() => { loadAll(); }, []);

  const handleTrigger = async (jid: string) => {
    setTriggering(jid);
    setPipeline([]);
    const steps = [
      'Reading ambient audio (SIMULATED)',
      'Extracting 40 MFCC coefficients',
      'Classifying with SVC (sklearn)',
      'Confidence threshold check (≥0.75)',
      'Estimating approach direction (triangulation)',
      'Generating TTS voice alert (gTTS)',
      'Dispatching police alert × 5 (SIMULATED RADIO)',
      'Broadcasting WebSocket alert',
    ];
    for (let i = 0; i < steps.length; i++) {
      await new Promise(r => setTimeout(r, 350));
      setPipeline(p => [...p, steps[i]]);
    }
    try {
      await api.triggerSirenDetection(jid);
      await loadAll();
    } finally {
      setTriggering(null);
      setPipeline([]);
    }
  };

  const handleAcknowledge = async (eventId: string, jid: string, newStatus: string) => {
    try {
      await api.acknowledgeSiren(eventId, newStatus);
      await loadAll();
    } catch {}
  };

  const activeStatuses = statuses.filter(s => (s.status as string) !== 'monitoring');

  return (
    <div className="page animate-fade-in">
      <div className="page-header">
        <div>
          <h2 className="page-title">Siren Detection & Police Alert</h2>
          <p className="page-subtitle">
            MFCC + SVC classifier → TTS dispatch → Officer acknowledgment workflow
            <span className="badge badge-simulated" style={{ marginLeft: 6 }}>SIMULATED RADIO DISPATCH</span>
            <span className="badge badge-amber" style={{ marginLeft: 4 }}>NOT REAL POLICE RADIO</span>
          </p>
        </div>
      </div>

      {/* Active siren events */}
      {activeStatuses.length > 0 && (
        <div>
          <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 12 }}>🔊 Active Siren Alerts</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {activeStatuses.map((status) => {
              const event = status.active_event as Record<string, unknown>;
              const dispatch = status.active_dispatch as Record<string, unknown>;
              const statusKey = (status.status as string) || 'monitoring';
              return (
                <div key={status.junction_id as string} className="siren-panel active" style={{ padding: 16 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
                    <span style={{ fontSize: 24, animation: 'sirenPulse 1s infinite' }}>🔊</span>
                    <div>
                      <div style={{ fontWeight: 800, fontSize: 15, color: 'var(--accent-amber)' }}>
                        Junction {status.junction_label as string} — SIREN DETECTED
                      </div>
                      <div style={{ fontSize: 11, color: 'var(--text-secondary)' }}>
                        Confidence: {event ? `${((event.confidence as number) * 100).toFixed(1)}%` : '--'} •
                        Direction: {event?.approach_direction as string || '--'} •
                        Source: {status.data_source as string}
                      </div>
                    </div>
                    <div style={{ marginLeft: 'auto', textAlign: 'right' }}>
                      <div style={{ fontWeight: 700, fontSize: 12, color: STATUS_COLORS[statusKey] || 'var(--text-secondary)', textTransform: 'uppercase' }}>
                        {statusKey.replace(/_/g, ' ')}
                      </div>
                      <span className="badge badge-simulated">SIMULATED RADIO</span>
                    </div>
                  </div>
                  {dispatch && (
                    <div style={{ padding: 10, background: 'rgba(245,158,11,0.08)', borderRadius: 8, marginBottom: 10, fontSize: 12, color: 'var(--text-secondary)' }}>
                      📢 <strong>Dispatched:</strong> {dispatch.voice_message_text as string}
                    </div>
                  )}
                  {event && (
                    <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                      {['officer_acknowledged', 'clearance_in_progress', 'path_clear', 'false_positive'].map(s => (
                        <button key={s} className="btn btn-ghost" style={{ fontSize: 11, padding: '4px 10px' }}
                          onClick={() => handleAcknowledge(event.id as string, status.junction_id as string, s)}>
                          {s.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Detection pipeline visualization */}
      {triggering && (
        <div className="card" style={{ borderColor: 'var(--accent-amber)' }}>
          <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 12, color: 'var(--accent-amber)' }}>
            🔊 Running Siren Detection Pipeline — Junction {triggering}
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {pipeline.map((step, i) => (
              <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 10, fontSize: 13, animation: 'fadeIn 0.3s ease' }}>
                <span style={{ color: 'var(--accent-emerald)', fontWeight: 700 }}>✓</span>
                <span>{step}</span>
              </div>
            ))}
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, fontSize: 13, opacity: 0.5 }}>
              <span style={{ animation: 'spin 1s linear infinite', display: 'inline-block' }}>⟳</span>
              <span>Processing...</span>
            </div>
          </div>
        </div>
      )}

      {/* Junction test grid */}
      <div>
        <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 12 }}>Trigger Siren Detection (Demo)</div>
        <div className="grid-3">
          {(statuses.length > 0 ? statuses : ['J1','J2','J3','J4','J5','J6'].map(id => ({ junction_id: id, junction_label: id, status: 'monitoring', monitoring_active: true }))).map((s) => {
            const jid = s.junction_id as string;
            const statusKey = (s.status as string) || 'monitoring';
            const isActive = statusKey !== 'monitoring';
            return (
              <div key={jid} className={`card ${isActive ? 'siren-panel' : ''}`} style={{ borderColor: isActive ? 'var(--accent-amber)' : 'var(--border-subtle)' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
                  <div style={{ fontWeight: 800, fontSize: 18, color: isActive ? 'var(--accent-amber)' : 'var(--text-secondary)' }}>{s.junction_label as string}</div>
                  <div style={{ width: 8, height: 8, borderRadius: '50%', background: STATUS_COLORS[statusKey] || 'var(--text-muted)', boxShadow: isActive ? `0 0 8px ${STATUS_COLORS[statusKey]}` : 'none' }} />
                </div>
                <div style={{ fontSize: 11, color: 'var(--text-secondary)', marginBottom: 10, textTransform: 'uppercase' }}>
                  {statusKey.replace(/_/g, ' ')}
                </div>
                <div style={{ display: 'flex', gap: 6 }}>
                  <button
                    className="btn btn-ghost"
                    style={{ flex: 1, fontSize: 11, padding: '6px 8px', justifyContent: 'center' }}
                    onClick={() => handleTrigger(jid)}
                    disabled={triggering !== null}
                  >
                    {triggering === jid ? '⟳' : '🔊'} Trigger
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Event history */}
      {events.length > 0 && (
        <div className="card">
          <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 12 }}>Detection History</div>
          <div className="table-wrapper">
            <table>
              <thead><tr>
                <th>Junction</th><th>Confidence</th><th>Direction</th><th>Status</th><th>Time</th><th>Source</th>
              </tr></thead>
              <tbody>
                {events.slice(0, 20).map((e) => (
                  <tr key={e.id as string}>
                    <td><strong>{e.junction_label as string}</strong></td>
                    <td style={{ color: (e.confidence as number) > 0.85 ? 'var(--status-critical)' : 'var(--accent-amber)', fontWeight: 700 }}>
                      {((e.confidence as number) * 100).toFixed(1)}%
                    </td>
                    <td>{e.approach_direction as string}</td>
                    <td><span className="badge badge-amber">{(e.status as string)?.replace(/_/g, ' ')}</span></td>
                    <td style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 11, color: 'var(--text-secondary)' }}>
                      {new Date(e.detected_at as string).toLocaleTimeString()}
                    </td>
                    <td><span className="data-label data-label-simulated">{e.data_source as string}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
