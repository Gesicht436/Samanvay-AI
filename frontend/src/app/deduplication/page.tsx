"use client";

import { FormEvent, useState } from "react";
import { ItemComparisonCard } from "../../components/ItemComparisonCard";
import { matchDescription } from "../../lib/api";
import type { MatchResult } from "../../lib/types";

export default function Deduplication() {
  const [description, setDescription] = useState("");
  const [result, setResult] = useState<MatchResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setResult(null);
    setSearched(false);
    setLoading(true);
    try {
      setResult(await matchDescription(description.trim()));
      setSearched(true);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Matching request failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="page-shell">
      <p className="eyebrow">Catalog workspace / material matching</p>
      <h1 className="page-title">Find the closest<br /><span>canonical item.</span></h1>
      <p className="page-lede">Paste a procurement or engineering description. Matching combines size, metallurgy, pressure/temperature, standards, and human-reviewed safety checks.</p>

      <form onSubmit={(event) => void submit(event)} className="mt-8 rounded-xl border border-[#d9dfd8] bg-white p-5 shadow-sm">
        <label htmlFor="description" className="block font-semibold">Material description</label>
        <textarea
          id="description"
          className="form-control mt-2 min-h-36"
          value={description}
          onChange={(event) => setDescription(event.target.value)}
          placeholder="Example: Gate valve, DN100, PN16, ASTM A216 WCB, API 600"
          maxLength={4000}
          required
        />
        <div className="mt-3 flex flex-wrap items-center justify-between gap-3">
          <p className="text-sm text-slate-500">Up to 4,000 characters · ranked with the compatibility reranker</p>
          <button className="action-primary" disabled={loading || description.trim().length === 0}>
            {loading ? "Finding candidates…" : "Find matches"}
          </button>
        </div>
      </form>

      {error && <p role="alert" className="mt-5 rounded-lg bg-red-50 p-4 text-sm text-red-800">{error}</p>}
      {result === null && !searched && !error && !loading && <section className="mt-8 rounded-xl border border-dashed border-slate-300 bg-white/60 p-8 text-center"><p className="font-semibold">Your results will appear here</p><p className="mt-2 text-sm text-slate-600">Use a description with the size, pressure rating, material, and governing standard when available.</p></section>}
      {result === null && loading && <p className="mt-8 text-sm text-slate-600" role="status">Searching the catalog and checking compatibility…</p>}
      {searched && result === null && !error && !loading && <section className="mt-8 rounded-xl border border-amber-300 bg-amber-50 p-5"><h2 className="font-semibold">No catalog match found</h2><p className="mt-1 text-sm">Try adding a standard, material grade, or nominal size. If matching is unavailable, check the dashboard service status.</p></section>}
      {result && result.matches.length === 0 && <section className="mt-8 rounded-xl border border-amber-300 bg-amber-50 p-5"><h2 className="font-semibold">No catalog match found</h2><p className="mt-1 text-sm">Try adding a standard, material grade, or nominal size. If matching is unavailable, check the dashboard service status.</p></section>}
      {result && result.matches.length > 0 && (
        <section className="mt-9">
          <div className="mb-4 flex flex-wrap items-end justify-between gap-2">
            <div><p className="eyebrow">Ranked suggestions</p><h2 className="mt-1 text-2xl font-bold">{result.matches.length} candidate{result.matches.length === 1 ? "" : "s"}</h2></div>
            <p className="text-sm text-slate-600">Route: <strong>{result.routing}</strong></p>
          </div>
          <div className="space-y-4">
            {result.matches.map((candidate) => (
              <ItemComparisonCard
                key={candidate.canonical_id}
                result={{ ...result, candidate, matches: [] }}
                candidate={candidate}
              />
            ))}
          </div>
        </section>
      )}
    </main>
  );
}
