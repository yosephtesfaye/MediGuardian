import { useEffect, useState } from 'react';
import { api, type DashboardData } from './api/client';
import { AdherenceHeatmap } from './components/AdherenceHeatmap';
import { ChatPanel } from './components/ChatPanel';
import { Header } from './components/Header';
import { OCRUpload } from './components/OCRUpload';
import { ToastProvider, useToast } from './components/Toast';

function Dashboard() {
  const [userId, setUserId] = useState(1);
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const { show } = useToast();

  const load = async () => {
    setLoading(true);
    try {
      setData(await api.dashboard(userId));
    } catch {
      show('Failed to load dashboard', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [userId]);

  const logDose = async (medId: number, status: string) => {
    try {
      await api.logAdherence(userId, medId, status);
      show(`Logged as ${status}`, 'success');
      load();
    } catch {
      show('Failed to log dose', 'error');
    }
  };

  return (
    <div className="min-h-screen">
      <Header userId={userId} onUserIdChange={setUserId} />

      <main className="max-w-7xl mx-auto px-4 py-6 space-y-6">
        {loading && !data ? (
          <div className="text-center py-20 text-slate-400">Loading dashboard...</div>
        ) : data ? (
          <>
            {/* Stats row */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {[
                { label: 'Medications', value: data.medications_count, icon: '💊' },
                { label: 'Adherence', value: `${data.adherence.adherence_rate}%`, icon: '📊' },
                { label: "Today's Reminders", value: data.today_reminders.length, icon: '⏰' },
                { label: 'Caregivers', value: data.caregivers.length, icon: '👨‍👩‍👧' },
              ].map((s) => (
                <div key={s.label} className="card text-center">
                  <div className="text-2xl mb-1">{s.icon}</div>
                  <div className="text-2xl font-bold text-teal-600 dark:text-teal-400">{s.value}</div>
                  <div className="text-xs text-slate-500">{s.label}</div>
                </div>
              ))}
            </div>

            <div className="grid lg:grid-cols-3 gap-6">
              {/* Today's reminders */}
              <div className="card lg:col-span-1">
                <h2 className="text-lg font-semibold mb-3">Today&apos;s Reminders</h2>
                {data.today_reminders.length === 0 ? (
                  <p className="text-sm text-slate-500">No reminders today.</p>
                ) : (
                  <ul className="space-y-2">
                    {data.today_reminders.map((r) => (
                      <li key={r.id} className="flex items-center justify-between p-2 rounded-xl bg-slate-50 dark:bg-slate-800">
                        <div>
                          <div className="font-medium text-sm">{r.medication}</div>
                          <div className="text-xs text-slate-500">{r.dosage} · {r.time}</div>
                        </div>
                        <div className="flex gap-1">
                          <button onClick={() => logDose(data.medications.find(m => m.name === r.medication)?.id || 1, 'taken')} className="text-xs px-2 py-1 bg-teal-100 dark:bg-teal-900 text-teal-700 dark:text-teal-300 rounded-lg">✓</button>
                          <button onClick={() => logDose(data.medications.find(m => m.name === r.medication)?.id || 1, 'missed')} className="text-xs px-2 py-1 bg-red-100 dark:bg-red-900 text-red-700 rounded-lg">✗</button>
                        </div>
                      </li>
                    ))}
                  </ul>
                )}
              </div>

              <div className="lg:col-span-2">
                <ChatPanel userId={userId} />
              </div>
            </div>

            <div className="grid md:grid-cols-2 gap-6">
              <AdherenceHeatmap heatmap={data.heatmap} />

              <div className="card">
                <h2 className="text-lg font-semibold mb-3">Caregivers</h2>
                {data.caregivers.length === 0 ? (
                  <p className="text-sm text-slate-500">No caregivers registered.</p>
                ) : (
                  <ul className="space-y-2">
                    {data.caregivers.map((c) => (
                      <li key={c.id} className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800">
                        <div className="font-medium">{c.name}</div>
                        <div className="text-xs text-slate-500">{c.email} · Alert after {c.notify_on_miss_count} misses</div>
                      </li>
                    ))}
                  </ul>
                )}
                <div className="mt-4 flex gap-2">
                  <button onClick={() => api.exportCsv(userId)} className="btn-secondary text-sm">Export CSV</button>
                  <button onClick={() => api.exportPdf(userId)} className="btn-primary text-sm">Export PDF</button>
                </div>
              </div>
            </div>

            <OCRUpload userId={userId} />
          </>
        ) : null}
      </main>
    </div>
  );
}

export default function App() {
  return (
    <ToastProvider>
      <Dashboard />
    </ToastProvider>
  );
}
