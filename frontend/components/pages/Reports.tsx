'use client';
import { useState } from 'react';
import { AppState, NavPage } from '@/app/page';
import api from '@/lib/api';

interface Props { appState: AppState; updateOptimization: (o: Record<string, unknown>) => void; updateEmergency: (e: Record<string, unknown>) => void; setCurrentPage: (p: NavPage) => void; }

export default function Reports({ appState }: Props) {
  const [generating, setGenerating] = useState<string | null>(null);
  const [done, setDone] = useState<string | null>(null);

  const handleGenerate = async (format: string) => {
    setGenerating(format); setDone(null);
    try {
      const res = await api.generateReport(format);
      if (!res.ok) throw new Error('Report generation failed');
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `clearway_report.${format}`;
      a.click();
      URL.revokeObjectURL(url);
      setDone(format);
    } catch (e) {
      alert('Report error: ' + (e as Error).message);
    } finally {
      setGenerating(null);
    }
  };

  const { intersections, pollution } = appState;
  const avgCongestion = intersections.length > 0
    ? intersections.reduce((s, i) => s + ((i as Record<string, unknown>).congestion_score as number || 0), 0) / intersections.length
    : 0;
  const totalVehicles = intersections.reduce((s, i) => s + ((i as Record<string, unknown>).vehicle_count as number || 0), 0);
  const totalCO2 = (pollution as Record<string, unknown>[]).reduce((s, p) => s + ((p.co2_kg_per_hour as number) || 0), 0);

  return (
    <div className="page animate-fade-in">
      <div className="page-header">
        <div>
          <h2 className="page-title">Reports & Analytics</h2>
          <p className="page-subtitle">Generate PDF/CSV traffic reports from demo data <span className="badge badge-demo">DEMO DATA</span></p>
        </div>
      </div>

      {/* Summary preview */}
      <div className="card">
        <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 16 }}>Report Preview — Current Network State</div>
        <div className="grid-4">
          {[
            { l: 'Report Date', v: new Date().toLocaleDateString(), c: 'var(--accent-cyan)' },
            { l: 'Avg Congestion', v: `${(avgCongestion * 100).toFixed(1)}%`, c: avgCongestion > 0.7 ? 'var(--status-critical)' : 'var(--accent-amber)' },
            { l: 'Total Vehicles', v: totalVehicles.toLocaleString(), c: 'var(--accent-purple)' },
            { l: 'CO₂ (Estimated)', v: `${totalCO2.toFixed(2)} kg/hr`, c: 'var(--accent-orange)' },
          ].map(({ l, v, c }) => (
            <div key={l} style={{ padding: 14, background: 'var(--bg-secondary)', borderRadius: 10, textAlign: 'center' }}>
              <div style={{ fontWeight: 800, fontSize: 18, color: c }}>{v}</div>
              <div style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 4 }}>{l}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Junction table */}
      <div className="card">
        <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 12 }}>Junction Summary</div>
        <div className="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>Junction</th><th>Name</th><th>Congestion</th><th>Vehicles</th><th>Queue</th><th>Wait</th><th>Speed</th>
              </tr>
            </thead>
            <tbody>
              {intersections.map((inter) => {
                const i = inter as Record<string, unknown>;
                const score = (i.congestion_score as number) || 0;
                return (
                  <tr key={i.id as string}>
                    <td><strong style={{ color: 'var(--accent-cyan)', fontFamily: 'JetBrains Mono, monospace' }}>{i.label as string}</strong></td>
                    <td>{i.name as string}</td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <div className="progress-bar" style={{ width: 60, flexShrink: 0 }}>
                          <div className="progress-fill" style={{ width: `${score * 100}%`, background: score > 0.7 ? 'var(--status-critical)' : score > 0.5 ? 'var(--accent-amber)' : 'var(--accent-emerald)' }} />
                        </div>
                        <span style={{ fontWeight: 700, color: score > 0.7 ? 'var(--status-critical)' : 'var(--text-primary)' }}>{(score * 100).toFixed(0)}%</span>
                      </div>
                    </td>
                    <td>{i.vehicle_count as number}</td>
                    <td>{i.queue_length as number}</td>
                    <td>{((i.waiting_time_seconds as number) || 0).toFixed(0)}s</td>
                    <td>{((i.average_speed_kmh as number) || 0).toFixed(0)} km/h</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Export buttons */}
      <div className="grid-2">
        {[
          { format: 'pdf', label: '📄 Download PDF Report', desc: 'Full report with charts and analysis', color: 'btn-primary' },
          { format: 'csv', label: '📊 Download CSV Data', desc: 'Raw junction metrics as spreadsheet', color: 'btn-ghost' },
        ].map(({ format, label, desc, color }) => (
          <div key={format} className="card" style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
            <div style={{ flex: 1 }}>
              <div style={{ fontWeight: 700, fontSize: 14 }}>{label}</div>
              <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 4 }}>{desc}</div>
              {done === format && <div style={{ fontSize: 11, color: 'var(--accent-emerald)', marginTop: 6 }}>✓ Downloaded successfully</div>}
            </div>
            <button
              className={`btn ${color}`}
              onClick={() => handleGenerate(format)}
              disabled={generating !== null}
              style={{ minWidth: 120 }}
            >
              {generating === format ? '⟳ Generating...' : `Export ${format.toUpperCase()}`}
            </button>
          </div>
        ))}
      </div>

      <div style={{ fontSize: 11, color: 'var(--text-muted)', textAlign: 'center' }}>
        ⚠ All report data is DEMO/SIMULATED. Emissions are ESTIMATED. Quantum results are QUANTUM SIMULATOR.
      </div>
    </div>
  );
}
