"use client";

import { useCallback, useEffect, useState } from "react";
import { ItemComparisonCard } from "../../components/ItemComparisonCard";
import { getHitlQueue, getHitlTrainingExamples } from "../../lib/api";
import type { ReviewQueueItem } from "../../lib/types";

export default function Hitl() {
  const [items, setItems] = useState<ReviewQueueItem[]>([]);
  const [exampleCount, setExampleCount] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    setError(null);
    try {
      const [queueItems, examples] = await Promise.all([getHitlQueue(), getHitlTrainingExamples()]);
      setItems(queueItems);
      setExampleCount(examples.length);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Unable to load the review queue.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void refresh(); }, [refresh]);

  return (
    <main className="page-shell">
      <p className="eyebrow">Quality workflow / human review</p>
      <div className="mt-2 flex flex-wrap items-end justify-between gap-4">
        <div><h1 className="page-title">Review queue</h1><p className="page-lede mt-3">Resolve uncertain or safety-flagged matches. Decisions become training examples for future model improvements.</p></div>
        <button className="action-secondary" onClick={() => void refresh()} disabled={loading}>Refresh queue</button>
      </div>

      <section className="mt-7 grid gap-3 sm:grid-cols-3">
        <div className="stat-card"><span>Waiting for review</span><strong>{loading ? "…" : items.length}</strong></div>
        <div className="stat-card"><span>Feedback captured</span><strong>{loading ? "…" : exampleCount}</strong></div>
        <div className="stat-card"><span>Queue capacity</span><strong>500</strong></div>
      </section>

      {error && <p role="alert" className="mt-5 rounded-lg bg-red-50 p-4 text-sm text-red-800">{error}</p>}
      {loading && <p role="status" className="mt-8 text-sm text-slate-600">Loading review items…</p>}
      {!loading && !error && items.length === 0 && <section className="mt-8 rounded-xl border border-dashed border-slate-300 bg-white p-8 text-center"><h2 className="font-semibold">Queue is clear</h2><p className="mt-2 text-sm text-slate-600">Lower-confidence matches will appear here for review.</p></section>}
      {!loading && items.length > 0 && <section className="mt-8 space-y-4">{items.map((item) => (
        <ItemComparisonCard
          key={item.id}
          result={{
            raw_description: item.query,
            tier: item.candidate.tier ?? "Tier-3",
            confidence: item.candidate.similarity,
            candidate: item.candidate,
            matches: [item.candidate],
            routing: "hitl",
            reasons: [],
          }}
          reviewItem={item}
          onResolved={() => void refresh()}
        />
      ))}</section>}
    </main>
  );
}
