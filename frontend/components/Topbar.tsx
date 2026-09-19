'use client';
import { useState, useEffect } from 'react';
import { NavPage, AppState } from '@/app/page';

const PAGE_TITLES: Record<NavPage, { title: string; subtitle: string }> = {
  'dashboard':          { title: 'Command Dashboard', subtitle: 'Quantum-Enhanced Traffic Overview' },
  'live-monitor':       { title: 'Live Traffic Monitor', subtitle: 'Real-time intersection state' },
  'quantum-optimizer':  { title: 'Quantum Signal Optimizer', subtitle: 'QUBO + QAOA (Qiskit Aer) — QUANTUM SIMULATOR' },
  'emergency-corridor': { title: 'Emergency Green Corridor', subtitle: 'AI-optimized ambulance routing — SIMULATED' },
  'siren-detection':    { title: 'Siren Detection & Police Alert', subtitle: 'Audio ML + TTS dispatch — SIMULATED RADIO' },
  'pollution-monitor':  { title: 'Pollution Monitor', subtitle: 'Emission estimates per junction — ESTIMATED' },
  'simulation':         { title: 'Traffic Simulation', subtitle: 'Custom discrete-event simulator — SIMULATION' },
  'ai-assistant':       { title: 'AIRA — AI Assistant', subtitle: 'Gemini-powered with backend grounding' },
  'camera-feed':        { title: 'Camera Intelligence', subtitle: 'CV vehicle detection — SIMULATED when no camera' },
  'predictions':        { title: 'AI Traffic Predictions', subtitle: 'Forecasting +5/10/15/30 min — AI PREDICTION' },
  'alerts':             { title: 'Alerts Center', subtitle: 'Active notifications and acknowledgments' },
  'reports':            { title: 'Reports & Analytics', subtitle: 'PDF/CSV traffic reports' },
  'system-status':      { title: 'System Status', subtitle: 'Backend health, Firebase, API keys' },
  'settings':           { title: 'Settings', subtitle: 'Configuration and demo users' },
};

interface TopbarProps {
  currentPage: NavPage;
  appState: AppState;
  wsConnected: boolean;
  demoMode: boolean;
  demoLoading: boolean;
  onDemoToggle: () => void;
}

export default function Topbar({
  currentPage, appState, wsConnected,
  demoMode, demoLoading, onDemoToggle,
}: TopbarProps) {
  const { title, subtitle } = PAGE_TITLES[currentPage] || PAGE_TITLES['dashboard'];

  // Client-only clock — avoids SSR/client hydration mismatch
  const [clock, setClock] = useState('');
  useEffect(() => {
    const fmt = () => new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    setClock(fmt());
    const id = setInterval(() => setClock(fmt()), 1000);
    return () => clearInterval(id);
  }, []);

  const avgCongestion = appState.intersections.length > 0
    ? (appState.intersections.reduce((s: number, i) => s + ((i as Record<string, unknown>).congestion_score as number || 0), 0) / appState.intersections.length * 100).toFixed(0)
    : '--';

  const totalVehicles = appState.networkSummary?.total_vehicles ?? '--';

  return (
    <header className="topbar">
      {/* Left: page title */}
      <div>
        <h1 style={{ fontSize: 16, fontWeight: 700, lineHeight: 1.2 }}>{title}</h1>
        <p style={{ fontSize: 11, color: 'var(--text-secondary)', marginTop: 2 }}>{subtitle}</p>
      </div>

      {/* Right: controls */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>

        {/* Network metrics — only shown when demo is on */}
        {demoMode && (
          <div style={{
            display: 'flex', gap: 20, padding: '6px 16px',
            background: 'var(--bg-secondary)', borderRadius: 8,
            border: '1px solid var(--border-subtle)',
          }}>
            <MetricChip label="Congestion" value={`${avgCongestion}%`} color="var(--accent-cyan)" />
            <MetricChip label="Vehicles"   value={String(totalVehicles)} color="var(--accent-purple)" />
            <MetricChip label="Junctions"  value={String(appState.intersections.length)} color="var(--accent-emerald)" />
          </div>
        )}

        {/* WS status */}
        <div style={{
          display: 'flex', alignItems: 'center', gap: 6,
          padding: '6px 12px', background: 'var(--bg-secondary)',
          borderRadius: 8, border: '1px solid var(--border-subtle)',
        }}>
          <span
            className={`status-dot ${wsConnected ? 'online' : ''}`}
            style={!wsConnected ? { background: 'var(--text-muted)' } : {}}
          />
          <span style={{ fontSize: 11, fontWeight: 600, color: wsConnected ? 'var(--accent-emerald)' : 'var(--text-muted)' }}>
            {wsConnected ? 'LIVE' : 'POLLING'}
          </span>
        </div>

        {/* Clock */}
        <div style={{ fontSize: 12, color: 'var(--text-secondary)', fontFamily: 'JetBrains Mono, monospace', minWidth: 80 }}>
          {clock}
        </div>

        {/* ── Demo Data Toggle Button ── */}
        <button
          onClick={onDemoToggle}
          disabled={demoLoading}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            padding: '8px 16px',
            borderRadius: 10,
            border: `1.5px solid ${demoMode ? 'var(--accent-emerald)' : 'var(--border-subtle)'}`,
            background: demoMode
              ? 'rgba(16,185,129,0.12)'
              : 'var(--bg-secondary)',
            cursor: demoLoading ? 'wait' : 'pointer',
            transition: 'all 0.25s ease',
            fontFamily: 'inherit',
            boxShadow: demoMode ? '0 0 16px rgba(16,185,129,0.2)' : 'none',
            outline: 'none',
            flexShrink: 0,
          }}
        >
          {/* Toggle pill */}
          <div style={{
            width: 34, height: 18, borderRadius: 9,
            background: demoMode ? 'var(--accent-emerald)' : 'var(--bg-primary)',
            border: `1.5px solid ${demoMode ? 'var(--accent-emerald)' : 'rgba(255,255,255,0.15)'}`,
            position: 'relative',
            transition: 'all 0.25s ease',
            flexShrink: 0,
          }}>
            <div style={{
              position: 'absolute',
              top: 2, left: demoMode ? 16 : 2,
              width: 10, height: 10,
              borderRadius: '50%',
              background: demoMode ? '#000' : 'rgba(255,255,255,0.4)',
              transition: 'left 0.25s ease',
            }} />
          </div>

          {/* Label */}
          <span style={{
            fontSize: 12,
            fontWeight: 700,
            letterSpacing: '0.04em',
            color: demoMode ? 'var(--accent-emerald)' : 'var(--text-secondary)',
            transition: 'color 0.2s',
            whiteSpace: 'nowrap',
          }}>
            {demoLoading
              ? 'Loading...'
              : demoMode
                ? 'Demo Data  ON'
                : 'Demo Data  OFF'}
          </span>

          {/* Spinner when loading */}
          {demoLoading && (
            <span style={{ fontSize: 12, animation: 'spin 1s linear infinite', display: 'inline-block', color: 'var(--accent-cyan)' }}>
              ⟳
            </span>
          )}
        </button>
      </div>
    </header>
  );
}

function MetricChip({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 1 }}>
      <span style={{ fontSize: 14, fontWeight: 800, color }}>{value}</span>
      <span style={{ fontSize: 9, color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.06em' }}>{label}</span>
    </div>
  );
}
