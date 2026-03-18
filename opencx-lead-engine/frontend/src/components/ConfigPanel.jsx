function ConfigPanel({ config, setConfig, collapsed, setCollapsed, hasAllKeys }) {
  const setField = (key, value) => setConfig((prev) => ({ ...prev, [key]: value }));

  return (
    <section className="mt-4 rounded-xl border border-slate-700 bg-slate-900/70 p-4">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-lg font-semibold text-slate-100">Config</h2>
        <div className="flex items-center gap-2">
          {hasAllKeys && (
            <span className="rounded bg-emerald-800 px-2 py-1 text-xs text-emerald-100">
              Keys configured ✓
            </span>
          )}
          <button
            type="button"
            onClick={() => setCollapsed((v) => !v)}
            className="rounded bg-slate-700 px-2 py-1 text-xs text-white hover:bg-slate-600"
          >
            {collapsed ? "Expand" : "Collapse"}
          </button>
        </div>
      </div>
      {!collapsed && (
        <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
          <label className="text-sm text-slate-300">
            Exa API Key
            <input
              type="password"
              className="mt-1 w-full rounded border border-slate-600 bg-slate-950 p-2 text-slate-100"
              value={config.exaKey}
              onChange={(e) => setField("exaKey", e.target.value)}
            />
          </label>
          <label className="text-sm text-slate-300">
            OpenAI API Key
            <input
              type="password"
              className="mt-1 w-full rounded border border-slate-600 bg-slate-950 p-2 text-slate-100"
              value={config.openaiKey}
              onChange={(e) => setField("openaiKey", e.target.value)}
            />
          </label>
          <label className="text-sm text-slate-300">
            Claude API Key
            <input
              type="password"
              className="mt-1 w-full rounded border border-slate-600 bg-slate-950 p-2 text-slate-100"
              value={config.claudeKey}
              onChange={(e) => setField("claudeKey", e.target.value)}
            />
          </label>
          <label className="text-sm text-slate-300">
            Default webhook URL
            <input
              type="text"
              className="mt-1 w-full rounded border border-slate-600 bg-slate-950 p-2 text-slate-100"
              value={config.defaultWebhookUrl}
              onChange={(e) => setField("defaultWebhookUrl", e.target.value)}
            />
          </label>
        </div>
      )}
    </section>
  );
}

export default ConfigPanel;
