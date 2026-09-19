'use client';
import { useState } from 'react';
import { AppState, NavPage } from '@/app/page';
import api from '@/lib/api';

interface Props { appState: AppState; updateOptimization: (o: Record<string, unknown>) => void; updateEmergency: (e: Record<string, unknown>) => void; setCurrentPage: (p: NavPage) => void; }

const METHODS = [
  {
    id: 'classical_fixed', label: 'Classical Fixed Timing', icon: '■',
    desc: 'Fixed 45s/35s NS/EW — no adaptation. Represents pre-AI baseline.',
    color: 'var(--text-muted)', badge: 'BASELINE',
  },
  {
    id: 'classical_adaptive', label: 'Rule-Based Adaptive', icon: '◈',
    desc: 'Greedy queue-weighted signal adjustment. No quantum computation.',
    color: 'var(--accent-blue)', badge: 'CLASSICAL',
  },
  {
    id: 'hybrid_quantum', label: 'Hybrid Quantum-Classical (QAOA)', icon: '⚛',
    desc: 'QUBO formulation + QAOA via Qiskit Aer simulator. Always QUANTUM SIMULATOR — never real hardware.',
    color: 'var(--accent-cyan)', badge: 'QUANTUM SIMULATOR',
  },
];

export default function QuantumOptimizer({ appState, updateOptimization }: Props) {
  const [selectedMethod, setSelectedMethod] = useState('hybrid_quantum');
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState('');

  const handleRun = async () => {
    setRunning(true);
    setError('');
    try {
      const r = await api.runOptimization(selectedMethod);
      setResult(r);
      updateOptimization(r);
    } catch (e: unknown) {
      setError((e as Error).message || 'Optimization failed');
    } finally {
      setRunning(false);
    }
  };

  const improvement = result ? (result.improvement_pct as number) : null;

  return (
    <div className="page animate-fade-in">
      <div className="page-header">
        <div>
          <h2 className="page-title">Quantum Signal Optimizer</h2>
          <p className="page-subtitle">
            QUBO formulation + QAOA via Qiskit Aer — always labeled
            <span className="badge badge-quantum" style={{ marginLeft: 6 }}>QUANTUM SIMULATOR</span>
            <span className="badge badge-simulated" style={{ marginLeft: 4 }}>NOT REAL HARDWARE</span>
          </p>
        </div>
        <button
          className="btn btn-quantum"
          onClick={handleRun}
          disabled={running}
          style={{ minWidth: 200, justifyContent: 'center' }}
        >
          <span style={{ fontSize: 16 }}>{running ? '⟳' : '⚛'}</span>
          {running ? 'Running Quantum Optimization...' : 'Run Optimization'}
        </button>
      </div>

      {/* Method selector */}
      <div className="grid-3">
        {METHODS.map(m => (
          <div
            key={m.id}
            className={`card ${selectedMethod === m.id ? 'quantum-panel' : ''}`}
            style={{
              cursor: 'pointer',
              borderColor: selectedMethod === m.id ? m.color : 'var(--border-subtle)',
              transition: 'all 0.2s',
            }}
            onClick={() => setSelectedMethod(m.id)}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10 }}>
              <span style={{ fontSize: 22, color: m.color }}>{m.icon}</span>
              <div>
                <div style={{ fontWeight: 700, fontSize: 13 }}>{m.label}</div>
                <span className={`badge ${selectedMethod === m.id ? 'badge-cyan' : 'badge-simulated'}`}>{m.badge}</span>
              </div>
              {selectedMethod === m.id && (
                <div style={{ marginLeft: 'auto', width: 20, height: 20, borderRadius: '50%', background: m.color, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 10, color: '#000', fontWeight: 900 }}>✓</div>
              )}
            </div>
            <p style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.5 }}>{m.desc}</p>
          </div>
        ))}
      </div>

      {/* QUBO explanation */}
      <div className="quantum-panel" style={{ padding: 20 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
          <span style={{ fontSize: 20 }}>⚛</span>
          <div style={{ fontWeight: 700, fontSize: 14 }}>QUBO Model — How It Works</div>
          <span className="badge badge-quantum">QUANTUM SIMULATOR</span>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16 }}>
          {[
            {
              step: '1', title: 'QUBO Formulation', color: 'var(--accent-cyan)',
              body: 'Binary variable x[j][p] = 1 if junction j, phase p is active. Cost function minimizes queue-weighted delay with λ=10 penalty for constraint violations.',
            },
            {
              step: '2', title: 'QAOA Circuit', color: 'var(--accent-purple)',
              body: 'Ising Hamiltonian from QUBO. QAOA ansatz with p=2 layers. COBYLA optimizer runs 50 iterations on Qiskit Aer statevector simulator.',
            },
            {
              step: '3', title: 'Signal Plans', color: 'var(--accent-emerald)',
              body: 'Binary assignments decoded to concrete NS/EW green seconds per junction. Applied to live signal state. Improvement measured vs fixed baseline.',
            },
          ].map(({ step, title, color, body }) => (
            <div key={step} style={{ padding: 16, background: 'rgba(0,0,0,0.2)', borderRadius: 10 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                <div style={{ width: 24, height: 24, borderRadius: '50%', background: color, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 12, fontWeight: 900, color: '#000' }}>{step}</div>
                <strong style={{ color }}>{title}</strong>
              </div>
              <p style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.6 }}>{body}</p>
            </div>
          ))}
        </div>
      </div>

      {error && <div className="alert-banner high">{error}</div>}

      {/* Loading animation */}
      {running && (
        <div className="quantum-panel" style={{ padding: 32, textAlign: 'center' }}>
          <div style={{ fontSize: 48, animation: 'spin 2s linear infinite', display: 'inline-block', marginBottom: 16 }}>⚛</div>
          <div style={{ fontWeight: 700, fontSize: 16, marginBottom: 8 }}>Running Quantum Optimization</div>
          <div style={{ color: 'var(--text-secondary)', fontSize: 13 }}>Building QUBO → Constructing Ising Hamiltonian → Running QAOA (Qiskit Aer) → Decoding signal plans...</div>
          <span className="badge badge-quantum" style={{ marginTop: 12, display: 'inline-block' }}>QUANTUM SIMULATOR — NOT REAL HARDWARE</span>
        </div>
      )}

      {/* Result */}
      {result && !running && (
        <div className="card animate-fade-in">
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 20 }}>
            <span style={{ fontSize: 20, color: 'var(--accent-emerald)' }}>✓</span>
            <div>
              <div style={{ fontWeight: 800, fontSize: 16, color: 'var(--accent-emerald)' }}>
                Optimization Complete — {improvement?.toFixed(1)}% improvement
              </div>
              <div style={{ fontSize: 11, color: 'var(--text-secondary)' }}>
                {result.simulator_status as string} • {(result.execution_time_ms as number)?.toFixed(0)}ms • {result.iteration_count as number} iterations
                <span className="badge badge-quantum" style={{ marginLeft: 8 }}>QUANTUM SIMULATION</span>
              </div>
            </div>
          </div>

          {/* KPI row */}
          <div className="grid-4" style={{ marginBottom: 20 }}>
            {[
              { label: 'Cost Before', value: (result.cost_before as number)?.toFixed(1), color: 'var(--status-critical)' },
              { label: 'Cost After', value: (result.cost_after as number)?.toFixed(1), color: 'var(--accent-emerald)' },
              { label: 'Improvement', value: `${improvement?.toFixed(1)}%`, color: 'var(--accent-emerald)' },
              { label: 'Wait Before → After', value: `${(result.avg_waiting_before as number)?.toFixed(0)}s → ${(result.avg_waiting_after as number)?.toFixed(0)}s`, color: 'var(--accent-cyan)' },
            ].map(({ label, value, color }) => (
              <div key={label} style={{ padding: 16, background: 'var(--bg-secondary)', borderRadius: 10, textAlign: 'center' }}>
                <div style={{ fontSize: 20, fontWeight: 900, color }}>{value}</div>
                <div style={{ fontSize: 10, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', marginTop: 4 }}>{label}</div>
              </div>
            ))}
          </div>

          {/* Signal plans */}
          {(result.signal_plans as Record<string, unknown>[])?.length > 0 && (
            <div>
              <div style={{ fontWeight: 700, fontSize: 13, marginBottom: 12 }}>Optimized Signal Plans</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {(result.signal_plans as Record<string, unknown>[]).map((plan) => (
                  <div key={plan.junction_id as string} style={{ padding: 12, background: 'var(--bg-secondary)', borderRadius: 8 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6 }}>
                      <strong style={{ color: 'var(--accent-cyan)', fontFamily: 'JetBrains Mono, monospace' }}>{plan.junction_label as string}</strong>
                      <div style={{ display: 'flex', gap: 8, fontSize: 12 }}>
                        <span style={{ color: 'var(--accent-emerald)' }}>NS: {plan.ns_green_seconds as number}s</span>
                        <span>•</span>
                        <span style={{ color: 'var(--accent-blue)' }}>EW: {plan.ew_green_seconds as number}s</span>
                      </div>
                    </div>
                    <p style={{ fontSize: 11, color: 'var(--text-secondary)' }}>{plan.rationale as string}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
