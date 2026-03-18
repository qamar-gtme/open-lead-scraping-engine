function CostBar({
  estimate,
  status,
  statusPayload,
  totalCosts,
  resultsPayload,
  onRun,
  runDisabled,
}) {
  const running = !["completed", "failed", "cancelled", "cancel_requested", ""].includes(status);
  const spent = statusPayload?.costs?.total ?? 0;
  const estimated = estimate?.total_estimated_usd ?? 0;
  const pct = estimated > 0 ? Math.min(100, Math.round((spent / estimated) * 100)) : 0;
  const companies = resultsPayload?.results?.length ?? 0;
  const runCost = resultsPayload?.total_cost_usd ?? spent;
  const cpc = companies ? runCost / companies : 0;

  return (
    <section className="sticky top-0 z-40 rounded-xl border border-slate-700 bg-slate-900/95 p-4 backdrop-blur">
      {!status && (
        <div className="flex flex-wrap items-center justify-between gap-3">
          <p className="text-sm text-slate-200">
            Estimated cost: <strong>${estimated.toFixed(2)}</strong> · ~
            {estimate?.estimated_companies ?? 0} companies
          </p>
          <button
            type="button"
            onClick={onRun}
            disabled={runDisabled}
            className="rounded bg-sky-600 px-4 py-2 text-sm text-white disabled:cursor-not-allowed disabled:bg-slate-700"
          >
            Run
          </button>
        </div>
      )}

      {running && status && (
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm text-slate-200">
            <span>
              Spent so far: <strong>${spent.toFixed(2)}</strong> / ${estimated.toFixed(2)} est ({pct}%)
            </span>
            <button
              type="button"
              onClick={onRun}
              disabled
              className="rounded bg-slate-700 px-3 py-1 text-xs text-slate-200"
            >
              Running...
            </button>
          </div>
          <div className="h-2 w-full overflow-hidden rounded bg-slate-700">
            <div className="h-2 bg-sky-500" style={{ width: `${pct}%` }} />
          </div>
          <p className="text-xs text-slate-300">
            Exa: ${Number(statusPayload?.costs?.exa || 0).toFixed(2)} · OpenAI: $
            {Number(statusPayload?.costs?.openai || 0).toFixed(2)} · Claude: $
            {Number(statusPayload?.costs?.claude || 0).toFixed(2)}
          </p>
        </div>
      )}

      {!running && status && (
        <div className="space-y-1 text-sm text-slate-200">
          <p>
            This run: <strong>${Number(runCost).toFixed(2)}</strong> · {companies} companies · $
            {cpc.toFixed(2)}/company
          </p>
          <p className="text-xs text-slate-300">
            All time: ${Number(totalCosts?.total_usd || 0).toFixed(2)} across {totalCosts?.total_runs || 0} runs · $
            {Number(totalCosts?.avg_cost_per_run || 0).toFixed(2)} avg/run
          </p>
          <button
            type="button"
            onClick={onRun}
            disabled={runDisabled}
            className="mt-1 rounded bg-sky-600 px-3 py-2 text-xs text-white disabled:cursor-not-allowed disabled:bg-slate-700"
          >
            Run again
          </button>
        </div>
      )}
    </section>
  );
}

export default CostBar;
