'use client';
import { NavPage } from '@/app/page';

const NAV_STRUCTURE = [
  {
    section: 'Overview',
    items: [
      { id: 'dashboard', label: 'Dashboard', icon: '⬡', description: 'Network overview' },
      { id: 'live-monitor', label: 'Live Monitor', icon: '◉', description: 'Real-time traffic' },
    ],
  },
  {
    section: 'Intelligence',
    items: [
      { id: 'quantum-optimizer', label: 'Quantum Optimizer', icon: '⚛', description: 'QUBO + QAOA', badge: 'QUANTUM' },
      { id: 'ai-assistant', label: 'AI Assistant', icon: '◈', description: 'AIRA chatbot' },
      { id: 'predictions', label: 'Predictions', icon: '◻', description: 'Forecasting' },
    ],
  },
  {
    section: 'Safety',
    items: [
      { id: 'emergency-corridor', label: 'Emergency Corridor', icon: '🚨', description: 'Green corridor FSM', badge: 'EMERGENCY' },
      { id: 'siren-detection', label: 'Siren Detection', icon: '🔊', description: 'Audio ML + dispatch' },
      { id: 'camera-feed', label: 'Camera Feed', icon: '📷', description: 'CV detection' },
    ],
  },
  {
    section: 'Analytics',
    items: [
      { id: 'pollution-monitor', label: 'Pollution Monitor', icon: '◌', description: 'Emission estimates' },
      { id: 'simulation', label: 'Simulation', icon: '▶', description: 'Traffic scenarios' },
      { id: 'alerts', label: 'Alerts Center', icon: '◇', description: 'Notifications' },
    ],
  },
  {
    section: 'Management',
    items: [
      { id: 'reports', label: 'Reports', icon: '◫', description: 'PDF/CSV exports' },
      { id: 'system-status', label: 'System Status', icon: '◍', description: 'Health & config' },
      { id: 'settings', label: 'Settings', icon: '⚙', description: 'Configuration' },
    ],
  },
];

interface SidebarProps {
  currentPage: NavPage;
  setCurrentPage: (p: NavPage) => void;
  activeAlertCount: number;
  emergencyActive: boolean;
  demoMode: boolean;
}

export default function Sidebar({ currentPage, setCurrentPage, activeAlertCount, emergencyActive, demoMode }: SidebarProps) {
  return (
    <aside className="sidebar">
      {/* Logo */}
      <div className="sidebar-logo">
        <div className="sidebar-logo-icon">C</div>
        <div>
          <div style={{ fontWeight: 800, fontSize: 14, lineHeight: 1.2 }}>ClearWay AI</div>
          <div style={{ fontSize: 9, color: 'var(--text-muted)', letterSpacing: '0.08em', textTransform: 'uppercase' }}>
            Quantum Traffic
          </div>
        </div>
      </div>

      {/* System mode indicator */}
      <div style={{ padding: '8px 16px', borderBottom: '1px solid var(--border-subtle)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <span
            className={`status-dot ${demoMode ? 'online' : ''}`}
            style={!demoMode ? { background: 'var(--text-muted)' } : {}}
          />
          <span style={{ fontSize: 11, fontWeight: 600, color: demoMode ? 'var(--accent-emerald)' : 'var(--text-secondary)' }}>
            {demoMode ? 'DEMO MODE' : 'LIVE MODE'}
          </span>
          <span style={{
            marginLeft: 'auto', fontSize: 9, fontWeight: 700,
            color: demoMode ? 'var(--accent-amber)' : 'var(--text-muted)',
          }}>
            {demoMode ? 'SIMULATED' : 'NO DATA'}
          </span>
        </div>
      </div>

      {/* Emergency banner */}
      {emergencyActive && (
        <div style={{
          margin: '8px',
          padding: '8px 12px',
          background: 'rgba(244,63,94,0.15)',
          border: '1px solid rgba(244,63,94,0.4)',
          borderRadius: 8,
          display: 'flex',
          alignItems: 'center',
          gap: 8,
          cursor: 'pointer',
          animation: 'sirenPulse 1s ease-in-out infinite',
        }}
        onClick={() => setCurrentPage('emergency-corridor')}
        >
          <span>🚨</span>
          <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--status-critical)' }}>CORRIDOR ACTIVE</span>
        </div>
      )}

      {/* Navigation */}
      <nav className="sidebar-nav">
        {NAV_STRUCTURE.map(({ section, items }) => (
          <div key={section} className="nav-section">
            <div className="nav-section-label">{section}</div>
            {items.map(item => {
              const isActive = currentPage === item.id;
              const hasBadge = item.id === 'alerts' && activeAlertCount > 0;
              return (
                <button
                  key={item.id}
                  className={`nav-item ${isActive ? 'active' : ''}`}
                  onClick={() => setCurrentPage(item.id as NavPage)}
                  title={item.description}
                >
                  <span className="nav-icon" style={{ fontSize: 14 }}>{item.icon}</span>
                  <span style={{ flex: 1, textAlign: 'left' }}>{item.label}</span>
                  {hasBadge && (
                    <span style={{
                      background: 'var(--status-critical)',
                      color: '#fff',
                      fontSize: 10, fontWeight: 700,
                      padding: '1px 6px', borderRadius: 10,
                      minWidth: 18, textAlign: 'center',
                    }}>{activeAlertCount}</span>
                  )}
                  {item.badge === 'QUANTUM' && (
                    <span className="badge badge-cyan" style={{ fontSize: 8, padding: '1px 5px' }}>Q</span>
                  )}
                  {item.badge === 'EMERGENCY' && emergencyActive && (
                    <span style={{ width: 8, height: 8, background: 'var(--status-critical)', borderRadius: '50%', animation: 'pulse-red 1s infinite' }}></span>
                  )}
                </button>
              );
            })}
          </div>
        ))}
      </nav>

      {/* Footer */}
      <div style={{
        padding: '12px 16px',
        borderTop: '1px solid var(--border-subtle)',
        fontSize: 10,
        color: 'var(--text-muted)',
        lineHeight: 1.5,
      }}>
        <div>⚠ All quantum results: SIMULATOR</div>
        <div>⚠ All emissions: ESTIMATED</div>
        <div>⚠ All audio alerts: SIMULATED</div>
      </div>
    </aside>
  );
}
