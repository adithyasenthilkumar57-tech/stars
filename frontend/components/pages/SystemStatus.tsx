'use client';
import { useState, useEffect } from 'react';
import { AppState, NavPage } from '@/app/page';
import api from '@/lib/api';

interface Props { appState: AppState; updateOptimization: (o: Record<string, unknown>) => void; updateEmergency: (e: Record<string, unknown>) => void; setCurrentPage: (p: NavPage) => void; }

export default function SystemStatus({ appState }: Props) {
  const [config, setConfig] = useState<Record<string, unknown> | null>(null);
  const [health, setHealth] = useState<Record<string, unknown> | null>(null);
  const [demoUsers, setDemoUsers] = useState<Record<string, unknown>[]>([]);

  useEffect(() => {
    api.getFirebaseConfig().then(setConfig).catch(() => {});
    api.health().then(setHealth).catch(() => {});
    api.getDemoUsers().then(d => setDemoUsers(d.demo_users || [])).catch(() => {});
  }, []);

  const sys = (config?.system_status || health?.system || {}) as Record<string, unknown>;
  const fbConfig = config?.firebase_config as Record<string, unknown> | null;

  const services = [
    { name: 'FastAPI Backend', status: health ? 'ok' : 'unknown', color: health ? 'var(--accent-emerald)' : 'var(--text-muted)' },
    { name: 'Firebase Admin SDK', status: sys.firebase_connected ? 'connected' : 'not_configured', color: sys.firebase_connected ? 'var(--accent-emerald)' : 'var(--accent-amber)' },
    { name: 'Gemini AI (AIRA)', status: sys.gemini_available ? 'available' : 'not_configured', color: sys.gemini_available ? 'var(--accent-emerald)' : 'var(--accent-amber)' },
    { name: 'Qiskit Aer (Quantum Sim)', status: sys.qiskit_available ? 'available' : 'classical_fallback', color: sys.qiskit_available ? 'var(--accent-cyan)' : 'var(--accent-blue)' },
    { name: 'OpenCV (Camera CV)', status: sys.cv2_available ? 'available' : 'simulated', color: sys.cv2_available ? 'var(--accent-emerald)' : 'var(--accent-blue)' },
    { name: 'scikit-learn (Audio ML)', status: sys.sklearn_available ? 'available' : 'simulated', color: sys.sklearn_available ? 'var(--accent-emerald)' : 'var(--accent-blue)' },
    { name: 'gTTS (Voice Dispatch)', status: sys.gtts_available ? 'available' : 'simulated', color: sys.gtts_available ? 'var(--accent-emerald)' : 'var(--accent-blue)' },
    { name: 'WebSocket Hub', status: appState.wsConnected ? 'connected' : 'polling', color: appState.wsConnected ? 'var(--accent-emerald)' : 'var(--accent-amber)' },
  ];

  return (
    <div className="page animate-fade-in">
      <div className="page-header">
        <div>
          <h2 className="page-title">System Status</h2>
          <p className="page-subtitle">Backend health, API key configuration, and service availability</p>
        </div>
        <span className={`badge ${health ? 'badge-emerald' : 'badge-simulated'}`}>
          {health ? '✓ Backend Online' : 'Backend Offline'}
        </span>
      </div>

      {/* Data mode banner */}
      <div className="alert-banner medium">
        <span>⚠</span>
        <div>
          <strong>Data Mode: {(sys.data_mode as string || 'DEMO').toUpperCase()}</strong> —
          All data is DEMO/SIMULATED. No real sensors connected. Firebase not configured = in-memory only.
          Emissions are ESTIMATED. Quantum uses QUANTUM SIMULATOR. Audio uses SIMULATED RADIO DISPATCH.
        </div>
      </div>

      <div className="grid-2">
        {/* Service status */}
        <div className="card">
          <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 16 }}>Service Status</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {services.map(({ name, status, color }) => (
              <div key={name} style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '8px 12px', background: 'var(--bg-secondary)', borderRadius: 8 }}>
                <div style={{ width: 8, height: 8, borderRadius: '50%', background: color, boxShadow: `0 0 6px ${color}` }} />
                <span style={{ flex: 1, fontSize: 13, fontWeight: 500 }}>{name}</span>
                <span style={{ fontSize: 11, fontWeight: 600, color, textTransform: 'uppercase', letterSpacing: '0.06em' }}>{status.replace(/_/g, ' ')}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Firebase config */}
        <div className="card">
          <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 16 }}>Firebase Configuration</div>
          {fbConfig ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {Object.entries(fbConfig).map(([k, v]) => (
                <div key={k} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '6px 10px', background: 'var(--bg-secondary)', borderRadius: 6 }}>
                  <span style={{ fontSize: 11, color: 'var(--text-muted)', minWidth: 120 }}>{k}</span>
                  <span style={{ fontSize: 11, fontFamily: 'JetBrains Mono, monospace', color: v ? 'var(--accent-emerald)' : 'var(--accent-amber)' }}>
                    {v ? (String(v).startsWith('AIza') ? '••••' + String(v).slice(-6) : String(v)) : 'not configured'}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <div style={{ padding: 20, textAlign: 'center', color: 'var(--text-muted)' }}>
              <div style={{ fontSize: 24, marginBottom: 8 }}>🔥</div>
              <div>Firebase not configured</div>
              <div style={{ fontSize: 12, marginTop: 6 }}>Set FIREBASE_* in .env to enable persistent storage</div>
              <div style={{ marginTop: 10, fontSize: 12, color: 'var(--accent-amber)' }}>Running in DEMO mode — in-memory store</div>
            </div>
          )}
        </div>

        {/* Demo users */}
        <div className="card">
          <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 16 }}>Demo Users</div>
          <div className="table-wrapper">
            <table>
              <thead><tr><th>Email</th><th>Role</th><th>Password</th></tr></thead>
              <tbody>
                {demoUsers.length > 0 ? demoUsers.map((u) => (
                  <tr key={u.email as string}>
                    <td style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 12 }}>{u.email as string}</td>
                    <td><span className="badge badge-cyan">{u.role as string}</span></td>
                    <td style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 12, color: 'var(--accent-amber)' }}>demo123</td>
                  </tr>
                )) : (
                  ['admin@clearway.demo', 'operator@clearway.demo', 'police@clearway.demo', 'analyst@clearway.demo'].map(e => (
                    <tr key={e}><td style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 12 }}>{e}</td><td></td><td style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 12, color: 'var(--accent-amber)' }}>demo123</td></tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* API Keys Guide */}
        <div className="card">
          <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 16 }}>Required API Keys</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8, fontSize: 12 }}>
            {[
              { key: 'GEMINI_API_KEY', desc: 'Enables AIRA AI chat. Get from Google AI Studio.', required: false },
              { key: 'FIREBASE_PROJECT_ID', desc: 'Enables persistent storage. Get from Firebase Console.', required: false },
              { key: 'FIREBASE_PRIVATE_KEY', desc: 'Firebase Admin SDK private key (JSON).', required: false },
              { key: 'FIREBASE_CLIENT_EMAIL', desc: 'Firebase service account email.', required: false },
            ].map(({ key, desc, required }) => (
              <div key={key} style={{ padding: 10, background: 'var(--bg-secondary)', borderRadius: 8 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 3 }}>
                  <code style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 11, color: 'var(--accent-cyan)' }}>{key}</code>
                  {!required && <span className="badge badge-simulated">OPTIONAL</span>}
                </div>
                <div style={{ color: 'var(--text-secondary)' }}>{desc}</div>
              </div>
            ))}
          </div>
          <div style={{ marginTop: 12, padding: 10, background: 'rgba(0,212,255,0.05)', borderRadius: 8, fontSize: 11, color: 'var(--text-secondary)' }}>
            Copy <code style={{ color: 'var(--accent-cyan)' }}>.env.example</code> to <code style={{ color: 'var(--accent-cyan)' }}>backend/.env</code> and fill in your keys.
          </div>
        </div>
      </div>
    </div>
  );
}
