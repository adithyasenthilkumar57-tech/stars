'use client';
import { useState } from 'react';
import { AppState, NavPage } from '@/app/page';
import api from '@/lib/api';

interface Props { appState: AppState; updateOptimization: (o: Record<string, unknown>) => void; updateEmergency: (e: Record<string, unknown>) => void; setCurrentPage: (p: NavPage) => void; }

const DEFAULT_SCENARIO = {
  name: 'Demo Scenario', num_intersections: 6, traffic_volume: 'medium',
  emergency_vehicle: false, siren_detection: false, accident: false,
  road_closure: false, pedestrian_surge: false, duration_minutes: 10,
};

export default function Simulation({ appState }: Props) {
  const [scenario, setScenario] = useState({ ...DEFAULT_SCENARIO });
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<Record<string, unknown> | null>(null);
  const [step, setStep] = useState('');
  const [error, setError] = useState('');

  const handleRun = async () => {
    setRunning(true); setResult(null); setError('');
    const steps = ['Initializing intersection states...', 'Injecting traffic events...', `Simulating ${scenario.duration_minutes} minutes...`, 'Applying optimization mid-run...', 'Computing pollution estimates...', 'Generating results...'];
    for (const s of steps) {
      setStep(s);
      await new Promise(r => setTimeout(r, 400));
    }
    try {
      const r = await api.runSimulation({ ...scenario, id: `sim-${Date.now()}` });
      setResult(r);
    } catch (e: unknown) {
      setError((e as Error).message || 'Simulation failed');
    } finally {
      setRunning(false); setStep('');
    }
  };

  const bool = (key: keyof typeof scenario) => scenario[key] as boolean;
  const toggleBool = (key: keyof typeof scenario) => setScenario(s => ({ ...s, [key]: !s[key] }));

  return (
    <div className="page animate-fade-in">
      <div className="page-header">
        <div>
          <h2 className="page-title">Traffic Simulation</h2>
          <p className="page-subtitle">Custom Python discrete-event simulator — labeled SIMULATION throughout <span className="badge badge-simulated">SIMULATION</span></p>
        </div>
        <button className="btn btn-primary" onClick={handleRun} disabled={running} style={{ minWidth: 160 }}>
          {running ? '⟳ Simulating...' : '▶ Run Simulation'}
        </button>
      </div>

      <div className="grid-2">
        {/* Config */}
        <div className="card">
          <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 16 }}>Scenario Configuration</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            <Field label="Scenario Name">
              <input className="input" value={scenario.name} onChange={e => setScenario(s => ({ ...s, name: e.target.value }))} />
            </Field>
            <Field label="Traffic Volume">
              <select className="select" value={scenario.traffic_volume} onChange={e => setScenario(s => ({ ...s, traffic_volume: e.target.value }))}>
                {['low', 'medium', 'high', 'peak'].map(v => <option key={v} value={v}>{v.toUpperCase()}</option>)}
              </select>
            </Field>
            <Field label={`Duration: ${scenario.duration_minutes} min`}>
              <input type="range" min="5" max="60" step="5" value={scenario.duration_minutes}
                onChange={e => setScenario(s => ({ ...s, duration_minutes: parseInt(e.target.value) }))}
                style={{ width: '100%', accentColor: 'var(--accent-cyan)' }} />
            </Field>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
              {([
                ['emergency_vehicle', '🚑 Emergency Vehicle'],
                ['siren_detection', '🔊 Siren Detection'],
                ['accident', '🚧 Accident'],
                ['road_closure', '🚫 Road Closure'],
                ['pedestrian_surge', '🚶 Pedestrian Surge'],
              ] as [keyof typeof scenario, string][]).map(([key, label]) => (
                <label key={key} style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer', fontSize: 13 }}>
                  <label className="switch">
                    <input type="checkbox" checked={bool(key)} onChange={() => toggleBool(key)} />
                    <span className="switch-track" />
                  </label>
                  {label}
                </label>
              ))}
            </div>
          </div>
        </div>

        {/* Results or loading */}
        <div>
          {running && (
            <div className="card" style={{ borderColor: 'var(--accent-cyan)', textAlign: 'center', padding: 40 }}>
              <div style={{ fontSize: 40, animation: 'spin 1.5s linear infinite', marginBottom: 16 }}>▶</div>
              <div style={{ fontWeight: 700, marginBottom: 8 }}>Simulation Running</div>
              <div style={{ color: 'var(--text-secondary)', fontSize: 13 }}>{step}</div>
              <div style={{ marginTop: 12 }}><span className="badge badge-simulated">SIMULATION</span></div>
            </div>
          )}
          {error && <div className="alert-banner high">{error}</div>}
          {result && !running && <SimResult result={result} />}
          {!result && !running && (
            <div className="card" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: 250, color: 'var(--text-muted)', flexDirection: 'column', gap: 12 }}>
              <span style={{ fontSize: 40 }}>▶</span>
              <span>Configure and run a simulation to see results</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <label style={{ fontSize: 11, color: 'var(--text-secondary)', display: 'block', marginBottom: 5, textTransform: 'uppercase', letterSpacing: '0.06em' }}>{label}</label>
      {children}
    </div>
  );
}

function SimResult({ result }: { result: Record<string, unknown> }) {
  return (
    <div className="card animate-fade-in">
      <div style={{ fontWeight: 800, fontSize: 15, color: 'var(--accent-emerald)', marginBottom: 12 }}>
        ✓ Simulation Complete — {result.scenario_name as string}
        <span className="badge badge-simulated" style={{ marginLeft: 8 }}>SIMULATION</span>
      </div>
      <div className="grid-2" style={{ marginBottom: 16 }}>
        {[
          { l: 'Vehicles Processed', v: (result.total_vehicles_processed as number)?.toLocaleString() },
          { l: 'Avg Wait Time', v: `${(result.avg_waiting_time_seconds as number)?.toFixed(1)}s` },
          { l: 'Avg Queue', v: (result.avg_queue_length as number)?.toFixed(1) },
          { l: 'Improvement', v: `${(result.improvement_pct as number)?.toFixed(1)}%`, highlight: true },
        ].map(({ l, v, highlight }) => (
          <div key={l} style={{ padding: 10, background: 'var(--bg-secondary)', borderRadius: 8, textAlign: 'center' }}>
            <div style={{ fontWeight: 800, fontSize: 16, color: highlight ? 'var(--accent-emerald)' : 'var(--accent-cyan)' }}>{v}</div>
            <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>{l}</div>
          </div>
        ))}
      </div>
      {result.emergency_improvement_pct && (
        <div style={{ padding: 10, background: 'rgba(244,63,94,0.08)', borderRadius: 8, marginBottom: 10, fontSize: 12 }}>
          🚨 Emergency travel time improvement: <strong style={{ color: 'var(--accent-emerald)' }}>{(result.emergency_improvement_pct as number)?.toFixed(1)}%</strong> faster
          ({(result.emergency_travel_time_classical as number)?.toFixed(0)}s → {(result.emergency_travel_time_optimized as number)?.toFixed(0)}s)
          <span className="badge badge-simulated" style={{ marginLeft: 6 }}>SIMULATED</span>
        </div>
      )}
      {result.siren_timeline && (result.siren_timeline as Record<string, unknown>[]).length > 0 && (
        <div style={{ padding: 10, background: 'rgba(245,158,11,0.08)', borderRadius: 8, fontSize: 12 }}>
          🔊 Siren events: {(result.siren_timeline as Record<string, unknown>[]).map(e => e.event as string).join(' → ')}
        </div>
      )}
      <div style={{ marginTop: 10, fontSize: 10, color: 'var(--text-muted)' }}>
        Ticks simulated: {result.tick_count as number} • CO₂: {(result.total_co2_kg as number)?.toFixed(2)}kg • NOx: {(result.total_nox_g as number)?.toFixed(2)}g (ESTIMATED)
      </div>
    </div>
  );
}
