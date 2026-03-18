function LogStream({ logs }) {
  return (
    <section className="rounded-xl border border-slate-700 bg-slate-900/70 p-4">
      <h2 className="mb-3 text-lg font-semibold text-slate-100">Live logs</h2>
      <div className="max-h-[560px] space-y-2 overflow-auto rounded border border-slate-800 bg-slate-950 p-3 text-xs">
        {logs.length === 0 && <p className="text-slate-400">No logs yet.</p>}
        {logs.map((log, idx) => (
          <p key={`${log.ts}-${idx}`} className={lineClass(log.level)}>
            [{log.ts}] {log.message}
          </p>
        ))}
      </div>
    </section>
  );
}

function lineClass(level) {
  if (level === "green") return "text-green-400";
  if (level === "yellow") return "text-yellow-300";
  if (level === "red") return "text-red-400";
  if (level === "blue") return "text-sky-400";
  return "text-slate-300";
}

export default LogStream;
