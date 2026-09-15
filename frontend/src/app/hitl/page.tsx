"use client";

import { useEffect, useState } from "react";
import { fetchHITLQueue, resolveHITLItem, bulkResolveHITL } from "@/lib/api";
import { HITLQueueItem } from "@/lib/types";
import {
  CheckCircle2,
  AlertTriangle,
  XCircle,
  CheckCheck,
  Filter,
  RefreshCw,
  MapPin,
  Download,
} from "lucide-react";
import { exportToCsv } from "@/lib/exportUtils";


export default function HITLTriagePage() {
  const [queue, setQueue] = useState<HITLQueueItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterCpse, setFilterCpse] = useState<string>("ALL");
  const [filterTier, setFilterTier] = useState<string>("ALL");
  const [actionFeedback, setActionFeedback] = useState<string | null>(null);
  const [resolvedCount, setResolvedCount] = useState(0);

  const loadQueue = async () => {
    setLoading(true);
    const data = await fetchHITLQueue();
    setQueue(data);
    setLoading(false);
  };

  useEffect(() => {
    loadQueue();
  }, []);

  const handleResolve = async (
    item: HITLQueueItem,
    decision: "APPROVE" | "REJECT" | "RECLASSIFY"
  ) => {
    await resolveHITLItem({
      source_sku: item.source_sku,
      source_cpse: item.source_cpse,
      canonical_id: item.canonical_id,
      decision,
      tier: item.tier,
      confidence: item.confidence,
    });
    setQueue((prev) => prev.filter((i) => i.queue_id !== item.queue_id));
    setResolvedCount((prev) => prev + 1);
    setActionFeedback(`Item ${item.source_sku} marked as ${decision}.`);
    setTimeout(() => setActionFeedback(null), 3000);
  };

  const handleBulkApprove = async () => {
    if (queue.length === 0) return;
    const safeItems = queue.filter(
      (i) => i.tier === "TIER_1_IDENTICAL" || i.confidence >= 0.85
    );
    await bulkResolveHITL(safeItems);
    setResolvedCount((prev) => prev + safeItems.length);
    setQueue((prev) =>
      prev.filter((i) => !safeItems.some((s) => s.queue_id === i.queue_id))
    );
    setActionFeedback(`Approved ${safeItems.length} items.`);
    setTimeout(() => setActionFeedback(null), 3000);
  };

  const filteredQueue = queue.filter((item) => {
    if (filterCpse !== "ALL" && item.source_cpse !== filterCpse) return false;
    if (filterTier !== "ALL" && item.tier !== filterTier) return false;
    return true;
  });

  const handleExportHitlCsv = () => {
    exportToCsv(filteredQueue, "Samanvay_Verification_Queue", {
      queue_id: "Queue ID",
      source_sku: "Legacy SKU",
      source_cpse: "Source CPSE",
      source_depot: "Source Depot",
      source_description: "Legacy Description",
      suggested_sku: "Suggested SKU",
      suggested_cpse: "Target CPSE",
      suggested_depot: "Target Depot",
      suggested_description: "Suggested Equivalent Description",
      canonical_id: "Canonical ID",
      tier: "Compatibility Tier",
      confidence: "Confidence Score",
      unit_cost_inr: "Unit Cost (INR)",
      available_qty: "Available Qty",
      days_idle: "Days Idle",
      rationale: "Engineering Rationale",
    });
  };


  return (
    <div className="space-y-4">
      {/* 1. Header */}
      <div className="bg-white border border-[#d5d9d9] rounded p-4 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-lg font-bold text-[#0f1111]">
            Material Verification Queue
          </h1>
          <p className="text-xs text-[#565959] mt-0.5">
            Review and certify material code equivalences flagged for specification differences.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleExportHitlCsv}
            className="btn-amazon-white px-3 py-1.5 rounded text-xs font-semibold flex items-center gap-1.5 cursor-pointer"
            title="Export verification queue to CSV/Excel"
          >
            <Download className="w-3.5 h-3.5 text-[#565959]" />
            Export CSV
          </button>
          <button
            onClick={handleBulkApprove}
            disabled={queue.length === 0}
            className="btn-amazon-primary px-3.5 py-1.5 rounded text-xs font-bold transition-all flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
          >
            <CheckCheck className="w-3.5 h-3.5 text-[#0f1111]" />
            Approve Safe Items ({queue.length})
          </button>
        </div>
      </div>


      {/* Action Notification */}
      {actionFeedback && (
        <div className="bg-emerald-50 border border-emerald-300 text-[#067d62] px-3.5 py-2 rounded text-xs font-semibold flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 shrink-0 text-[#067d62]" />
          <span>{actionFeedback}</span>
        </div>
      )}

      {/* 2. Filter & Controls Toolbar */}
      <div className="bg-white border border-[#d5d9d9] rounded p-3 flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-2.5 shadow-sm">
        <div className="flex items-center gap-2 text-xs text-[#565959]">
          <Filter className="w-3.5 h-3.5 text-[#565959]" />
          <span className="font-semibold text-[#0f1111]">Filter Queue:</span>

          <select
            value={filterCpse}
            onChange={(e) => setFilterCpse(e.target.value)}
            className="amazon-input text-xs font-semibold px-2 py-1 bg-white cursor-pointer"
          >
            <option value="ALL">All CPSEs</option>
            <option value="IOCL">IOCL</option>
            <option value="ONGC">ONGC</option>
            <option value="BPCL">BPCL</option>
          </select>

          <select
            value={filterTier}
            onChange={(e) => setFilterTier(e.target.value)}
            className="amazon-input text-xs font-semibold px-2 py-1 bg-white cursor-pointer"
          >
            <option value="ALL">All Tiers</option>
            <option value="TIER_1_IDENTICAL">Tier 1 (Identical)</option>
            <option value="TIER_2_SUBSTITUTE">Tier 2 (Substitute)</option>
          </select>
        </div>

        <div className="flex items-center gap-3 text-xs text-[#565959]">
          <span>Pending: <strong>{queue.length}</strong></span>
          <span>Certified Today: <strong className="text-[#067d62]">{resolvedCount}</strong></span>
          <button
            onClick={loadQueue}
            className="btn-amazon-white p-1 rounded cursor-pointer"
            title="Refresh Queue"
          >
            <RefreshCw className="w-3.5 h-3.5 text-[#565959]" />
          </button>
        </div>
      </div>

      {/* 3. Queue Item Cards */}
      {loading ? (
        <div className="bg-white border border-[#d5d9d9] rounded p-8 text-center text-xs text-[#565959] shadow-sm">
          <RefreshCw className="w-5 h-5 animate-spin mx-auto mb-1 text-[#007185]" />
          Loading verification items...
        </div>
      ) : filteredQueue.length === 0 ? (
        <div className="bg-white border border-[#d5d9d9] rounded p-8 text-center space-y-2 shadow-sm">
          <CheckCircle2 className="w-8 h-8 text-[#067d62] mx-auto" />
          <h2 className="text-sm font-bold text-[#0f1111]">Queue is Empty</h2>
          <p className="text-xs text-[#565959] max-w-sm mx-auto">
            All flagged items have been reviewed and certified.
          </p>
          <button
            onClick={loadQueue}
            className="btn-amazon-white px-3 py-1.5 rounded text-xs font-semibold cursor-pointer"
          >
            Reload Sample Queue
          </button>
        </div>
      ) : (
        <div className="space-y-3">
          {filteredQueue.map((item) => (
            <div
              key={item.queue_id}
              className="bg-white border border-[#d5d9d9] rounded overflow-hidden shadow-sm"
            >
              {/* Card Header Strip */}
              <div className="bg-[#f2f3f3] px-4 py-2 border-b border-[#d5d9d9] flex flex-col sm:flex-row sm:items-center justify-between gap-1.5 text-xs">
                <div className="flex items-center gap-2">
                  <span className="font-mono font-bold text-[#565959]">{item.queue_id}</span>
                  <span className="text-slate-300">•</span>
                  <span
                    className={`px-2 py-0.2 rounded text-[11px] font-bold uppercase ${
                      item.tier === "TIER_1_IDENTICAL"
                        ? "bg-emerald-100 text-emerald-900 border border-emerald-300"
                        : "bg-amber-100 text-amber-900 border border-amber-300"
                    }`}
                  >
                    {item.tier === "TIER_1_IDENTICAL" ? "Tier 1: Identical" : "Tier 2: Substitute"}
                  </span>
                  <span className="text-[#565959]">
                    Confidence: <strong className="font-mono text-[#0f1111]">{(item.confidence * 100).toFixed(0)}%</strong>
                  </span>
                </div>

                <div className="font-mono text-xs text-[#007185]">
                  Canonical SKU: {item.canonical_id}
                </div>
              </div>

              {/* Card Content */}
              <div className="p-4 space-y-3">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {/* Source Item */}
                  <div className="bg-[#fbfbfb] border border-[#d5d9d9] rounded p-3 space-y-1">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-bold text-[#565959]">Requesting Item</span>
                      <span className="px-1.5 py-0.2 bg-slate-200 text-slate-800 rounded font-bold text-[10px]">
                        {item.source_cpse}
                      </span>
                    </div>
                    <div className="text-xs font-mono text-[#565959]">SKU: {item.source_sku}</div>
                    <div className="text-xs font-semibold text-[#0f1111]">{item.source_description}</div>
                    <div className="text-[11px] text-[#565959] flex items-center gap-1 pt-1 border-t border-[#eaeded]">
                      <MapPin className="w-3 h-3 text-slate-400 shrink-0" />
                      <span>{item.source_depot}</span>
                    </div>
                  </div>

                  {/* Matched Spare */}
                  <div className="bg-[#fbfbfb] border border-[#d5d9d9] rounded p-3 space-y-1">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-bold text-[#565959]">Candidate Spare</span>
                      <span className="px-1.5 py-0.2 bg-amber-100 text-amber-900 border border-amber-300 rounded font-bold text-[10px]">
                        {item.suggested_cpse}
                      </span>
                    </div>
                    <div className="text-xs font-mono text-[#565959]">SKU: {item.suggested_sku}</div>
                    <div className="text-xs font-semibold text-[#007185]">{item.suggested_description}</div>
                    <div className="text-[11px] text-[#565959] flex items-center gap-1 pt-1 border-t border-[#eaeded]">
                      <MapPin className="w-3 h-3 text-slate-400 shrink-0" />
                      <span>{item.suggested_depot}</span>
                    </div>
                  </div>
                </div>

                {/* Parameter Check Badges */}
                <div className="flex flex-wrap items-center gap-1.5">
                  {item.parameters.map((param, pIdx) => (
                    <div
                      key={pIdx}
                      className={`text-xs px-2 py-0.5 rounded border flex items-center gap-1 font-medium ${
                        param.status === "EXACT"
                          ? "bg-emerald-50 border-emerald-300 text-emerald-900"
                          : param.status === "UPGRADE"
                          ? "bg-amber-50 border-amber-300 text-amber-900"
                          : "bg-rose-50 border-rose-300 text-rose-900"
                      }`}
                    >
                      {param.status === "EXACT" ? (
                        <CheckCircle2 className="w-3 h-3 text-[#067d62]" />
                      ) : (
                        <AlertTriangle className="w-3 h-3 text-[#b12704]" />
                      )}
                      <span>
                        {param.name}: <strong className="font-mono">{param.source}</strong>
                        {param.status === "UPGRADE" && (
                          <> &rarr; <strong className="font-mono">{param.candidate}</strong></>
                        )}
                      </span>
                    </div>
                  ))}
                </div>

                {/* Rationale & Inventory Info */}
                <div className="bg-[#f8f9fa] border border-[#d5d9d9] rounded p-2.5 flex flex-col md:flex-row md:items-center justify-between gap-2 text-xs">
                  <div className="text-[#565959] text-[11px] max-w-xl">
                    <strong className="text-[#0f1111]">Rationale: </strong>
                    {item.rationale}
                  </div>

                  <div className="flex items-center gap-3 shrink-0 text-[11px]">
                    <div>
                      <span className="text-[#565959]">Stock: </span>
                      <strong className="text-[#0f1111]">{item.available_qty} Units</strong>
                    </div>
                    <div>
                      <span className="text-[#565959]">Unit Cost: </span>
                      <strong className="text-[#0f1111]">₹{item.unit_cost_inr.toLocaleString("en-IN")}</strong>
                    </div>
                  </div>
                </div>

                {/* Decision Actions */}
                <div className="flex items-center justify-end gap-2 pt-1 border-t border-[#eaeded]">
                  <button
                    onClick={() => handleResolve(item, "REJECT")}
                    className="btn-amazon-white px-2.5 py-1 rounded text-xs font-semibold text-[#c40000] hover:bg-rose-50 flex items-center gap-1 cursor-pointer"
                  >
                    <XCircle className="w-3 h-3" />
                    Reject
                  </button>

                  <button
                    onClick={() => handleResolve(item, "RECLASSIFY")}
                    className="btn-amazon-white px-2.5 py-1 rounded text-xs font-semibold text-[#b12704] hover:bg-amber-50 flex items-center gap-1 cursor-pointer"
                  >
                    <AlertTriangle className="w-3 h-3" />
                    Reclassify
                  </button>

                  <button
                    onClick={() => handleResolve(item, "APPROVE")}
                    className="btn-amazon-primary px-3.5 py-1 rounded text-xs font-bold flex items-center gap-1 cursor-pointer"
                  >
                    <CheckCircle2 className="w-3.5 h-3.5 text-[#0f1111]" />
                    Approve & Link
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
