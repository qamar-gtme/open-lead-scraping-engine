function PromptPanel({ prompt, setPrompt, loading, error }) {
  return (
    <section className="rounded-xl border border-slate-700 bg-slate-900/70 p-4">
      <h2 className="mb-2 text-lg font-semibold text-slate-100">Prompt</h2>
      <textarea
        className="h-36 w-full rounded-md border border-slate-600 bg-slate-950 p-3 text-sm text-slate-100 outline-none focus:border-sky-500"
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
        placeholder="Describe what you're looking for... e.g. ecommerce companies in Netherlands with large support teams, or German SaaS companies using Intercom"
      />
      {loading && <p className="mt-2 text-sm text-sky-300">Claude is reading your prompt...</p>}
      {error && <p className="mt-2 text-sm text-rose-300">{error}</p>}
    </section>
  );
}

export default PromptPanel;
