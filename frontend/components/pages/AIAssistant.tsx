'use client';
import { useState, useRef, useEffect } from 'react';
import { AppState, NavPage } from '@/app/page';
import api from '@/lib/api';

interface Props { appState: AppState; updateOptimization: (o: Record<string, unknown>) => void; updateEmergency: (e: Record<string, unknown>) => void; setCurrentPage: (p: NavPage) => void; }

interface Message { role: 'user' | 'ai'; text: string; source?: string; timestamp: string; isTyping?: boolean; }

const SUGGESTIONS = [
  'What is the current network congestion level?',
  'Which junction has the worst queue right now?',
  'Explain how the quantum optimizer works',
  'What are the estimated CO₂ emissions?',
  'Is there any active emergency?',
  'What should I do about high congestion at J3?',
  'Summarize the network status',
];

export default function AIAssistant({ appState }: Props) {
  const [messages, setMessages] = useState<Message[]>([{
    role: 'ai',
    text: "I'm **AIRA** — the ClearWay AI Real-time Assistant. I have full access to your backend traffic data: junction states, optimization results, emergency status, siren detections, and pollution estimates. How can I help you optimize the network today?",
    source: 'AIRA — AI Assistant (Gemini-powered with fallback)',
    timestamp: new Date().toISOString(),
  }]);
  const [input, setInput] = useState('');
  const [thinking, setThinking] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const send = async (text: string) => {
    if (!text.trim() || thinking) return;
    const userMsg: Message = { role: 'user', text, timestamp: new Date().toISOString() };
    setMessages(prev => [...prev, userMsg, { role: 'ai', text: '', source: '', timestamp: new Date().toISOString(), isTyping: true }]);
    setInput('');
    setThinking(true);

    try {
      const r = await api.chat(text, { latest_optimization: appState.latestOptimization });
      const aiMsg: Message = {
        role: 'ai',
        text: r.response || r.text || 'No response from AI.',
        source: r.source || 'AIRA',
        timestamp: new Date().toISOString(),
      };
      setMessages(prev => [...prev.slice(0, -1), aiMsg]);
    } catch {
      setMessages(prev => [...prev.slice(0, -1), {
        role: 'ai',
        text: '⚠ AI service unavailable. Check that the backend is running and GEMINI_API_KEY is configured.',
        source: 'Fallback',
        timestamp: new Date().toISOString(),
      }]);
    } finally {
      setThinking(false);
    }
  };

  return (
    <div className="page animate-fade-in" style={{ height: 'calc(100vh - 64px)', paddingBottom: 0 }}>
      <div style={{ display: 'flex', flexDirection: 'column', height: '100%', gap: 16 }}>
        {/* Header */}
        <div className="page-header" style={{ paddingBottom: 0, flexShrink: 0 }}>
          <div>
            <h2 className="page-title">AIRA — AI Real-time Assistant</h2>
            <p className="page-subtitle">
              Gemini-powered with full backend data grounding — real intersection states, not generic answers
              <span className="badge badge-cyan" style={{ marginLeft: 6 }}>AI PREDICTION</span>
            </p>
          </div>
          <div style={{ padding: '8px 14px', background: 'var(--bg-secondary)', borderRadius: 8, border: '1px solid var(--border-subtle)', fontSize: 12 }}>
            <span style={{ color: 'var(--text-secondary)' }}>Junctions in context: </span>
            <strong style={{ color: 'var(--accent-cyan)' }}>{appState.intersections.length}</strong>
          </div>
        </div>

        {/* Suggestions */}
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', flexShrink: 0 }}>
          {SUGGESTIONS.map(s => (
            <button key={s} className="btn btn-ghost" style={{ fontSize: 11, padding: '5px 10px' }} onClick={() => send(s)}>
              {s}
            </button>
          ))}
        </div>

        {/* Chat area */}
        <div style={{ flex: 1, overflow: 'auto', display: 'flex', flexDirection: 'column', gap: 12, paddingRight: 4 }}>
          {messages.map((msg, i) => (
            <div key={i} style={{ display: 'flex', flexDirection: 'column', alignItems: msg.role === 'user' ? 'flex-end' : 'flex-start', gap: 4 }}>
              {msg.role === 'ai' && (
                <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <div style={{ width: 24, height: 24, borderRadius: '50%', background: 'var(--quantum-gradient)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 12, fontWeight: 900, color: '#000' }}>A</div>
                  <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>AIRA</span>
                  {msg.source && <span className="data-label data-label-ai">{msg.source}</span>}
                </div>
              )}
              <div className={msg.role === 'user' ? 'chat-bubble-user' : 'chat-bubble-ai'}>
                {msg.isTyping ? (
                  <div style={{ display: 'flex', gap: 4, alignItems: 'center' }}>
                    {[0, 1, 2].map(d => (
                      <div key={d} style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--accent-cyan)', animation: `spin 1s ${d * 0.2}s ease-in-out infinite` }} />
                    ))}
                    <span style={{ fontSize: 11, color: 'var(--text-secondary)', marginLeft: 4 }}>Thinking...</span>
                  </div>
                ) : (
                  <div style={{ whiteSpace: 'pre-wrap', lineHeight: 1.7 }} dangerouslySetInnerHTML={{ __html: msg.text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>').replace(/\n/g, '<br/>') }} />
                )}
              </div>
              <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>
                {new Date(msg.timestamp).toLocaleTimeString()}
              </span>
            </div>
          ))}
          <div ref={bottomRef} />
        </div>

        {/* Input */}
        <div style={{ display: 'flex', gap: 8, padding: '16px 0', flexShrink: 0, borderTop: '1px solid var(--border-subtle)' }}>
          <input
            className="input"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && !e.shiftKey && send(input)}
            placeholder="Ask AIRA about traffic, optimization, emissions, emergency status..."
            disabled={thinking}
          />
          <button className="btn btn-primary" onClick={() => send(input)} disabled={thinking || !input.trim()} style={{ minWidth: 80 }}>
            {thinking ? '⟳' : '→'}
          </button>
        </div>
      </div>
    </div>
  );
}
