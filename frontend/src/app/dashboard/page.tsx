"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { getDashboardSummary } from "../../lib/api";
import type { DashboardSummary } from "../../lib/types";

export default function Dashboard() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    setError(null);
    try {
      setSummary(await getDashboardSummary());
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Dashboard status is unavailable.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void refresh(); }, [refresh]);

  const cards = summary ? [
    { label: "Reviews waiting", value: summary.pending_reviews, href: "/hitl", hint: "Open the review queue" },
    { label: "Feedback captured", value: summary.resolved_reviews, href: "/hitl", hint: "Resolved examples in this session" },
    { label: "Vector search", value: summary.vector_search.ready ? "Ready" : "Needs setup", href: "/deduplication", hint: summary.vector_search.message },
    { label: "Document OCR", value: `${summary.ocr.raster_dpi} DPI`, href: "/ingest", hint: "Per-page hybrid routing" },
  ] : [];

  return (
    <main className="page-shell">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="eyebrow">Operations / overview</p>
          <h1 className="page-title">Material command center</h1>
          <p className="page-lede mt-3">A live view of catalog matching, certificate extraction, and human review.</p>
        </div>
        <button className="action-secondary" onClick={() => void refresh()} disabled={loading}>Refresh status</button>
      </div>

      {error && <p role="alert" className="mt-6 rounded-lg bg-red-50 p-4 text-sm text-red-800">{error}</p>}
      {loading && <p role="status" className="mt-8 text-sm text-slate-600">Loading live workspace status…</p>}
      {summary && <>
        <section className="mt-8 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {cards.map((card) => (
            <Link href={card.href} key={card.label} className="stat-card interactive-card">
              <span>{card.label}</span><strong>{card.value}</strong><small>{card.hint}</small>
            </Link>
          ))}
        </section>

        <section className="mt-8 grid gap-5 lg:grid-cols-[1.2fr_.8fr]">
          <div className="rounded-xl border border-[#d9dfd8] bg-white p-5 shadow-sm">
            <div className="flex items-center justify-between gap-3">
              <div><p className="eyebrow">System status</p><h2 className="mt-1 text-xl font-bold">Matching pipeline</h2></div>
              <span className={`status-pill ${summary.vector_search.ready ? "status-ready" : "status-pending"}`}>{summary.vector_search.ready ? "Operational" : "Setup needed"}</span>
            </div>
            <p className="mt-4 text-sm text-slate-600">{summary.vector_search.message}</p>
            <div className="mt-5 divide-y divide-slate-100">
              <StatusRow label="Embedding model" ready={summary.embedding_model_ready} />
              <StatusRow label="Reranker model" ready={summary.reranker_model_ready} optional />
              <StatusRow label="Qdrant vector index" ready={summary.vector_search.ready} />
              <StatusRow label="PaddleOCR primary engine" ready={summary.ocr.primary_engine_ready} />
              <StatusRow label="EasyOCR fallback" ready={summary.ocr.fallback_engine_ready} />
            </div>
          </div>

          <div className="rounded-xl bg-[#17221b] p-5 text-white">
            <p className="text-xs font-bold uppercase tracking-[.18em] text-[#b8d9c0]">Available capabilities</p>
            <ul className="mt-4 space-y-3 text-sm">
              <li>✓ Four evidence vectors: {summary.capabilities.named_vector_domains.join(" · ")}</li>
              <li>{summary.capabilities.industry_metadata ? "✓" : "—"} Indian standards, OISD, EIL, GeM, CPPP and MESC extraction</li>
              <li>{summary.ocr.mtc_intelligence && summary.ocr.chemistry_extraction ? "✓" : "—"} Full MTC intelligence, chemistry, and mechanical properties</li>
              <li>{summary.ocr.manufacturer_tpi_extraction ? "✓" : "—"} Manufacturer and TPI extraction</li>
              <li>{summary.capabilities.active_learning ? "✓" : "—"} Human review and feedback capture</li>
            </ul>
            <div className="mt-5 border-t border-white/20 pt-4 text-xs leading-relaxed text-white/80">
              <p className="font-bold">OCR policy: {summary.ocr.routing.replaceAll("_", " ")} · {summary.ocr.raster_dpi} DPI</p>
              <p className="mt-1">Preprocessing: {summary.ocr.preprocessing.join(", ")}. {summary.ocr.primary_engine} with {summary.ocr.fallback_engine} fallback.</p>
            </div>
            <p className="mt-5 border-t border-white/20 pt-4 text-xs leading-relaxed text-white/70">Review feedback is held in memory for this running API process. Persist it before relying on it across restarts.</p>
          </div>
        </section>

        <section className="mt-8">
          <p className="eyebrow">Quick actions</p>
          <div className="mt-3 grid gap-3 sm:grid-cols-3">
            <ActionLink href="/deduplication" title="Find a material match" text="Compare a description with the canonical catalog." />
            <ActionLink href="/ingest" title="Extract a certificate" text="Upload a document or paste MTC text." />
            <ActionLink href="/hitl" title="Review uncertain matches" text="Approve or correct suggestions and capture feedback." />
          </div>
        </section>
      </>}
    </main>
  );
}

function StatusRow({ label, ready, optional = false }: { label: string; ready: boolean; optional?: boolean }) {
  return <div className="flex items-center justify-between py-3 text-sm"><span>{label}{optional ? " (optional)" : ""}</span><span className={ready ? "text-emerald-700" : "text-amber-700"}>{ready ? "Ready" : "Not ready"}</span></div>;
}

function ActionLink({ href, title, text }: { href: string; title: string; text: string }) {
  return <Link href={href} className="rounded-xl border border-[#d9dfd8] bg-white p-4 transition hover:-translate-y-0.5 hover:shadow-md"><h2 className="font-bold">{title} <span aria-hidden="true">→</span></h2><p className="mt-2 text-sm text-slate-600">{text}</p></Link>;
}
