"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Card, CardHeader } from "@/components/ui/Card";
import { KpiCard } from "@/components/ui/KpiCard";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { Modal } from "@/components/ui/Modal";
import { EmptyState } from "@/components/ui/EmptyState";
import { useTheme } from "@/components/ThemeProvider";
import {
  fetchRequisitions,
  confirmRequisition,
  declineRequisition,
  dispatchRequisition,
  deliverRequisition,
} from "@/lib/api";
import { formatInr, formatDateTime } from "@/lib/formatters";
import { InterCPSERequisition, RequisitionStatus } from "@/lib/types";
import {
  Truck,
  Package,
  Search,
  CheckCircle2,
  XCircle,
  Clock,
  ArrowRight,
  ShieldCheck,
  RefreshCw,
  AlertTriangle,
  FileText,
  Building2,
  Radio,
  Send,
} from "lucide-react";

export default function RequestsPage() {
  const router = useRouter();
  const { activeCpse } = useTheme();

  const [requisitions, setRequisitions] = useState<InterCPSERequisition[]>([]);
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [toastMsg, setToastMsg] = useState<string | null>(null);

  // Tabs: "ALL" | "INBOUND" (received by active facility) | "OUTBOUND" (sent from active facility)
  const [activeTab, setActiveTab] = useState<"ALL" | "INBOUND" | "OUTBOUND">("ALL");
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState<string>("");

  // Facility Action Modals
  const [confirmReq, setConfirmReq] = useState<InterCPSERequisition | null>(null);
  const [confirmNotes, setConfirmNotes] = useState(
    "Part physical condition verified in surplus bay; facility confirmed capability to supply requested quantity."
  );
  const [vehicleNo, setVehicleNo] = useState("GJ-05-AB-7712");
  const [driverName, setDriverName] = useState("Mukesh Singh Parmar");
  const [driverIdNo, setDriverIdNo] = useState("DL-GJ0520210084");
  const [isProcessing, setIsProcessing] = useState(false);

  const [declineReq, setDeclineReq] = useState<InterCPSERequisition | null>(null);
  const [declineReason, setDeclineReason] = useState(
    "Item reserved for imminent internal unit turnaround maintenance."
  );

  useEffect(() => {
    loadRequisitions();
  }, []);

  const loadRequisitions = async () => {
    setLoading(true);
    setErrorMsg(null);
    try {
      const data = await fetchRequisitions();
      setRequisitions(data || []);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to load transfer requisitions.");
    } finally {
      setLoading(false);
    }
  };

  const handleConfirmSupply = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!confirmReq) return;
    setIsProcessing(true);
    try {
      await confirmRequisition(confirmReq.requisition_id, {
        confirming_officer: `Chief General Manager (Procurement, ${activeCpse})`,
        confirmation_notes: confirmNotes,
        vehicle_no: vehicleNo,
        driver_name: driverName,
        driver_id_no: driverIdNo,
      });

      setToastMsg(`Requisition ${confirmReq.requisition_id} confirmed and approved for dispatch!`);
      setTimeout(() => setToastMsg(null), 4000);
      setConfirmReq(null);
      loadRequisitions();
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to confirm requisition.");
    } finally {
      setIsProcessing(false);
    }
  };

  const handleDeclineRequest = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!declineReq) return;
    setIsProcessing(true);
    try {
      await declineRequisition(declineReq.requisition_id, {
        rejection_reason: declineReason,
        rejected_by: `General Manager (Materials, ${activeCpse})`,
      });

      setToastMsg(`Requisition ${declineReq.requisition_id} declined. Stock reservation released.`);
      setTimeout(() => setToastMsg(null), 4000);
      setDeclineReq(null);
      loadRequisitions();
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to decline requisition.");
    } finally {
      setIsProcessing(false);
    }
  };

  // Filter requisitions
  const filteredRequisitions = requisitions.filter((req) => {
    // Tab filter
    if (activeTab === "INBOUND" && req.target_cpse !== activeCpse) return false;
    if (activeTab === "OUTBOUND" && req.source_cpse !== activeCpse) return false;

    // Status filter
    if (statusFilter !== "ALL" && req.status !== statusFilter) return false;

    // Search query
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const matchId = req.requisition_id.toLowerCase().includes(q);
      const matchDesc = req.item_description.toLowerCase().includes(q);
      const matchSku = req.sku_code.toLowerCase().includes(q);
      const matchSource = req.source_depot.toLowerCase().includes(q);
      const matchTarget = req.target_depot.toLowerCase().includes(q);
      if (!matchId && !matchDesc && !matchSku && !matchSource && !matchTarget) return false;
    }

    return true;
  });

  // KPI calculations
  const inboundCount = requisitions.filter((r) => r.target_cpse === activeCpse).length;
  const outboundCount = requisitions.filter((r) => r.source_cpse === activeCpse).length;
  const pendingActionCount = requisitions.filter(
    (r) => r.target_cpse === activeCpse && r.status === "PENDING_APPROVAL"
  ).length;
  const inTransitCount = requisitions.filter((r) => r.status === "IN_TRANSIT").length;

  return (
    <div className="space-y-6">
      {/* Toast Alert */}
      {toastMsg && (
        <div className="fixed top-4 right-4 z-50 p-3 rounded-lg bg-emerald-600 text-white shadow-lg text-xs font-medium flex items-center gap-2 animate-in slide-in-from-top-2">
          <CheckCircle2 className="w-4 h-4" />
          <span>{toastMsg}</span>
        </div>
      )}

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold text-[var(--text-primary)]">
            Procurement Requisitions & Live Tracking
          </h1>
          <p className="text-xs text-[var(--text-secondary)] mt-1">
            Manage inbound facility supply confirmations, monitor outbound procurement indents, and track cross-CPSE transit milestones in real time.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Link href="/discover" className="btn-primary py-2 px-3 text-xs">
            <Send className="w-3.5 h-3.5" />
            <span>New Indent Request</span>
          </Link>
          <button
            onClick={loadRequisitions}
            disabled={loading}
            className="btn-secondary py-2 px-2.5 text-xs"
            title="Refresh Requisitions"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
          </button>
        </div>
      </div>

      {/* KPI Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <KpiCard
          label="Total Indents"
          value={requisitions.length}
          subtitle="All inter-CPSE indents"
          icon={<Package className="w-4 h-4 text-blue-500" />}
          accent="blue"
        />
        <KpiCard
          label="Inbound Facility Requests"
          value={inboundCount}
          subtitle={`Targeted at ${activeCpse}`}
          icon={<Building2 className="w-4 h-4 text-purple-500" />}
          accent="purple"
        />
        <KpiCard
          label="Action Required"
          value={pendingActionCount}
          subtitle="Pending supply confirmation"
          icon={<AlertTriangle className="w-4 h-4 text-amber-500" />}
          accent="amber"
        />
        <KpiCard
          label="In Transit Fleet"
          value={inTransitCount}
          subtitle="Active interstate road/rail"
          icon={<Truck className="w-4 h-4 text-emerald-500" />}
          accent="green"
        />
      </div>

      {/* Filter Tabs & Toolbar */}
      <Card padding="sm">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-3">
          {/* Tabs */}
          <div className="flex items-center gap-1 p-1 bg-[var(--bg-tertiary)] rounded-lg text-xs font-semibold">
            <button
              onClick={() => setActiveTab("ALL")}
              className={`px-3 py-1.5 rounded-md transition-all cursor-pointer ${
                activeTab === "ALL"
                  ? "bg-[var(--bg-secondary)] text-[var(--text-primary)] shadow-xs"
                  : "text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
              }`}
            >
              All Requests ({requisitions.length})
            </button>
            <button
              onClick={() => setActiveTab("INBOUND")}
              className={`px-3 py-1.5 rounded-md transition-all cursor-pointer flex items-center gap-1.5 ${
                activeTab === "INBOUND"
                  ? "bg-[var(--bg-secondary)] text-[var(--text-primary)] shadow-xs"
                  : "text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
              }`}
            >
              <span>Received Requests (Inbound)</span>
              {pendingActionCount > 0 && (
                <span className="w-4 h-4 rounded-full bg-amber-500 text-white text-[10px] flex items-center justify-center font-bold">
                  {pendingActionCount}
                </span>
              )}
            </button>
            <button
              onClick={() => setActiveTab("OUTBOUND")}
              className={`px-3 py-1.5 rounded-md transition-all cursor-pointer ${
                activeTab === "OUTBOUND"
                  ? "bg-[var(--bg-secondary)] text-[var(--text-primary)] shadow-xs"
                  : "text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
              }`}
            >
              Sent Requests (Outbound) ({outboundCount})
            </button>
          </div>

          {/* Filters */}
          <div className="flex items-center gap-2">
            <div className="relative flex-1 sm:w-60">
              <Search className="w-3.5 h-3.5 absolute left-2.5 top-2.5 text-[var(--text-muted)]" />
              <input
                type="text"
                placeholder="Search ID, SKU, desc, depot..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="app-input w-full pl-8 text-xs"
              />
            </div>

            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="app-input text-xs cursor-pointer"
            >
              <option value="ALL">All Statuses</option>
              <option value="PENDING_APPROVAL">Pending Confirmation</option>
              <option value="APPROVED_FOR_DISPATCH">Approved for Dispatch</option>
              <option value="IN_TRANSIT">In Transit</option>
              <option value="DELIVERED">Delivered</option>
              <option value="REJECTED">Declined</option>
            </select>
          </div>
        </div>
      </Card>

      {/* Requisitions List */}
      <Card padding="none">
        {loading ? (
          <div className="py-20 flex flex-col items-center justify-center space-y-2">
            <RefreshCw className="w-6 h-6 text-[var(--accent-primary)] animate-spin" />
            <div className="text-xs text-[var(--text-secondary)]">Loading requisitions and tracking state...</div>
          </div>
        ) : filteredRequisitions.length === 0 ? (
          <div className="p-8">
            <EmptyState
              title="No Requisitions Found"
              description="No transfer requisitions match the selected tab or status filter."
              action={
                <Link href="/discover" className="btn-primary text-xs py-1.5 px-3">
                  Discover Spares to Indent
                </Link>
              }
            />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-[var(--bg-tertiary)] text-[var(--text-secondary)] font-semibold border-b border-[var(--border-primary)]">
                <tr>
                  <th className="py-2.5 px-4">Indent ID & Date</th>
                  <th className="py-2.5 px-3">Material Specification</th>
                  <th className="py-2.5 px-3">Transfer Corridor</th>
                  <th className="py-2.5 px-3 text-right">Qty & Value</th>
                  <th className="py-2.5 px-3 text-center">Live Status</th>
                  <th className="py-2.5 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--border-subtle)] bg-[var(--bg-secondary)]">
                {filteredRequisitions.map((req) => {
                  const isTargetFacility = req.target_cpse === activeCpse;
                  const isSourceRequester = req.source_cpse === activeCpse;
                  const isPending = req.status === "PENDING_APPROVAL";

                  return (
                    <tr key={req.requisition_id} className="hover:bg-[var(--bg-tertiary)]/50 transition-colors">
                      {/* ID & Date */}
                      <td className="py-3 px-4">
                        <Link
                          href={`/requests/${req.requisition_id}`}
                          className="font-mono font-bold text-[var(--accent-primary)] hover:underline block"
                        >
                          {req.requisition_id}
                        </Link>
                        <div className="text-[10px] text-[var(--text-muted)] font-mono mt-0.5">
                          {formatDateTime(req.created_at)}
                        </div>
                        {isTargetFacility && (
                          <span className="inline-block mt-1 text-[9px] uppercase font-bold px-1.5 py-0.2 rounded bg-purple-50 dark:bg-purple-950/40 text-purple-700 dark:text-purple-300 border border-purple-200 dark:border-purple-800">
                            Inbound To My Depot
                          </span>
                        )}
                      </td>

                      {/* Material Spec */}
                      <td className="py-3 px-3 max-w-[280px]">
                        <div className="font-bold text-[var(--text-primary)] truncate" title={req.item_description}>
                          {req.item_description}
                        </div>
                        <div className="text-[10px] text-[var(--text-muted)] font-mono mt-0.5">
                          SKU: {req.sku_code}
                        </div>
                        <div className="text-[10px] text-[var(--text-secondary)] italic truncate mt-0.5">
                          &quot;{req.justification}&quot;
                        </div>
                      </td>

                      {/* Corridor */}
                      <td className="py-3 px-3 text-[11px]">
                        <div className="flex items-center gap-1 font-semibold text-[var(--text-primary)]">
                          <span className="text-[var(--accent-primary)]">{req.source_cpse}</span>
                          <ArrowRight className="w-3 h-3 text-[var(--text-muted)]" />
                          <span className="text-purple-600 dark:text-purple-400">{req.target_cpse}</span>
                        </div>
                        <div className="text-[10px] text-[var(--text-muted)] truncate max-w-[200px] mt-0.5">
                          From: {req.source_depot.split(",")[0]}
                        </div>
                        <div className="text-[10px] text-[var(--text-muted)] truncate max-w-[200px]">
                          To: {req.target_depot.split(",")[0]}
                        </div>
                      </td>

                      {/* Qty & Valuation */}
                      <td className="py-3 px-3 text-right font-mono">
                        <div className="font-bold text-sm text-[var(--text-primary)]">
                          {req.required_qty} Units
                        </div>
                        <div className="text-[11px] font-semibold text-[var(--accent-primary)]">
                          {formatInr(req.total_value_inr)}
                        </div>
                      </td>

                      {/* Status */}
                      <td className="py-3 px-3 text-center">
                        <StatusBadge status={req.status} />
                        {req.gate_pass && (
                          <div className="text-[9px] font-mono text-emerald-600 dark:text-emerald-400 mt-1">
                            {req.gate_pass.gate_pass_no}
                          </div>
                        )}
                      </td>

                      {/* Actions */}
                      <td className="py-3 px-4 text-right">
                        <div className="flex items-center justify-end gap-1.5">
                          {/* Facility Confirmation / Decline buttons for targeted facility */}
                          {isTargetFacility && isPending ? (
                            <>
                              <button
                                onClick={() => setConfirmReq(req)}
                                className="btn-primary py-1 px-2.5 text-[11px] bg-emerald-600 hover:bg-emerald-700"
                                title="Confirm ability to supply this spare part"
                              >
                                <CheckCircle2 className="w-3 h-3" />
                                <span>Confirm Supply</span>
                              </button>
                              <button
                                onClick={() => setDeclineReq(req)}
                                className="btn-secondary py-1 px-2 text-[11px] text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/40 border-rose-200 dark:border-rose-800"
                                title="Decline requisition"
                              >
                                <XCircle className="w-3 h-3" />
                                <span>Decline</span>
                              </button>
                            </>
                          ) : (
                            <Link
                              href={`/requests/${req.requisition_id}`}
                              className="btn-secondary py-1 px-2.5 text-[11px]"
                            >
                              <span>Track Live</span>
                              <ArrowRight className="w-3 h-3" />
                            </Link>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Facility Supply Confirmation Modal */}
      {confirmReq && (
        <Modal
          isOpen={true}
          onClose={() => setConfirmReq(null)}
          title={`Confirm Supply Ability: ${confirmReq.requisition_id}`}
          subtitle={`Request from ${confirmReq.source_cpse} (${confirmReq.source_depot}) for ${confirmReq.required_qty} units`}
          maxWidth="lg"
        >
          <form onSubmit={handleConfirmSupply} className="space-y-4">
            <div className="p-3 rounded-lg bg-[var(--bg-tertiary)] border border-[var(--border-subtle)] text-xs space-y-1">
              <div className="font-bold text-[var(--text-primary)]">{confirmReq.item_description}</div>
              <div className="text-[11px] text-[var(--text-secondary)] flex justify-between">
                <span>SKU: <strong className="font-mono">{confirmReq.sku_code}</strong></span>
                <span>Valuation: <strong className="font-mono text-[var(--accent-primary)]">{formatInr(confirmReq.total_value_inr)}</strong></span>
              </div>
            </div>

            <div className="p-3 rounded-lg bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 text-xs text-emerald-800 dark:text-emerald-300 leading-relaxed">
              <strong>Confirmation Notice:</strong> By confirming supply, you certify that the physical spare has been inspected in your surplus warehouse bay and locked for outbound interstate transfer. A CISF Electronic Material Gate Pass with SHA-256 seal will be automatically issued.
            </div>

            <div>
              <label className="text-[11px] font-semibold text-[var(--text-secondary)] block mb-1">
                Facility Verification & Supply Notes
              </label>
              <textarea
                rows={2}
                value={confirmNotes}
                onChange={(e) => setConfirmNotes(e.target.value)}
                className="app-input w-full text-xs"
                required
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div>
                <label className="text-[11px] font-semibold text-[var(--text-secondary)] block mb-1">
                  Assigned Vehicle No
                </label>
                <input
                  type="text"
                  value={vehicleNo}
                  onChange={(e) => setVehicleNo(e.target.value)}
                  className="app-input w-full font-mono text-xs"
                  required
                />
              </div>
              <div>
                <label className="text-[11px] font-semibold text-[var(--text-secondary)] block mb-1">
                  Driver Name
                </label>
                <input
                  type="text"
                  value={driverName}
                  onChange={(e) => setDriverName(e.target.value)}
                  className="app-input w-full text-xs"
                  required
                />
              </div>
              <div>
                <label className="text-[11px] font-semibold text-[var(--text-secondary)] block mb-1">
                  Driver License / ID No
                </label>
                <input
                  type="text"
                  value={driverIdNo}
                  onChange={(e) => setDriverIdNo(e.target.value)}
                  className="app-input w-full font-mono text-xs"
                  required
                />
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 pt-2 border-t border-[var(--border-subtle)]">
              <button
                type="button"
                onClick={() => setConfirmReq(null)}
                className="btn-secondary"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isProcessing}
                className="btn-primary bg-emerald-600 hover:bg-emerald-700"
              >
                {isProcessing ? (
                  <>
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                    <span>Issuing Gate Pass...</span>
                  </>
                ) : (
                  <>
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>Confirm Supply & Issue Gate Pass</span>
                  </>
                )}
              </button>
            </div>
          </form>
        </Modal>
      )}

      {/* Facility Decline Modal */}
      {declineReq && (
        <Modal
          isOpen={true}
          onClose={() => setDeclineReq(null)}
          title={`Decline Procurement Requisition: ${declineReq.requisition_id}`}
          subtitle={`Requested by ${declineReq.source_cpse}`}
          maxWidth="md"
        >
          <form onSubmit={handleDeclineRequest} className="space-y-4">
            <div className="p-3 rounded-lg bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800 text-xs text-rose-800 dark:text-rose-300">
              Declining this requisition will immediately release the surplus stock reservation back to available inventory and notify the requesting engineer with your stated reason.
            </div>

            <div>
              <label className="text-[11px] font-semibold text-[var(--text-secondary)] block mb-1">
                Formal Reason for Declining (Required)
              </label>
              <textarea
                rows={3}
                value={declineReason}
                onChange={(e) => setDeclineReason(e.target.value)}
                className="app-input w-full text-xs"
                placeholder="e.g. Item reserved for internal turnaround shutdown maintenance..."
                required
              />
            </div>

            <div className="flex items-center justify-end gap-2 pt-2 border-t border-[var(--border-subtle)]">
              <button
                type="button"
                onClick={() => setDeclineReq(null)}
                className="btn-secondary"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isProcessing}
                className="btn-primary bg-rose-600 hover:bg-rose-700"
              >
                {isProcessing ? (
                  <>
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                    <span>Processing...</span>
                  </>
                ) : (
                  <>
                    <XCircle className="w-3.5 h-3.5" />
                    <span>Decline Requisition</span>
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
