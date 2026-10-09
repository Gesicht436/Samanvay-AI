"use client";

import { useState } from "react";
import { resolveHitlItem } from "../lib/api";
import type { CandidateMatch, MatchResult, ReviewQueueItem } from "../lib/types";

function display(value: string | number | null | undefined): string {
  return value === null || value === undefined || value === "" ? "Not specified" : String(value);
}

export function ItemComparisonCard({
  result,
  candidate: candidateOverride,
  reviewItem,
  onResolved,
}: {
  result: MatchResult;
  candidate?: CandidateMatch;
  reviewItem?: ReviewQueueItem;
  onResolved?: () => void;
}) {
  const candidate = candidateOverride ?? result.candidate;
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [corrected, setCorrected] = useState("");
  const tier = candidate?.tier ?? result.tier;

  async function resolve(accepted: boolean) {
    if (!reviewItem) return;
    setBusy(true);
    setError(null);
    try {
      await resolveHitlItem(reviewItem.id, accepted, accepted ? undefined : corrected);
      onResolved?.();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Could not save this decision.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <article className="rounded-xl border border-[#d9dfd8] bg-white p-5 shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#e4e8e3] pb-4">
        <div className="flex items-center gap-2">
          <span className={`tier-badge ${tier === "Tier-1" ? "tier-good" : tier === "Tier-4-Reject" ? "tier-reject" : "tier-review"}`}>
            {tier}
          </span>
          <span className="text-sm text-slate-500">Candidate {candidate?.canonical_id ?? "—"}</span>
        </div>
        <strong className="text-lg">{Math.round((candidate?.similarity ?? result.confidence) * 100)}% match</strong>
      </div>

      <div className="grid gap-4 py-4 md:grid-cols-2">
        <section className="rounded-lg bg-[#f7f8f5] p-4">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500">Incoming description</h3>
          <p className="mt-2 leading-relaxed">{reviewItem?.query ?? result.raw_description}</p>
        </section>
        <section className="rounded-lg bg-[#f7f8f5] p-4">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500">Suggested canonical item</h3>
          <p className="mt-2 leading-relaxed">{candidate?.canonical_description ?? "No candidate description available"}</p>
          <p className="mt-1 text-sm text-slate-500">{candidate?.canonical_id}</p>
        </section>
      </div>

      {candidate && (
        <dl className="grid grid-cols-2 gap-x-5 gap-y-3 border-t border-[#e4e8e3] pt-4 text-sm sm:grid-cols-3 lg:grid-cols-4">
          {[
            ["Item type", candidate.item_type],
            ["Nominal size", candidate.size_nb_mm === null || candidate.size_nb_mm === undefined ? null : `${candidate.size_nb_mm} mm`],
            ["Pressure class", candidate.pressure_class === null || candidate.pressure_class === undefined ? null : `Class ${candidate.pressure_class}`],
            ["Material", candidate.metallurgy],
            ["Facing", candidate.facing_end],
            ["Standard", candidate.standard],
            ["Manufacturer", candidate.manufacturer],
            ["Project", candidate.project],
          ].map(([label, value]) => (
            <div key={label}>
              <dt className="text-xs uppercase tracking-wide text-slate-500">{label}</dt>
              <dd className="mt-1 font-medium">{display(value)}</dd>
            </div>
          ))}
        </dl>
      )}

      {candidate?.domain_scores && Object.keys(candidate.domain_scores).length > 0 && (
        <section className="mt-5">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500">Evidence by domain</h3>
          <div className="mt-3 grid grid-cols-2 gap-3 md:grid-cols-4">
            {Object.entries(candidate.domain_scores).map(([domain, score]) => (
              <div key={domain}>
                <div className="mb-1 flex justify-between text-xs uppercase">
                  <span>{domain}</span><span>{Math.round(score * 100)}%</span>
                </div>
                <div className="h-2 overflow-hidden rounded bg-slate-100">
                  <div className="h-full rounded bg-[#327457]" style={{ width: `${Math.max(0, Math.min(100, score * 100))}%` }} />
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {(candidate?.violations?.length || result.reasons.length > 0 || candidate?.reasons?.length) ? (
        <ul className="mt-4 space-y-1 text-sm">
          {[...(candidate?.violations ?? []), ...result.reasons, ...(candidate?.reasons ?? [])].map((reason, index) => (
            <li key={`${reason}-${index}`} className="text-slate-700">• {reason}</li>
          ))}
        </ul>
      ) : null}

      {reviewItem && (
        <div className="mt-5 border-t border-[#e4e8e3] pt-4">
          {tier === "Tier-4-Reject" && (
            <label className="block text-sm font-medium">
              Correct canonical item (optional)
              <input
                className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2"
                value={corrected}
                onChange={(event) => setCorrected(event.target.value)}
                placeholder="Enter the correct item or specification"
              />
            </label>
          )}
          {error && <p role="alert" className="mt-3 text-sm text-red-700">{error}</p>}
          <div className="mt-4 flex flex-wrap gap-2">
            <button className="action-primary" onClick={() => void resolve(true)} disabled={busy}>
              {busy ? "Saving…" : "Approve match"}
            </button>
            <button className="action-secondary" onClick={() => void resolve(false)} disabled={busy}>
              Reject / correct
            </button>
          </div>
        </div>
      )}
    </article>
  );
}
