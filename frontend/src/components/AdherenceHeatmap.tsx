import type { DashboardData } from '../api/client';

export function AdherenceHeatmap({ heatmap }: { heatmap: DashboardData['heatmap'] }) {
  const maxTaken = Math.max(...heatmap.map((d) => d.taken || 0), 1);

  return (
    <div className="card">
      <h2 className="text-lg font-semibold mb-4">Adherence Calendar</h2>
      {heatmap.length === 0 ? (
        <p className="text-slate-500 text-sm">No adherence data yet. Log your first dose!</p>
      ) : (
        <div className="grid grid-cols-7 gap-1">
          {heatmap.slice(-28).map((day) => {
            const intensity = (day.taken || 0) / maxTaken;
            return (
              <div key={day.date} className="text-center" title={`${day.date}: ${day.taken} taken`}>
                <div
                  className="w-full aspect-square rounded-md"
                  style={{
                    backgroundColor: `rgba(13, 148, 136, ${0.15 + intensity * 0.85})`,
                  }}
                />
                <span className="text-[10px] text-slate-400">{day.date.slice(8)}</span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
