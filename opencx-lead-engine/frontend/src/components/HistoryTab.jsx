const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

function HistoryTab({ history, onResend }) {
  return (
    <section className="mt-6 rounded-xl border border-slate-700 bg-slate-900/70 p-4">
      <h2 className="mb-3 text-lg font-semibold text-slate-100">History</h2>
      <div className="overflow-x-auto">
        <table className="min-w-full text-left text-xs text-slate-200">
          <thead className="bg-slate-800">
            <tr>
              <th className="px-2 py-2">date</th>
              <th className="px-2 py-2">prompt</th>
              <th className="px-2 py-2">companies</th>
              <th className="px-2 py-2">cost</th>
              <th className="px-2 py-2">actions</th>
            </tr>
          </thead>
          <tbody>
            {history.map((row) => (
              <tr key={row.job_id} className="border-b border-slate-800">
                <td className="px-2 py-2">{formatDate(row.created_at)}</td>
                <td className="px-2 py-2">{truncate(row.prompt, 80)}</td>
                <td className="px-2 py-2">{row.companies_found}</td>
                <td className="px-2 py-2">${Number(row.total_cost_usd || 0).toFixed(2)}</td>
                <td className="px-2 py-2">
                  <div className="flex gap-2">
                    <a
                      href={`${API_BASE}/download/${row.job_id}`}
                      className="rounded bg-emerald-600 px-2 py-1 text-white"
                    >
                      Download CSV
                    </a>
                    <button
                      type="button"
                      onClick={() => onResend(row.job_id)}
                      className="rounded bg-sky-600 px-2 py-1 text-white"
                    >
                      Resend webhook
                    </button>
                  </div>
                </td>
              </tr>
            ))}
            {history.length === 0 && (
              <tr>
                <td colSpan={5} className="px-2 py-3 text-slate-400">
                  No previous runs found.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function truncate(value = "", max = 80) {
  if (value.length <= max) return value;
  return `${value.slice(0, max - 3)}...`;
}

function formatDate(value) {
  if (!value) return "-";
  return new Date(value).toLocaleString();
}

export default HistoryTab;
