import { useTheme } from '../hooks/useTheme';

interface Props {
  userId: number;
  onUserIdChange: (id: number) => void;
}

export function Header({ userId, onUserIdChange }: Props) {
  const { dark, toggle } = useTheme();

  return (
    <header className="sticky top-0 z-40 bg-white/80 dark:bg-slate-950/80 backdrop-blur border-b border-slate-200 dark:border-slate-800">
      <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-teal-600 flex items-center justify-center text-white font-bold text-lg">
            M
          </div>
          <div>
            <h1 className="text-xl font-bold text-teal-700 dark:text-teal-400">MediGuardian AI</h1>
            <p className="text-xs text-slate-500">Multi-Agent Medication Management</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <label className="text-sm text-slate-500 hidden sm:block">User ID</label>
          <input
            type="number"
            min={1}
            value={userId}
            onChange={(e) => onUserIdChange(Number(e.target.value))}
            className="input w-20 text-center"
          />
          <button onClick={toggle} className="btn-secondary" aria-label="Toggle theme">
            {dark ? '☀️' : '🌙'}
          </button>
        </div>
      </div>
    </header>
  );
}
