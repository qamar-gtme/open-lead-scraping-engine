import { useMemo, useState } from "react";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

const COLUMNS = [
  "fit_score",
  "icp_tier",
  "company_name",
  "country",
  "industry",
  "estimated_total_employees",
  "estimated_support_headcount",
];

function ResultsTable({ results, totalCost, jobId }) {
  const [tierFilter, setTierFilter] = useState("all");
  const [search, setSearch] = useState("");
  const [sortKey, setSortKey] = useState("fit_score");
  const [sortDir, setSortDir] = useState("desc");

  const filtered = useMemo(() => {
    let rows = [...results];
    if (tierFilter !== "all") {
      rows = rows.filter((r) => String(r.icp_tier) === tierFilter);
    }
    if (search.trim()) {
      const q = search.toLowerCase();
      rows = rows.filter(
        (r) =>
          String(r.company_name || "").toLowerCase().includes(q) ||
          String(r.domain || "").toLowerCase().includes(q) ||
          String(r.industry || "").toLowerCase().includes(q)
      );
    }
    rows.sort((a, b) => compareValues(a[sortKey], b[sortKey], sortDir));
    return rows;
  }, [results, tierFilter, search, sortKey, sortDir]);

  const downloadUrl = jobId ? `${API_BASE}/download/${jobId}` : "#";

  return (
    <section className="rounded-xl border border-slate-700 bg-slate-900/70 p-4">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-lg font-semibold text-slate-100">Results</h2>
        <a
          href={downloadUrl}
          className={`rounded px-3 py-1 text-xs ${
            jobId ? "bg-emerald-600 text-white" : "bg-slate-700 text-slate-300"
          }`}
        >
          Download CSV
        </a>
      </div>
      <div className="mb-3 flex flex-wrap items-center gap-2">
        <select
          className="rounded border border-slate-600 bg-slate-950 px-2 py-1 text-xs text-slate-100"
          value={tierFilter}
          onChange={(e) => setTierFilter(e.target.value)}
        >
          <option value="all">All tiers</option>
          <option value="1">Tier 1</option>
          <option value="2">Tier 2</option>
          <option value="3">Tier 3</option>
        </select>
        <input
          placeholder="Search company, domain, industry"
          className="rounded border border-slate-600 bg-slate-950 px-2 py-1 text-xs text-slate-100"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <span className="text-xs text-slate-300">
          {filtered.length} companies · ${Number(totalCost || 0).toFixed(2)} total
        </span>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full text-left text-xs text-slate-200">
          <thead className="bg-slate-800">
            <tr>
              {COLUMNS.map((column) => (
                <th
                  key={column}
                  className="cursor-pointer px-2 py-2"
                  onClick={() => {
                    if (sortKey === column) {
                      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
                    } else {
                      setSortKey(column);
                      setSortDir("desc");
                    }
                  }}
                >
                  {column}
                </th>
              ))}
              <th className="px-2 py-2">fit_reason</th>
              <th className="px-2 py-2">suggested_angle</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((row, idx) => (
              <tr key={`${row.domain}-${idx}`} className="border-b border-slate-800">
                <td className="px-2 py-2">
                  <span className={`rounded px-2 py-1 ${scoreClass(row.fit_score)}`}>{row.fit_score}</span>
                </td>
                <td className="px-2 py-2">{row.icp_tier}</td>
                <td className="px-2 py-2">
                  <a
                    href={`https://${row.domain}`}
                    target="_blank"
                    rel="noreferrer"
                    className="text-sky-300 hover:underline"
                  >
                    {row.company_name}
                  </a>
                </td>
                <td className="px-2 py-2">{row.country}</td>
                <td className="px-2 py-2">{row.industry}</td>
                <td className="px-2 py-2">{row.estimated_total_employees ?? "-"}</td>
                <td className="px-2 py-2">{row.estimated_support_headcount ?? "-"}</td>
                <td className="px-2 py-2">{row.fit_reason}</td>
                <td className="px-2 py-2">{row.suggested_angle}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function compareValues(a, b, dir) {
  const av = a ?? "";
  const bv = b ?? "";
  if (typeof av === "number" && typeof bv === "number") {
    return dir === "asc" ? av - bv : bv - av;
  }
  return dir === "asc" ? String(av).localeCompare(String(bv)) : String(bv).localeCompare(String(av));
}

function scoreClass(score) {
  if (score >= 90) return "bg-green-600 text-white";
  if (score >= 75) return "bg-green-400 text-slate-900";
  if (score >= 60) return "bg-yellow-400 text-slate-900";
  if (score >= 40) return "bg-orange-400 text-slate-900";
  return "bg-red-400 text-slate-900";
}

export default ResultsTable;
