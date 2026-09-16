"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Card, CardHeader } from "@/components/ui/Card";
import { KpiCard } from "@/components/ui/KpiCard";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { Modal } from "@/components/ui/Modal";
import { EmptyState } from "@/components/ui/EmptyState";
import { useTheme, CPSE_OPTIONS } from "@/components/ThemeProvider";
import { DEPOT_MAP } from "@/lib/constants";
import { fetchSpares, createRequisition } from "@/lib/api";
import { formatInr } from "@/lib/formatters";
import { InterCPSESpare, UrgencyLevel } from "@/lib/types";
import {
  Search,
  Filter,
  Package,
  Building2,
  Truck,
  ArrowRight,
  ShieldCheck,
  Clock,
  Send,
  AlertTriangle,
  CheckCircle2,
  RefreshCw,
  Sparkles,
} from "lucide-react";

export default function DiscoverPage() {
  const router = useRouter();
  const { activeCpse, activeDepot } = useTheme();

  const [searchQuery, setSearchQuery] = useState("FLANGE 4IN 300#");
  const [selectedCpse, setSelectedCpse] = useState("ALL");
  const [results, setResults] = useState<InterCPSESpare[]>([]);
  const [loading, setLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);

  // Request Composition Modal
  const [selectedSpare, setSelectedSpare] = useState<InterCPSESpare | null>(null);
  const [isRequestModalOpen, setIsRequestModalOpen] = useState(false);
  const [sourceDepot, setSourceDepot] = useState(activeDepot);
  const [sourceUnit, setSourceUnit] = useState("Refinery CDU-2 / Hydrocracker Unit");
  const [requiredQty, setRequiredQty] = useState(2);
  const [urgencyLevel, setUrgencyLevel] = useState<UrgencyLevel>("EMERGENCY_SHUTDOWN");
  const [justification, setJustification] = useState(
    "Urgent replacement required for upcoming turnaround overhaul. Local vendor lead time exceeds 6 weeks."
  );
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  useEffect(() => {
    handleSearch();
  }, []);

  const handleSearch = async (overrideQuery?: string, overrideCpse?: string) => {
    setLoading(true);
    setHasSearched(true);
    const q = overrideQuery !== undefined ? overrideQuery : searchQuery;
    const target = overrideCpse !== undefined ? overrideCpse : selectedCpse;
    try {
      const spares = await fetchSpares(q || "ALL", activeCpse, target);
      setResults(spares || []);
    } catch {
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  const handleOpenRequestModal = (spare: InterCPSESpare) => {
    setSelectedSpare(spare);
    setRequiredQty(Math.min(spare.available_qty, 2));
    setSubmitError(null);
    setIsRequestModalOpen(true);
  };

  const handleSendRequest = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedSpare) return;

    setIsSubmitting(true);
    setSubmitError(null);

    try {
      const sourceDepots = DEPOT_MAP[activeCpse] || [];
      const currentDepotObj = sourceDepots.find((d) => d.id === sourceDepot) || sourceDepots[0];
      const sourceDepotName = currentDepotObj ? currentDepotObj.location : `${activeCpse} Main Facility`;

      const req = await createRequisition({
        source_cpse: activeCpse,
        source_depot: sourceDepotName,
        source_unit: sourceUnit,
        target_cpse: selectedSpare.owner_cpse,
        target_depot: selectedSpare.depot_location,
        sku_code: selectedSpare.equivalent_sku,
        item_description: selectedSpare.description,
        required_qty: requiredQty,
        unit_cost_inr: selectedSpare.unit_cost,
        justification,
        urgency_level: urgencyLevel,
      });

      setIsRequestModalOpen(false);
      // Navigate directly to the newly created request tracking page!
      router.push(`/requests/${req.requisition_id}`);
    } catch (err: any) {
      setSubmitError(err.message || "Failed to submit requisition. Please check inventory stock.");
    } finally {
      setIsSubmitting(false);
    }
  };

  // Filter results by CPSE if selected
  const displayedResults = results.filter((r) => {
    if (selectedCpse !== "ALL" && r.owner_cpse !== selectedCpse) return false;
    return true;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-xl font-bold text-[var(--text-primary)]">
          Cross-CPSE Spare Material Discovery
        </h1>
        <p className="text-xs text-[var(--text-secondary)] mt-1">
          Search the centralized idle surplus database across ONGC, IOCL, BPCL, HPCL, and GAIL.
          Locate available certified spares and dispatch procurement transfer requests directly to the holding facility.
        </p>
      </div>

      {/* Search & Quick Suggestions Card */}
      <Card>
        <div className="space-y-3">
          <div className="flex flex-col sm:flex-row gap-2">
            <div className="relative flex-1">
              <Search className="w-4 h-4 absolute left-3 top-3 text-[var(--text-muted)]" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                placeholder="Search by specification (e.g. '4 inch flange 300# A105', 'Gate valve 2in', 'Flameproof motor 37kW')..."
                className="app-input w-full pl-9 pr-3 py-2.5 text-xs font-medium"
              />
            </div>

            <select
              value={selectedCpse}
              onChange={(e) => {
                const val = e.target.value;
                setSelectedCpse(val);
                handleSearch(searchQuery, val);
              }}
              className="app-input text-xs cursor-pointer sm:w-44"
            >
              <option value="ALL">All Holding CPSEs</option>
              <option value="ONGC">ONGC Facilities</option>
              <option value="IOCL">IOCL Refineries</option>
              <option value="BPCL">BPCL Refineries</option>
            </select>

            <button
              onClick={() => handleSearch()}
              disabled={loading}
              className="btn-primary py-2 px-5 text-xs shrink-0"
            >
              {loading ? (
                <RefreshCw className="w-4 h-4 animate-spin" />
              ) : (
                <>
                  <Search className="w-4 h-4" />
                  <span>Discover Spares</span>
                </>
              )}
            </button>
          </div>

          {/* Quick preset search tags */}
          <div className="flex flex-wrap items-center gap-1.5 text-xs text-[var(--text-secondary)] pt-1">
            <span className="text-[11px] text-[var(--text-muted)] flex items-center gap-1">
              <Sparkles className="w-3 h-3 text-[var(--accent-primary)]" />
              Suggested Searches:
            </span>
            {[
              "10\" SEAMLESS PIPE",
              "4\" WN FLANGE 300#",
              "GATE VALVE 2\" CL600",
              "MOTOR EX D 37KW",
              "MECHANICAL SEAL 50MM",
              "BEARING 6310-2RS1",
            ].map((tag) => (
              <button
                key={tag}
                onClick={() => {
                  setSearchQuery(tag);
                  handleSearch(tag);
                }}
                className="px-2 py-0.5 rounded-md bg-[var(--bg-tertiary)] hover:bg-[var(--border-primary)] text-[var(--text-secondary)] text-[11px] transition-colors cursor-pointer border border-[var(--border-subtle)]"
              >
                {tag}
              </button>
            ))}
          </div>
        </div>
      </Card>

      {/* Results Header */}
      <div className="flex items-center justify-between text-xs text-[var(--text-muted)]">
        <span>
          Found <strong className="text-[var(--text-primary)] font-mono">{displayedResults.length}</strong> matching spare items across CPSE depots
        </span>
        <span>My Facility: <strong className="text-[var(--accent-primary)]">{activeCpse}</strong></span>
      </div>

      {/* Results Grid / Table */}
      {loading ? (
        <div className="py-20 flex flex-col items-center justify-center space-y-2">
          <RefreshCw className="w-6 h-6 text-[var(--accent-primary)] animate-spin" />
          <div className="text-xs text-[var(--text-secondary)]">Querying Qdrant vector index & Neo4j graph...</div>
        </div>
      ) : displayedResults.length === 0 ? (
        <Card>
          <EmptyState
            title="No Matching Spares Found"
            description="No active idle surplus items match your query. Try broadening your specification search or checking back after other plants broadcast surplus."
          />
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {displayedResults.map((spare, idx) => (
            <Card key={idx} className="flex flex-col justify-between hover:border-[var(--accent-primary)] transition-all">
              <div className="space-y-3">
                {/* Header: CPSE & SKU */}
                <div className="flex items-start justify-between gap-2 border-b border-[var(--border-subtle)] pb-2.5">
                  <div>
                    <span className="text-[10px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded bg-[var(--accent-subtle)] text-[var(--accent-primary)] border border-[var(--accent-border)]">
                      {spare.owner_cpse} Holding
                    </span>
                    <div className="font-mono text-xs font-bold text-[var(--text-primary)] mt-1">
                      {spare.equivalent_sku}
                    </div>
                  </div>
                  <div className="text-right">
                    <span className="text-[10px] text-[var(--text-muted)] block">Available Stock</span>
                    <span className="font-mono font-bold text-sm text-emerald-600 dark:text-emerald-400">
                      {spare.available_qty} Units
                    </span>
                  </div>
                </div>

                {/* Description */}
                <div>
                  <h4 className="text-xs font-bold text-[var(--text-primary)] line-clamp-2 leading-relaxed">
                    {spare.description}
                  </h4>
                  <div className="text-[11px] text-[var(--text-secondary)] mt-1 flex items-center gap-1">
                    <Building2 className="w-3 h-3 text-[var(--text-muted)] shrink-0" />
                    <span className="truncate">{spare.depot_location}</span>
                  </div>
                </div>

                {/* Specs Pill */}
                <div className="grid grid-cols-2 gap-2 p-2 rounded-md bg-[var(--bg-tertiary)]/70 text-[11px]">
                  <div>
                    <span className="text-[10px] text-[var(--text-muted)] block">Unit Cost</span>
                    <span className="font-mono font-semibold text-[var(--text-primary)]">
                      {formatInr(spare.unit_cost)}
                    </span>
                  </div>
                  <div>
                    <span className="text-[10px] text-[var(--text-muted)] block">Surplus Dormancy</span>
                    <span className="font-mono text-amber-600 dark:text-amber-400">
                      {spare.days_idle} Days Idle
                    </span>
                  </div>
                </div>
              </div>

              {/* Action Button */}
              <div className="pt-3 border-t border-[var(--border-subtle)] mt-3">
                <button
                  onClick={() => handleOpenRequestModal(spare)}
                  className="btn-primary w-full text-xs py-2 shadow-xs"
                >
                  <Send className="w-3.5 h-3.5" />
                  <span>Send Procurement Request</span>
                </button>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Procurement Request Composition Modal */}
      {selectedSpare && isRequestModalOpen && (
        <Modal
          isOpen={isRequestModalOpen}
          onClose={() => setIsRequestModalOpen(false)}
          title="Compose Cross-CPSE Procurement Requisition"
          subtitle={`Target Facility: ${selectedSpare.owner_cpse} (${selectedSpare.depot_location})`}
          maxWidth="lg"
        >
          <form onSubmit={handleSendRequest} className="space-y-4">
            {submitError && (
              <div className="p-2.5 rounded-lg bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800 text-rose-800 dark:text-rose-300 text-xs flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 shrink-0" />
                <span>{submitError}</span>
              </div>
            )}

            {/* Item Summary Banner */}
            <div className="p-3 rounded-lg bg-[var(--bg-tertiary)] border border-[var(--border-subtle)] text-xs space-y-1">
              <div className="font-mono font-bold text-[var(--accent-primary)]">{selectedSpare.equivalent_sku}</div>
              <div className="font-medium text-[var(--text-primary)]">{selectedSpare.description}</div>
              <div className="text-[11px] text-[var(--text-secondary)] flex items-center justify-between pt-1">
                <span>Holding Facility: <strong>{selectedSpare.owner_cpse}</strong> ({selectedSpare.depot_location})</span>
                <span>Stock: <strong>{selectedSpare.available_qty}</strong> units available</span>
              </div>
            </div>

            {/* Requisition Fields */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="text-[11px] font-semibold text-[var(--text-secondary)] block mb-1">
                  Requesting Depot (Your Facility)
                </label>
                <select
                  value={sourceDepot}
                  onChange={(e) => setSourceDepot(e.target.value)}
                  className="app-input w-full cursor-pointer text-xs"
                  required
                >
                  {(DEPOT_MAP[activeCpse] || []).map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.name} ({d.state})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-[11px] font-semibold text-[var(--text-secondary)] block mb-1">
                  Plant Processing Unit
                </label>
                <input
                  type="text"
                  value={sourceUnit}
                  onChange={(e) => setSourceUnit(e.target.value)}
                  className="app-input w-full text-xs"
                  required
                />
              </div>

              <div>
                <label className="text-[11px] font-semibold text-[var(--text-secondary)] block mb-1">
                  Required Quantity (Max: {selectedSpare.available_qty})
                </label>
                <input
                  type="number"
                  min="1"
                  max={selectedSpare.available_qty}
                  value={requiredQty}
                  onChange={(e) => setRequiredQty(Math.min(selectedSpare.available_qty, Math.max(1, parseInt(e.target.value) || 1)))}
                  className="app-input w-full font-mono font-bold text-xs"
                  required
                />
              </div>

              <div>
                <label className="text-[11px] font-semibold text-[var(--text-secondary)] block mb-1">
                  Urgency Level
                </label>
                <select
                  value={urgencyLevel}
                  onChange={(e) => setUrgencyLevel(e.target.value as UrgencyLevel)}
                  className="app-input w-full cursor-pointer text-xs"
                >
                  <option value="EMERGENCY_SHUTDOWN">Emergency Shutdown (Critical Risk)</option>
                  <option value="PLANNED_MAINTENANCE">Planned Maintenance (14 Days Window)</option>
                  <option value="ROUTINE">Routine Replenishment</option>
                </select>
              </div>
            </div>

            <div>
              <label className="text-[11px] font-semibold text-[var(--text-secondary)] block mb-1">
                Engineering Justification & Operating Unit Need
              </label>
              <textarea
                rows={3}
                value={justification}
                onChange={(e) => setJustification(e.target.value)}
                className="app-input w-full text-xs"
                required
              />
            </div>

            {/* Financial Valuation Summary */}
            <div className="p-2.5 rounded-lg bg-[var(--bg-tertiary)] border border-[var(--border-subtle)] flex items-center justify-between text-xs">
              <span className="text-[var(--text-secondary)]">Total Requisition Value:</span>
              <span className="font-mono font-bold text-sm text-[var(--accent-primary)]">
                {formatInr(requiredQty * selectedSpare.unit_cost)}
              </span>
            </div>

            {/* Form Actions */}
            <div className="flex items-center justify-end gap-2 pt-2 border-t border-[var(--border-subtle)]">
              <button
                type="button"
                onClick={() => setIsRequestModalOpen(false)}
                className="btn-secondary"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isSubmitting}
                className="btn-primary"
              >
                {isSubmitting ? (
                  <>
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                    <span>Transmitting Request...</span>
                  </>
                ) : (
                  <>
                    <Send className="w-3.5 h-3.5" />
                    <span>Send Requisition to {selectedSpare.owner_cpse}</span>
                  </>
                )}
              </button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}
