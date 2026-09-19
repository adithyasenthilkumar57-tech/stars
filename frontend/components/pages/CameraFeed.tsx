'use client';
import { useState, useEffect } from 'react';
import { AppState, NavPage } from '@/app/page';
import api from '@/lib/api';

interface Props { appState: AppState; updateOptimization: (o: Record<string, unknown>) => void; updateEmergency: (e: Record<string, unknown>) => void; setCurrentPage: (p: NavPage) => void; }

export default function CameraFeed({ appState }: Props) {
  const [cameras, setCameras] = useState<Record<string, unknown>[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [analysis, setAnalysis] = useState<Record<string, unknown> | null>(null);
  const [analyzing, setAnalyzing] = useState(false);

  useEffect(() => {
    api.getCameras().then(d => setCameras(d.cameras || [])).catch(() => {});
  }, []);

  const handleAnalyze = async (cameraId: string) => {
    setSelected(cameraId);
    setAnalyzing(true); setAnalysis(null);
    try {
      const r = await api.analyzeCamera(cameraId);
      setAnalysis(r);
    } finally {
      setAnalyzing(false);
    }
  };

  return (
    <div className="page animate-fade-in">
      <div className="page-header">
        <div>
          <h2 className="page-title">Camera Intelligence</h2>
          <p className="page-subtitle">
            OpenCV motion detection + vehicle classification — real frames when connected, simulated when not
            <span className="badge badge-simulated" style={{ marginLeft: 6 }}>SIMULATED WHEN NO CAMERA</span>
          </p>
        </div>
      </div>

      <div className="grid-2">
        {/* Camera list */}
        <div className="card">
          <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 12 }}>Cameras ({cameras.length})</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            {cameras.slice(0, 12).map((cam) => {
              const c = cam as Record<string, unknown>;
              return (
                <div key={c.id as string}
                  style={{
                    display: 'flex', alignItems: 'center', gap: 10,
                    padding: 10, background: selected === c.id ? 'rgba(0,212,255,0.05)' : 'var(--bg-secondary)',
                    borderRadius: 8, cursor: 'pointer',
                    border: `1px solid ${selected === c.id ? 'rgba(0,212,255,0.3)' : 'transparent'}`,
                    transition: 'all 0.15s',
                  }}
                  onClick={() => handleAnalyze(c.id as string)}>
                  <div style={{ fontSize: 20 }}>📷</div>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontWeight: 600, fontSize: 13 }}>{c.label as string}</div>
                    <div style={{ fontSize: 11, color: 'var(--text-secondary)' }}>
                      {c.intersection_name as string} — {c.direction as string}
                    </div>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{
                      width: 8, height: 8, borderRadius: '50%', marginLeft: 'auto',
                      background: c.is_online ? 'var(--accent-emerald)' : 'var(--status-critical)',
                      boxShadow: c.is_online ? '0 0 6px var(--accent-emerald)' : 'none',
                    }} />
                    <div style={{ fontSize: 9, color: 'var(--text-muted)', marginTop: 2 }}>
                      {c.is_online ? 'ONLINE' : 'OFFLINE'}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Analysis result */}
        <div>
          {selected && (
            <div className="card">
              {analyzing ? (
                <div style={{ textAlign: 'center', padding: 40 }}>
                  <div style={{ fontSize: 40, animation: 'spin 1.5s linear infinite', marginBottom: 16 }}>📷</div>
                  <div style={{ fontWeight: 700 }}>Analyzing camera feed...</div>
                  <div style={{ color: 'var(--text-secondary)', fontSize: 12, marginTop: 6 }}>Running OpenCV motion detection + vehicle classification</div>
                  <span className="badge badge-simulated" style={{ marginTop: 10, display: 'inline-block' }}>SIMULATED</span>
                </div>
              ) : analysis ? (
                <CameraAnalysis analysis={analysis} />
              ) : null}
            </div>
          )}
          {!selected && (
            <div className="card" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: 300, color: 'var(--text-muted)', flexDirection: 'column', gap: 12 }}>
              <span style={{ fontSize: 48 }}>📷</span>
              <span>Click a camera to analyze its feed</span>
              <span className="badge badge-simulated">SIMULATED WHEN NO CAMERA CONNECTED</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function CameraAnalysis({ analysis }: { analysis: Record<string, unknown> }) {
  const a = (analysis.analysis || analysis) as Record<string, unknown>;
  const vehicles = (a.detected_vehicles as Record<string, unknown>[]) || [];
  return (
    <div className="animate-fade-in">
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
        <span style={{ fontWeight: 700, fontSize: 15 }}>Analysis Result</span>
        <span className="data-label data-label-simulated">{a.data_source as string || 'SIMULATED'}</span>
      </div>

      {/* Simulated camera view */}
      <div style={{ width: '100%', height: 200, background: 'radial-gradient(ellipse at 30% 40%, rgba(0,212,255,0.06) 0%, transparent 60%), var(--bg-secondary)', borderRadius: 10, marginBottom: 16, display: 'flex', alignItems: 'center', justifyContent: 'center', position: 'relative', border: '1px solid var(--border-subtle)', overflow: 'hidden' }}>
        {vehicles.map((v, i) => {
          const x = v.x as number || (20 + i * 15);
          const y = v.y as number || (40 + i * 10);
          return (
            <div key={i} style={{ position: 'absolute', left: `${x}%`, top: `${y}%`, width: (v.width as number) || 40, height: (v.height as number) || 20, border: '2px solid var(--accent-cyan)', borderRadius: 3, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 9, color: 'var(--accent-cyan)', background: 'rgba(0,212,255,0.08)' }}>
              {v.class as string}
            </div>
          );
        })}
        <div style={{ position: 'absolute', top: 8, right: 8, fontSize: 10, color: 'var(--accent-cyan)', fontFamily: 'JetBrains Mono, monospace' }}>SIMULATED FEED</div>
        {vehicles.length === 0 && <span style={{ color: 'var(--text-muted)', fontSize: 13 }}>No vehicles detected</span>}
      </div>

      <div className="grid-2" style={{ marginBottom: 12 }}>
        {[
          { l: 'Vehicles Detected', v: String(a.vehicle_count ?? vehicles.length ?? 0) },
          { l: 'Congestion Score', v: `${((a.congestion_score as number || 0) * 100).toFixed(0)}%` },
          { l: 'Emergency Detected', v: a.emergency_vehicle_detected ? '🚨 YES' : 'No' },
          { l: 'Plate Recognized', v: a.plate_detected ? (a.plate_text as string) : 'No' },
        ].map(({ l, v }) => (
          <div key={l} style={{ padding: 10, background: 'var(--bg-secondary)', borderRadius: 8 }}>
            <div style={{ fontWeight: 700, color: 'var(--accent-cyan)' }}>{v}</div>
            <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>{l}</div>
          </div>
        ))}
      </div>

      {a.ai_insight && (
        <div style={{ padding: 10, background: 'rgba(16,185,129,0.08)', borderRadius: 8, fontSize: 12, color: 'var(--text-secondary)' }}>
          💡 {a.ai_insight as string}
        </div>
      )}
    </div>
  );
}
