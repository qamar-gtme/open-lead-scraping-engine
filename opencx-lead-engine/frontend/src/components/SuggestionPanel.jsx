function SuggestionPanel({ suggestion, accepted, onEdit, onAccept }) {
  if (!suggestion) return null;

  return (
    <section className="mt-4 rounded-xl border border-slate-700 bg-slate-900/70 p-4">
      <h2 className="mb-3 text-lg font-semibold text-slate-100">Claude suggestion</h2>
      <div className="rounded-md border border-slate-700 bg-slate-950/60 p-3 text-sm text-slate-200">
        <p>
          <strong>List type:</strong> {suggestion.list_type}
        </p>
        <p>
          <strong>Regions:</strong> {(suggestion.regions || []).join(", ")}
        </p>
        <p>
          <strong>Enrichers:</strong> {(suggestion.enrichers || []).join(", ")}
        </p>
        <p>
          <strong>Est. results:</strong> {suggestion.estimated_results}
        </p>
        <p>
          <strong>Reasoning:</strong> {suggestion.reasoning}
        </p>
      </div>
      <div className="mt-3 flex flex-wrap gap-2">
        <button
          type="button"
          onClick={onEdit}
          className="rounded bg-slate-700 px-3 py-2 text-sm text-white hover:bg-slate-600"
        >
          Edit settings
        </button>
        <button
          type="button"
          onClick={onAccept}
          className="rounded bg-emerald-600 px-3 py-2 text-sm text-white hover:bg-emerald-500"
        >
          Looks good →
        </button>
        {accepted && <span className="self-center text-xs text-emerald-300">Suggestion accepted</span>}
      </div>
    </section>
  );
}

export default SuggestionPanel;
