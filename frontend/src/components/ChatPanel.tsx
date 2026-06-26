import { useState } from 'react';
import { api, speak, type ChatResponse } from '../api/client';
import { useToast } from './Toast';

interface Message {
  role: 'user' | 'assistant';
  text: string;
  agent?: string;
  traces?: ChatResponse['traces'];
}

export function ChatPanel({ userId }: { userId: number }) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const { show } = useToast();

  const send = async () => {
    if (!input.trim() || loading) return;
    const userMsg = input.trim();
    setInput('');
    setMessages((m) => [...m, { role: 'user', text: userMsg }]);
    setLoading(true);
    try {
      const res = await api.chat(userMsg, userId);
      setMessages((m) => [...m, {
        role: 'assistant',
        text: res.response,
        agent: res.agent,
        traces: res.traces,
      }]);
    } catch {
      show('Chat failed. Is the backend running?', 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card flex flex-col h-[420px]">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-lg font-semibold">💬 AI Concierge</h2>
        <button
          className="text-xs btn-secondary"
          onClick={() => speak('Hello, I am MediGuardian. How can I help with your medications today?')}
        >
          🔊 Voice
        </button>
      </div>
      <div className="flex-1 overflow-y-auto space-y-3 mb-3">
        {messages.length === 0 && (
          <p className="text-sm text-slate-500">Try: &quot;Register aspirin 100mg at 8am daily&quot;</p>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div
              className={`max-w-[85%] px-3 py-2 rounded-2xl text-sm ${
                m.role === 'user'
                  ? 'bg-teal-600 text-white'
                  : 'bg-slate-100 dark:bg-slate-800'
              }`}
            >
              {m.agent && <span className="text-xs text-teal-500 block mb-1">{m.agent}</span>}
              {m.text}
              {m.traces && m.traces.length > 0 && m.traces[0].collaboration && m.traces[0].collaboration!.length > 0 && (
                <div className="mt-2 pt-2 border-t border-slate-200 dark:border-slate-700 text-xs text-slate-500">
                  <span className="font-medium text-teal-600 dark:text-teal-400">Agent collaboration:</span>
                  {m.traces[0].collaboration!.map((c, j) => (
                    <div key={j} className="mt-1">
                      {c.from} → {c.to}: {c.action}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
        {loading && <p className="text-sm text-slate-400 animate-pulse">Agent thinking...</p>}
      </div>
      <div className="flex gap-2">
        <input
          className="input flex-1"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && send()}
          placeholder="Ask MediGuardian..."
          disabled={loading}
        />
        <button onClick={send} disabled={loading} className="btn-primary">Send</button>
      </div>
    </div>
  );
}
