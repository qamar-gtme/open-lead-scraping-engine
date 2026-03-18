import { useEffect, useMemo, useState } from "react";
import ConfigPanel from "./components/ConfigPanel";
import CostBar from "./components/CostBar";
import HistoryTab from "./components/HistoryTab";
import LogStream from "./components/LogStream";
import PromptPanel from "./components/PromptPanel";
import ResultsTable from "./components/ResultsTable";
import RunPanel from "./components/RunPanel";
import SuggestionPanel from "./components/SuggestionPanel";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

const DEFAULT_RUN_CONFIG = {
  prompt: "",
  list_type: "high_volume",
  regions: ["NL", "BE"],
  enrichers: ["exa_neural", "exa_similar", "exa_keyword"],
  anchor_urls: [],
  planner_model: "claude-haiku-4-5",
  qualifier_model: "gpt-4o",
  max_results_per_query: 10,
  outputs: ["csv_writer"],
  webhook_url: "",
};

const DEFAULT_KEYS = {
  exaKey: "",
  openaiKey: "",
  claudeKey: "",
  defaultWebhookUrl: "",
};

function App() {
  const [prompt, setPrompt] = useState("");
  const [suggestion, setSuggestion] = useState(null);
  const [suggestionError, setSuggestionError] = useState("");
  const [suggestionLoading, setSuggestionLoading] = useState(false);
  const [suggestionAccepted, setSuggestionAccepted] = useState(false);
  const [showRunPanel, setShowRunPanel] = useState(true);
  const [runConfig, setRunConfig] = useState(DEFAULT_RUN_CONFIG);
  const [estimate, setEstimate] = useState(null);
  const [jobId, setJobId] = useState("");
  const [jobStatus, setJobStatus] = useState("");
  const [statusPayload, setStatusPayload] = useState(null);
  const [resultsPayload, setResultsPayload] = useState(null);
  const [totalCosts, setTotalCosts] = useState(null);
  const [history, setHistory] = useState([]);
  const [keysConfig, setKeysConfig] = useState(DEFAULT_KEYS);
  const [configCollapsed, setConfigCollapsed] = useState(false);
  const [listTypes, setListTypes] = useState([]);
  const [enrichers, setEnrichers] = useState([]);
  const [models, setModels] = useState([]);
  const [outputs, setOutputs] = useState([]);

  const jobTerminal = ["completed", "failed", "cancelled", "cancel_requested"].includes(jobStatus);
  const hasAllKeys = Boolean(keysConfig.exaKey && keysConfig.openaiKey && keysConfig.claudeKey);
  const debouncedPrompt = useDebounce(prompt, 800);

  useEffect(() => {
    const saved = localStorage.getItem("opencx_keys");
    if (saved) {
      const parsed = JSON.parse(saved);
      setKeysConfig({ ...DEFAULT_KEYS, ...parsed });
      if (parsed.exaKey && parsed.openaiKey && parsed.claudeKey) {
        setConfigCollapsed(true);
      }
    }
  }, []);

  useEffect(() => {
    localStorage.setItem("opencx_keys", JSON.stringify(keysConfig));
  }, [keysConfig]);

  useEffect(() => {
    Promise.all([
      fetchJson("/list-types"),
      fetchJson("/enrichers"),
      fetchJson("/models"),
      fetchJson("/outputs"),
      fetchJson("/costs/total"),
      fetchJson("/history"),
    ])
      .then(([listsResp, enrichersResp, modelsResp, outputsResp, totalsResp, historyResp]) => {
        setListTypes(listsResp);
        setEnrichers(enrichersResp);
        setModels(modelsResp);
        setOutputs(outputsResp);
        setTotalCosts(totalsResp);
        setHistory(historyResp);
      })
      .catch(() => {
        // Non-fatal during initial load if backend is still starting.
      });
  }, []);

  useEffect(() => {
    if (!debouncedPrompt || debouncedPrompt.length < 4) {
      return;
    }
    setSuggestionLoading(true);
    setSuggestionError("");
    fetchJson("/suggest", {
      method: "POST",
      body: JSON.stringify({ prompt: debouncedPrompt }),
    })
      .then((data) => {
        setSuggestion(data);
        setSuggestionAccepted(false);
        setShowRunPanel(true);
        setRunConfig((prev) => ({
          ...prev,
          prompt: debouncedPrompt,
          list_type: data.list_type ?? prev.list_type,
          regions: data.regions ?? prev.regions,
          enrichers: data.enrichers ?? prev.enrichers,
          anchor_urls: data.anchor_urls ?? prev.anchor_urls,
          planner_model: data.planner_model ?? prev.planner_model,
          qualifier_model: data.qualifier_model ?? prev.qualifier_model,
        }));
      })
      .catch((err) => setSuggestionError(err.message))
      .finally(() => setSuggestionLoading(false));
  }, [debouncedPrompt]);

  useEffect(() => {
    const qp = new URLSearchParams({
      prompt: runConfig.prompt || prompt,
      list_type: runConfig.list_type,
      regions: runConfig.regions.join(","),
      enrichers: runConfig.enrichers.join(","),
      anchor_urls: runConfig.anchor_urls.join(","),
      planner_model: runConfig.planner_model,
      qualifier_model: runConfig.qualifier_model,
      max_results_per_query: String(runConfig.max_results_per_query),
      outputs: runConfig.outputs.join(","),
    });
    fetchJson(`/costs/estimate?${qp.toString()}`)
      .then(setEstimate)
      .catch(() => setEstimate(null));
  }, [prompt, runConfig]);

  useEffect(() => {
    if (!jobId) {
      return;
    }
    const tick = () => {
      fetchJson(`/status/${jobId}`)
        .then((data) => {
          setStatusPayload(data);
          setJobStatus(data.phase);
        })
        .catch(() => null);
      fetchJson(`/results/${jobId}`).then(setResultsPayload).catch(() => null);
      fetchJson("/costs/total").then(setTotalCosts).catch(() => null);
      fetchJson("/history").then(setHistory).catch(() => null);
    };
    tick();
    const interval = setInterval(tick, 2000);
    return () => clearInterval(interval);
  }, [jobId]);

  const runDisabled = !suggestionAccepted || (!estimate && !runConfig.prompt) || !jobTerminal && Boolean(jobId);

  async function handleRun() {
    const payload = { ...runConfig, prompt: runConfig.prompt || prompt };
    const response = await fetchJson("/run", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    setJobId(response.job_id);
    setJobStatus(response.status);
    setResultsPayload(null);
  }

  async function handleResend(jobIdToResend) {
    const qp = keysConfig.defaultWebhookUrl
      ? `?webhook_url=${encodeURIComponent(keysConfig.defaultWebhookUrl)}`
      : "";
    await fetchJson(`/resend-webhook/${jobIdToResend}${qp}`, { method: "POST" });
    fetchJson("/history").then(setHistory).catch(() => null);
  }

  const logs = useMemo(() => statusPayload?.live_logs ?? [], [statusPayload]);

  return (
    <div className="mx-auto min-h-screen max-w-7xl px-4 pb-10 pt-6">
      <CostBar
        estimate={estimate}
        status={jobStatus}
        statusPayload={statusPayload}
        totalCosts={totalCosts}
        resultsPayload={resultsPayload}
        onRun={handleRun}
        runDisabled={runDisabled}
      />

      <h1 className="mb-6 mt-4 text-3xl font-semibold text-slate-100">open.cx lead generation ecosystem</h1>

      <PromptPanel
        prompt={prompt}
        setPrompt={setPrompt}
        loading={suggestionLoading}
        error={suggestionError}
      />

      <SuggestionPanel
        suggestion={suggestion}
        accepted={suggestionAccepted}
        onEdit={() => {
          setSuggestionAccepted(false);
          setShowRunPanel(true);
        }}
        onAccept={() => {
          setSuggestionAccepted(true);
          setShowRunPanel(false);
        }}
      />

      <ConfigPanel
        config={keysConfig}
        setConfig={setKeysConfig}
        collapsed={configCollapsed}
        setCollapsed={setConfigCollapsed}
        hasAllKeys={hasAllKeys}
      />

      <RunPanel
        visible={showRunPanel}
        config={runConfig}
        setConfig={setRunConfig}
        listTypes={listTypes}
        enrichers={enrichers}
        models={models}
        outputs={outputs}
        defaultWebhookUrl={keysConfig.defaultWebhookUrl}
      />

      <div className="mt-6 grid grid-cols-1 gap-4 lg:grid-cols-[65%_35%]">
        <ResultsTable
          results={resultsPayload?.results ?? []}
          totalCost={resultsPayload?.total_cost_usd ?? 0}
          jobId={jobId}
        />
        <LogStream logs={logs} />
      </div>

      <HistoryTab history={history} onResend={handleResend} />
    </div>
  );

  async function fetchJson(path, options = {}) {
    const resp = await fetch(`${API_BASE}${path}`, {
      headers: { "Content-Type": "application/json", ...(options.headers || {}) },
      ...options,
    });
    const text = await resp.text();
    const data = text ? JSON.parse(text) : {};
    if (!resp.ok) {
      throw new Error(data?.detail || `Request failed: ${resp.status}`);
    }
    return data;
  }
}

function useDebounce(value, delayMs) {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delayMs);
    return () => clearTimeout(timer);
  }, [value, delayMs]);
  return debounced;
}

export default App;
