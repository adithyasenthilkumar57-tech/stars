'use client';
import { useState, useEffect, useCallback } from 'react';
import api from '@/lib/api';
import { useWebSocket } from '@/lib/useWebSocket';
import Sidebar from '@/components/Sidebar';
import Topbar from '@/components/Topbar';
import Dashboard from '@/components/pages/Dashboard';
import LiveMonitor from '@/components/pages/LiveMonitor';
import QuantumOptimizer from '@/components/pages/QuantumOptimizer';
import EmergencyCorridor from '@/components/pages/EmergencyCorridor';
import SirenDetection from '@/components/pages/SirenDetection';
import PollutionMonitor from '@/components/pages/PollutionMonitor';
import Simulation from '@/components/pages/Simulation';
import AIAssistant from '@/components/pages/AIAssistant';
import CameraFeed from '@/components/pages/CameraFeed';
import Predictions from '@/components/pages/Predictions';
import AlertsCenter from '@/components/pages/AlertsCenter';
import Reports from '@/components/pages/Reports';
import SystemStatus from '@/components/pages/SystemStatus';
import Settings from '@/components/pages/Settings';

export type NavPage =
  | 'dashboard' | 'live-monitor' | 'quantum-optimizer'
  | 'emergency-corridor' | 'siren-detection' | 'pollution-monitor'
  | 'simulation' | 'ai-assistant' | 'camera-feed' | 'predictions'
  | 'alerts' | 'reports' | 'system-status' | 'settings';

export interface AppState {
  intersections: Record<string, unknown>[];
  networkSummary: Record<string, unknown>;
  alerts: Record<string, unknown>[];
  emergency: Record<string, unknown>;
  sirenEvents: Record<string, unknown>[];
  latestOptimization: Record<string, unknown> | null;
  pollution: Record<string, unknown>[];
  dataMode: string;
  lastUpdated: string;
  wsConnected: boolean;
}

const EMPTY_STATE: AppState = {
  intersections: [],
  networkSummary: {},
  alerts: [],
  emergency: {},
  sirenEvents: [],
  latestOptimization: null,
  pollution: [],
  dataMode: 'LIVE',
  lastUpdated: new Date().toISOString(),
  wsConnected: false,
};

const INITIAL_STATE: AppState = { ...EMPTY_STATE };

export default function App() {
  const [currentPage, setCurrentPage] = useState<NavPage>('dashboard');
  const [appState, setAppState] = useState<AppState>(INITIAL_STATE);
  const [loading, setLoading] = useState(true);
  const [activeAlertCount, setActiveAlertCount] = useState(0);
  const [demoMode, setDemoMode] = useState(false);        // ← demo toggle
  const [demoLoading, setDemoLoading] = useState(false);  // button spinner

  // ── WebSocket real-time updates ──────────────────────────────────────────
  const onWsMessage = useCallback((data: Record<string, unknown>) => {
    if (data.type === 'traffic_update') {
      setAppState(prev => ({
        ...prev,
        intersections: (data.intersections as Record<string, unknown>[]) || prev.intersections,
        lastUpdated: data.timestamp as string,
      }));
    } else if (data.type === 'emergency_update') {
      setAppState(prev => ({ ...prev, emergency: data.status as Record<string, unknown> }));
    } else if (data.type === 'siren_alert') {
      setAppState(prev => ({
        ...prev,
        sirenEvents: data.event
          ? [data.event as Record<string, unknown>, ...prev.sirenEvents.slice(0, 49)]
          : prev.sirenEvents,
      }));
    }
  }, []);

  const { connected } = useWebSocket(onWsMessage);

  useEffect(() => {
    setAppState(prev => ({ ...prev, wsConnected: connected }));
  }, [connected]);

  // ── Initial page load (empty / no demo data) ─────────────────────────────
  useEffect(() => {
    // Just mark loading as done; start empty until user hits Demo Data
    setLoading(false);
  }, []); // eslint-disable-line

  // ── Load demo data from backend ───────────────────────────────────────────
  const loadDemoData = useCallback(async () => {
    setDemoLoading(true);
    try {
      const [traffic, emergency, sirenStatus, pollution] = await Promise.allSettled([
        api.getLiveTraffic(),
        api.getEmergencyStatus(),
        api.getSirenStatuses(),
        api.getPollutionEstimates(),
      ]);

      setAppState(prev => ({
        ...prev,
        intersections: traffic.status === 'fulfilled' ? (traffic.value.intersections || []) : [],
        networkSummary: traffic.status === 'fulfilled' ? (traffic.value.network_summary || {}) : {},
        dataMode: 'DEMO',
        emergency: emergency.status === 'fulfilled' ? emergency.value : {},
        sirenEvents: sirenStatus.status === 'fulfilled' ? (sirenStatus.value.statuses || []) : [],
        pollution: pollution.status === 'fulfilled' ? (pollution.value.estimates || []) : [],
        lastUpdated: new Date().toISOString(),
      }));

      const alertCount =
        traffic.status === 'fulfilled' && traffic.value.intersections
          ? traffic.value.intersections.filter(
              (i: Record<string, unknown>) => (i.congestion_score as number) > 0.7,
            ).length
          : 0;
      setActiveAlertCount(alertCount);
    } catch (e) {
      console.error('Demo data load error:', e);
    } finally {
      setDemoLoading(false);
    }
  }, []);

  // ── Clear to empty / fresh state ─────────────────────────────────────────
  const clearDemoData = useCallback(() => {
    setAppState({ ...EMPTY_STATE, wsConnected: connected, lastUpdated: new Date().toISOString() });
    setActiveAlertCount(0);
  }, [connected]);

  // ── Toggle handler ────────────────────────────────────────────────────────
  const handleDemoToggle = useCallback(async () => {
    if (!demoMode) {
      // OFF → ON: load demo data
      setDemoMode(true);
      await loadDemoData();
    } else {
      // ON → OFF: wipe everything
      setDemoMode(false);
      clearDemoData();
    }
  }, [demoMode, loadDemoData, clearDemoData]);

  // Keep demo data refreshed via polling while demo mode is active
  useEffect(() => {
    if (!demoMode) return;
    const id = setInterval(() => {
      api.getLiveTraffic().then(data => {
        setAppState(prev => ({
          ...prev,
          intersections: data.intersections || prev.intersections,
          networkSummary: data.network_summary || prev.networkSummary,
          lastUpdated: new Date().toISOString(),
        }));
      }).catch(() => {});
    }, 10000);
    return () => clearInterval(id);
  }, [demoMode]);

  // ── Update emergency / optimization from child pages ──────────────────────
  const updateOptimization = useCallback((opt: Record<string, unknown>) => {
    setAppState(prev => ({ ...prev, latestOptimization: opt }));
  }, []);

  const updateEmergency = useCallback((em: Record<string, unknown>) => {
    setAppState(prev => ({ ...prev, emergency: em }));
  }, []);

  // ── Page renderer ─────────────────────────────────────────────────────────
  const renderPage = () => {
    const props = { appState, updateOptimization, updateEmergency, setCurrentPage };
    switch (currentPage) {
      case 'dashboard':         return <Dashboard {...props} />;
      case 'live-monitor':      return <LiveMonitor {...props} />;
      case 'quantum-optimizer': return <QuantumOptimizer {...props} />;
      case 'emergency-corridor':return <EmergencyCorridor {...props} />;
      case 'siren-detection':   return <SirenDetection {...props} />;
      case 'pollution-monitor': return <PollutionMonitor {...props} />;
      case 'simulation':        return <Simulation {...props} />;
      case 'ai-assistant':      return <AIAssistant {...props} />;
      case 'camera-feed':       return <CameraFeed {...props} />;
      case 'predictions':       return <Predictions {...props} />;
      case 'alerts':            return <AlertsCenter {...props} />;
      case 'reports':           return <Reports {...props} />;
      case 'system-status':     return <SystemStatus {...props} />;
      case 'settings':          return <Settings {...props} />;
      default:                  return <Dashboard {...props} />;
    }
  };

  return (
    <div style={{ display: 'flex' }}>
      <Sidebar
        currentPage={currentPage}
        setCurrentPage={setCurrentPage}
        activeAlertCount={activeAlertCount}
        emergencyActive={!!(appState.emergency as Record<string, unknown>)?.active}
        demoMode={demoMode}
      />
      <div className="main-content">
        <Topbar
          currentPage={currentPage}
          appState={appState}
          wsConnected={connected}
          demoMode={demoMode}
          demoLoading={demoLoading}
          onDemoToggle={handleDemoToggle}
        />
        {loading ? <LoadingScreen /> : (
          demoMode ? renderPage() : <EmptyState onEnable={handleDemoToggle} loading={demoLoading} />
        )}
      </div>
    </div>
  );
}

// ── Empty / fresh state screen ────────────────────────────────────────────────
function EmptyState({ onEnable, loading }: { onEnable: () => void; loading: boolean }) {
  return (
    <div style={{
      flex: 1, display: 'flex', flexDirection: 'column',
      alignItems: 'center', justifyContent: 'center',
      gap: 28, minHeight: '80vh',
      background: 'radial-gradient(ellipse at 50% 40%, rgba(0,212,255,0.04) 0%, transparent 70%)',
    }}>
      {/* Logo */}
      <div style={{
        width: 72, height: 72,
        background: 'var(--quantum-gradient)',
        borderRadius: 20,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize: 36, fontWeight: 900, color: '#000',
        boxShadow: 'var(--quantum-glow)',
      }}>C</div>

      {/* Headline */}
      <div style={{ textAlign: 'center', maxWidth: 520 }}>
        <h1 style={{ fontSize: 28, fontWeight: 900, color: 'var(--text-primary)', marginBottom: 10 }}>
          ClearWay AI
        </h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: 14, lineHeight: 1.7, marginBottom: 6 }}>
          Quantum-Enhanced Adaptive Urban Traffic Optimization
        </p>
        <p style={{ color: 'var(--text-muted)', fontSize: 12 }}>
          No data is loaded. Connect real sensors or enable demo mode to explore the platform.
        </p>
      </div>

      {/* Feature cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12, maxWidth: 620 }}>
        {[
          { icon: '⚛', label: 'Quantum Optimizer',    desc: 'QUBO + QAOA via Qiskit Aer' },
          { icon: '🚨', label: 'Emergency Corridor',   desc: 'AI green corridor routing' },
          { icon: '🔊', label: 'Siren Detection',      desc: 'MFCC + SVC audio ML' },
          { icon: '◌',  label: 'Pollution Monitor',    desc: 'Emission factor estimates' },
          { icon: '◈',  label: 'AI Assistant (AIRA)',  desc: 'Gemini-powered chat' },
          { icon: '▶',  label: 'Simulation',           desc: 'Discrete-event simulator' },
        ].map(({ icon, label, desc }) => (
          <div key={label} style={{
            padding: '14px 16px',
            background: 'var(--bg-card)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 12,
            textAlign: 'center',
          }}>
            <div style={{ fontSize: 24, marginBottom: 6 }}>{icon}</div>
            <div style={{ fontWeight: 700, fontSize: 12, color: 'var(--text-primary)', marginBottom: 3 }}>{label}</div>
            <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{desc}</div>
          </div>
        ))}
      </div>

      {/* Enable button */}
      <button
        className="btn btn-quantum"
        onClick={onEnable}
        disabled={loading}
        style={{ padding: '12px 32px', fontSize: 15, fontWeight: 800, gap: 10, minWidth: 240, justifyContent: 'center' }}
      >
        {loading
          ? <><span style={{ animation: 'spin 1s linear infinite', display: 'inline-block' }}>⟳</span> Loading Demo Data...</>
          : <><span>⚡</span> Enable Demo Data</>}
      </button>

      <p style={{ fontSize: 11, color: 'var(--text-muted)', textAlign: 'center' }}>
        Demo data is synthetic — Tiruppur, Tamil Nadu urban network (6 junctions).<br />
        All values are labeled SIMULATED / ESTIMATED / AI PREDICTION.
      </p>
    </div>
  );
}

function LoadingScreen() {
  return (
    <div style={{
      flex: 1, display: 'flex', flexDirection: 'column',
      alignItems: 'center', justifyContent: 'center',
      gap: 24, minHeight: '80vh',
    }}>
      <div style={{
        width: 64, height: 64,
        background: 'var(--quantum-gradient)',
        borderRadius: 18,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize: 32, fontWeight: 900, color: '#000',
        animation: 'quantumPulse 1.5s ease-in-out infinite',
      }}>C</div>
      <div style={{ textAlign: 'center' }}>
        <div style={{ fontSize: 20, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 8 }}>
          ClearWay AI
        </div>
        <div style={{ color: 'var(--text-secondary)', fontSize: 13 }}>
          Initializing backend services...
        </div>
      </div>
    </div>
  );
}
