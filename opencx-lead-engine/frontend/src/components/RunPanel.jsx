const REGION_OPTIONS = ["NL", "BE", "DACH", "Nordics", "EU"];

function RunPanel({
  visible,
  config,
  setConfig,
  listTypes,
  enrichers,
  models,
  outputs,
  defaultWebhookUrl,
}) {
  if (!visible) return null;

  const toggleRegion = (region) => {
    setConfig((prev) => {
      const exists = prev.regions.includes(region);
      return {
        ...prev,
        regions: exists ? prev.regions.filter((r) => r !== region) : [...prev.regions, region],
      };
    });
  };

  const toggleEnricher = (key) => {
    setConfig((prev) => {
      const exists = prev.enrichers.includes(key);
      return {
        ...prev,
        enrichers: exists ? prev.enrichers.filter((e) => e !== key) : [...prev.enrichers, key],
      };
    });
  };

  const toggleOutput = (key) => {
    setConfig((prev) => {
      const exists = prev.outputs.includes(key);
      const next = exists ? prev.outputs.filter((o) => o !== key) : [...prev.outputs, key];
      return {
        ...prev,
        outputs: next,
        webhook_url: prev.webhook_url || defaultWebhookUrl || "",
      };
    });
  };

  return (
    <section className="mt-4 rounded-xl border border-slate-700 bg-slate-900/70 p-4">
      <h2 className="mb-3 text-lg font-semibold text-slate-100">Run settings</h2>
      <div className="grid gap-4 lg:grid-cols-2">
        <label className="text-sm text-slate-300">
          List type
          <select
            value={config.list_type}
            onChange={(e) => setConfig((prev) => ({ ...prev, list_type: e.target.value }))}
            className="mt-1 w-full rounded border border-slate-600 bg-slate-950 p-2 text-slate-100"
          >
            {listTypes.map((item) => (
              <option key={item.key} value={item.key}>
                {item.name}
              </option>
            ))}
          </select>
        </label>

        <label className="text-sm text-slate-300">
          Max results per query: {config.max_results_per_query}
          <input
            type="range"
            min={5}
            max={20}
            value={config.max_results_per_query}
            onChange={(e) =>
              setConfig((prev) => ({ ...prev, max_results_per_query: Number(e.target.value) }))
            }
            className="mt-1 w-full"
          />
        </label>

        <label className="text-sm text-slate-300">
          Planner model
          <select
            value={config.planner_model}
            onChange={(e) => setConfig((prev) => ({ ...prev, planner_model: e.target.value }))}
            className="mt-1 w-full rounded border border-slate-600 bg-slate-950 p-2 text-slate-100"
          >
            {models.map((item) => (
              <option key={item.key} value={item.key}>
                {item.name}
              </option>
            ))}
          </select>
        </label>

        <label className="text-sm text-slate-300">
          Qualifier model
          <select
            value={config.qualifier_model}
            onChange={(e) => setConfig((prev) => ({ ...prev, qualifier_model: e.target.value }))}
            className="mt-1 w-full rounded border border-slate-600 bg-slate-950 p-2 text-slate-100"
          >
            {models.map((item) => (
              <option key={item.key} value={item.key}>
                {item.name}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="mt-4">
        <p className="mb-2 text-sm text-slate-300">Regions</p>
        <div className="flex flex-wrap gap-2">
          {REGION_OPTIONS.map((region) => {
            const active = config.regions.includes(region);
            return (
              <button
                key={region}
                type="button"
                onClick={() => toggleRegion(region)}
                className={`rounded px-3 py-1 text-sm ${
                  active ? "bg-sky-600 text-white" : "bg-slate-700 text-slate-100"
                }`}
              >
                {region}
              </button>
            );
          })}
        </div>
      </div>

      <div className="mt-4">
        <p className="mb-2 text-sm text-slate-300">Enrichers</p>
        <div className="grid gap-2 md:grid-cols-2">
          {enrichers.map((item) => {
            const active = config.enrichers.includes(item.key);
            return (
              <button
                key={item.key}
                type="button"
                onClick={() => toggleEnricher(item.key)}
                className={`rounded border px-3 py-2 text-left text-sm ${
                  active
                    ? "border-emerald-500 bg-emerald-900/20 text-emerald-100"
                    : "border-slate-700 bg-slate-950 text-slate-200"
                }`}
              >
                <div className="font-medium">{item.name}</div>
                <div className="text-xs opacity-80">
                  ${item.cost_per_call_usd}/call · {active ? "on" : "off"}
                </div>
              </button>
            );
          })}
        </div>
      </div>

      <div className="mt-4">
        <p className="mb-2 text-sm text-slate-300">Output destinations</p>
        <div className="flex flex-wrap gap-2">
          {outputs.map((item) => {
            const active = config.outputs.includes(item.key);
            return (
              <button
                key={item.key}
                type="button"
                onClick={() => toggleOutput(item.key)}
                className={`rounded px-3 py-1 text-sm ${
                  active ? "bg-emerald-600 text-white" : "bg-slate-700 text-slate-100"
                }`}
              >
                {item.name}
              </button>
            );
          })}
        </div>
      </div>

      {(config.outputs.includes("webhook_clay") ||
        config.outputs.includes("webhook_generic") ||
        config.outputs.includes("webhook_hubspot")) && (
        <label className="mt-4 block text-sm text-slate-300">
          Webhook URL
          <input
            type="text"
            value={config.webhook_url || ""}
            onChange={(e) => setConfig((prev) => ({ ...prev, webhook_url: e.target.value }))}
            className="mt-1 w-full rounded border border-slate-600 bg-slate-950 p-2 text-slate-100"
          />
        </label>
      )}
    </section>
  );
}

export default RunPanel;
