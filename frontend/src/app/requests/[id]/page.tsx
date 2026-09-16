"use client";

import React, { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { Card, CardHeader } from "@/components/ui/Card";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { Timeline } from "@/components/ui/Timeline";
import { Modal } from "@/components/ui/Modal";
import { useTheme } from "@/components/ThemeProvider";
import {
  fetchSingleRequisition,
  confirmRequisition,
  declineRequisition,
  dispatchRequisition,
  deliverRequisition,
  updateTracking,
} from "@/lib/api";
import { formatInr, formatDateTime } from "@/lib/formatters";
import { InterCPSERequisition } from "@/lib/types";
import {
  ArrowLeft,
  Truck,
  Package,
  ShieldCheck,
  CheckCircle2,
  XCircle,
  Clock,
  Printer,
  QrCode,
  Building2,
  RefreshCw,
  AlertCircle,
  Send,
  MapPin,
  FileText,
} from "lucide-react";

export default function RequestDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { activeCpse } = useTheme();

  const reqId = params?.id as string;

  const [requisition, setRequisition] = useState<InterCPSERequisition | null>(null);
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState(false);
  const [toastMsg, setToastMsg] = useState<string | null>(null);

  // Modals
  const [isConfirmModalOpen, setIsConfirmModalOpen] = useState(false);
  const [isDeclineModalOpen, setIsDeclineModalOpen] = useState(false);
  const [isMilestoneModalOpen, setIsMilestoneModalOpen] = useState(false);
  const [isGatePassModalOpen, setIsGatePassModalOpen] = useState(false);

  // Modal form states
  const [confirmNotes, setConfirmNotes] = useState(
    "Part physical condition verified in surplus bay; facility confirmed capability to supply requested quantity."
  );
  const [vehicleNo, setVehicleNo] = useState("GJ-05-AB-7712");
  const [driverName, setDriverName] = useState("Mukesh Singh Parmar");
  const [driverIdNo, setDriverIdNo] = useState("DL-GJ0520210084");
  const [declineReason, setDeclineReason] = useState(
    "Item reserved for imminent internal unit turnaround maintenance."
  );
  const [milestoneTitle, setMilestoneTitle] = useState("Corridor Checkpoint Cleared");
  const [milestoneNotes, setMilestoneNotes] = useState("Vehicle inspected and cleared interstate toll checkpost.");

  useEffect(() => {
    if (reqId) loadRequisition();
  }, [reqId]);

  const loadRequisition = async () => {
    setLoading(true);
    setErrorMsg(null);
    try {
      const data = await fetchSingleRequisition(reqId);
      setRequisition(data);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to load requisition details.");
    } finally {
      setLoading(false);
    }
  };

  const handleConfirmSupply = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!requisition) return;
    setActionLoading(true);
    try {
      const updated = await confirmRequisition(requisition.requisition_id, {
        confirming_officer: `Chief General Manager (Procurement, ${activeCpse})`,
        confirmation_notes: confirmNotes,
        vehicle_no: vehicleNo,
        driver_name: driverName,
        driver_id_no: driverIdNo,
      });
      setRequisition(updated);
      setIsConfirmModalOpen(false);
      setToastMsg("Supply confirmed and Material Gate Pass issued!");
      setTimeout(() => setToastMsg(null), 4000);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to confirm requisition.");
    } finally {
      setActionLoading(false);
    }
  };

  const handleDeclineRequest = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!requisition) return;
    setActionLoading(true);
    try {
      const updated = await declineRequisition(requisition.requisition_id, {
        rejection_reason: declineReason,
        rejected_by: `General Manager (Materials, ${activeCpse})`,
      });
      setRequisition(updated);
      setIsDeclineModalOpen(false);
      setToastMsg("Requisition declined and stock reservation released.");
      setTimeout(() => setToastMsg(null), 4000);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to decline requisition.");
    } finally {
      setActionLoading(false);
    }
  };

  const handleDispatch = async () => {
    if (!requisition) return;
    setActionLoading(true);
    try {
      const updated = await dispatchRequisition(requisition.requisition_id);
      setRequisition(updated);
      setToastMsg("Vehicle cleared outward gate. Consignment is now In Transit!");
      setTimeout(() => setToastMsg(null), 4000);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to dispatch requisition.");
    } finally {
      setActionLoading(false);
    }
  };

  const handleDeliver = async () => {
    if (!requisition) return;
    setActionLoading(true);
    try {
      const updated = await deliverRequisition(requisition.requisition_id);
      setRequisition(updated);
      setToastMsg("Consignment verified and marked as Delivered at site depot!");
      setTimeout(() => setToastMsg(null), 4000);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to confirm delivery.");
    } finally {
      setActionLoading(false);
    }
  };

  const handleAddMilestone = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!requisition) return;
    setActionLoading(true);
    try {
      const updated = await updateTracking(requisition.requisition_id, {
        event: "IN_TRANSIT_UPDATE",
        title: milestoneTitle,
        actor: "CISF / Logistics Corridor Officer",
        actor_cpse: "MoPNG",
        notes: milestoneNotes,
      });
      setRequisition(updated);
      setIsMilestoneModalOpen(false);
      setToastMsg("Transit tracking milestone added to timeline!");
      setTimeout(() => setToastMsg(null), 4000);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to add tracking milestone.");
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="py-24 flex flex-col items-center justify-center space-y-3">
        <RefreshCw className="w-8 h-8 text-[var(--accent-primary)] animate-spin" />
        <div className="text-xs font-semibold text-[var(--text-primary)]">Loading Requisition Tracking...</div>
        <div className="text-[11px] text-[var(--text-secondary)] font-mono">{reqId}</div>
      </div>
    );
  }

  if (!requisition) {
    return (
      <div className="p-8">
        <Card className="text-center py-12 space-y-3">
          <AlertCircle className="w-8 h-8 text-rose-500 mx-auto" />
          <h3 className="text-sm font-bold text-[var(--text-primary)]">Requisition Not Found</h3>
          <p className="text-xs text-[var(--text-secondary)]">Indent ID &apos;{reqId}&apos; could not be retrieved from the central ledger.</p>
          <Link href="/requests" className="btn-primary inline-flex text-xs py-1.5 px-3 mt-2">
            Back to Requests Inbox
          </Link>
        </Card>
      </div>
    );
  }

  const isTargetFacility = requisition.target_cpse === activeCpse;
  const isSourceRequester = requisition.source_cpse === activeCpse;

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Toast Alert */}
      {toastMsg && (
        <div className="fixed top-4 right-4 z-50 p-3 rounded-lg bg-emerald-600 text-white shadow-lg text-xs font-medium flex items-center gap-2 animate-in slide-in-from-top-2">
          <CheckCircle2 className="w-4 h-4" />
          <span>{toastMsg}</span>
        </div>
      )}

      {/* Top Navigation */}
      <div className="flex items-center justify-between">
        <Link
          href="/requests"
          className="inline-flex items-center gap-1.5 text-xs text-[var(--text-secondary)] hover:text-[var(--text-primary)] font-medium transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Requests Inbox</span>
        </Link>
        <div className="flex items-center gap-2">
          <span className="text-xs text-[var(--text-muted)] font-mono">
            Audit Hash: {requisition.audit_hash.substring(0, 16)}...
          </span>
          <button
            onClick={loadRequisition}
            className="p-1 rounded text-[var(--text-muted)] hover:text-[var(--text-primary)] cursor-pointer"
            title="Refresh Tracking"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Header Banner */}
      <Card>
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-mono text-base font-bold text-[var(--accent-primary)]">
                {requisition.requisition_id}
              </span>
              <StatusBadge status={requisition.status} />
              <span className="text-[10px] uppercase font-bold px-1.5 py-0.5 rounded bg-amber-50 dark:bg-amber-950/40 text-amber-700 dark:text-amber-300 border border-amber-200 dark:border-amber-800">
                {requisition.urgency_level.replace("_", " ")}
              </span>
            </div>
            <h2 className="text-sm font-bold text-[var(--text-primary)]">
              {requisition.item_description}
            </h2>
            <div className="text-[11px] text-[var(--text-secondary)] font-mono">
              SKU: {requisition.sku_code} • Issued on: {formatDateTime(requisition.created_at)}
            </div>
          </div>

          {/* Quick Action Buttons */}
          <div className="flex flex-wrap items-center gap-2 shrink-0">
            {/* Facility Confirmation / Decline if PENDING and target facility */}
            {isTargetFacility && requisition.status === "PENDING_APPROVAL" && (
              <>
                <button
                  onClick={() => setIsConfirmModalOpen(true)}
                  disabled={actionLoading}
                  className="btn-primary py-2 px-3 text-xs bg-emerald-600 hover:bg-emerald-700"
                >
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>Confirm Ability to Supply</span>
                </button>
                <button
                  onClick={() => setIsDeclineModalOpen(true)}
                  disabled={actionLoading}
                  className="btn-secondary py-2 px-3 text-xs text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/40 border-rose-200 dark:border-rose-800"
                >
                  <XCircle className="w-3.5 h-3.5" />
                  <span>Decline Request</span>
                </button>
              </>
            )}

            {/* Outward Dispatch button if APPROVED_FOR_DISPATCH */}
            {requisition.status === "APPROVED_FOR_DISPATCH" && (
              <button
                onClick={handleDispatch}
                disabled={actionLoading}
                className="btn-primary py-2 px-3 text-xs bg-indigo-600 hover:bg-indigo-700"
              >
                <Truck className="w-3.5 h-3.5" />
                <span>Log Perimeter Gate Dispatch</span>
              </button>
            )}

            {/* Delivery Confirmation if IN_TRANSIT */}
            {requisition.status === "IN_TRANSIT" && (
              <button
                onClick={handleDeliver}
                disabled={actionLoading}
                className="btn-primary py-2 px-3 text-xs bg-emerald-600 hover:bg-emerald-700"
              >
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>Confirm Material Received at Site</span>
              </button>
            )}

            {/* View Gate Pass if issued */}
            {requisition.gate_pass && (
              <button
                onClick={() => setIsGatePassModalOpen(true)}
                className="btn-secondary py-2 px-3 text-xs"
              >
                <FileText className="w-3.5 h-3.5" />
                <span>CISF Gate Pass</span>
              </button>
            )}
          </div>
        </div>
      </Card>

      {/* Main Grid: Corridor Details + Live Tracking Timeline */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Requisition Parties & Financials */}
        <div className="lg:col-span-5 space-y-4">
          {/* Transfer Parties Card */}
          <Card>
            <CardHeader
              title="Corridor & Enterprise Parties"
              subtitle="Transparent inter-CPSE allocation"
            />
            <div className="space-y-4 text-xs">
              {/* Requesting Party */}
              <div className="p-3 rounded-lg bg-[var(--bg-tertiary)] border border-[var(--border-subtle)] space-y-1">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] uppercase font-bold text-[var(--accent-primary)]">
                    Requesting Facility (Inbound)
                  </span>
                  <span className="font-bold text-[var(--text-primary)]">{requisition.source_cpse}</span>
                </div>
                <div className="font-semibold text-[var(--text-primary)]">{requisition.source_depot}</div>
                <div className="text-[11px] text-[var(--text-secondary)]">{requisition.source_unit}</div>
                <div className="text-[10px] text-[var(--text-muted)] pt-1">
                  Officer: {requisition.requested_by}
                </div>
              </div>

              {/* Supplying Party */}
              <div className="p-3 rounded-lg bg-[var(--bg-tertiary)] border border-[var(--border-subtle)] space-y-1">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] uppercase font-bold text-purple-600 dark:text-purple-400">
                    Supplying Facility (Outbound)
                  </span>
                  <span className="font-bold text-[var(--text-primary)]">{requisition.target_cpse}</span>
                </div>
                <div className="font-semibold text-[var(--text-primary)]">{requisition.target_depot}</div>
                {requisition.approved_by && (
                  <div className="text-[10px] text-emerald-600 dark:text-emerald-400 font-semibold pt-1">
                    Confirmed by: {requisition.approved_by}
                  </div>
                )}
                {requisition.facility_confirmation_note && (
                  <div className="text-[10px] text-[var(--text-secondary)] italic pt-0.5">
                    &quot;{requisition.facility_confirmation_note}&quot;
                  </div>
                )}
              </div>

              {/* Justification */}
              <div>
                <span className="text-[11px] font-bold text-[var(--text-secondary)] block mb-1">
                  Operating Need Justification:
                </span>
                <p className="p-2.5 rounded-lg bg-[var(--bg-tertiary)]/50 border border-[var(--border-subtle)] text-[var(--text-secondary)] italic leading-relaxed">
                  &quot;{requisition.justification}&quot;
                </p>
              </div>

              {/* Rejection notice if declined */}
              {requisition.rejection_reason && (
                <div className="p-3 rounded-lg bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800 text-rose-800 dark:text-rose-300">
                  <div className="font-bold text-[11px]">Reason for Facility Decline:</div>
                  <div className="text-[11px] mt-0.5">{requisition.rejection_reason}</div>
                </div>
              )}
            </div>
          </Card>

          {/* Consignment Valuation */}
          <Card>
            <CardHeader title="Consignment Commercials" />
            <div className="space-y-2 text-xs">
              <div className="flex justify-between py-1 border-b border-[var(--border-subtle)]">
                <span className="text-[var(--text-secondary)]">Allocated Quantity:</span>
                <span className="font-mono font-bold text-[var(--text-primary)]">{requisition.required_qty} Units</span>
              </div>
              <div className="flex justify-between py-1 border-b border-[var(--border-subtle)]">
                <span className="text-[var(--text-secondary)]">Unit Rate (INR):</span>
                <span className="font-mono text-[var(--text-primary)]">{formatInr(requisition.unit_cost_inr)}</span>
              </div>
              <div className="flex justify-between py-1 font-bold text-sm">
                <span className="text-[var(--text-primary)]">Total Stock Value:</span>
                <span className="font-mono text-[var(--accent-primary)]">{formatInr(requisition.total_value_inr)}</span>
              </div>
            </div>
          </Card>

          {/* Transporter Tracking Metadata */}
          {requisition.tracking_carrier && (
            <Card>
              <CardHeader title="Carrier & Dispatch Traceability" />
              <div className="space-y-2 text-xs">
                <div className="flex justify-between">
                  <span className="text-[var(--text-secondary)]">Fleet Carrier:</span>
                  <span className="font-semibold text-[var(--text-primary)]">{requisition.tracking_carrier}</span>
                </div>
                {requisition.tracking_number && (
                  <div className="flex justify-between">
                    <span className="text-[var(--text-secondary)]">Consignment No:</span>
                    <span className="font-mono font-bold text-[var(--accent-primary)]">{requisition.tracking_number}</span>
                  </div>
                )}
                {requisition.estimated_delivery && (
                  <div className="flex justify-between">
                    <span className="text-[var(--text-secondary)]">Est. Site Arrival:</span>
                    <span className="font-mono text-emerald-600 dark:text-emerald-400 font-bold">
                      {formatDateTime(requisition.estimated_delivery)}
                    </span>
                  </div>
                )}
              </div>
            </Card>
          )}
        </div>

        {/* Right Column: Interactive Live Timeline */}
        <div className="lg:col-span-7 space-y-4">
          <Card className="min-h-[500px]">
            <CardHeader
              title="Live Movement Timeline"
              subtitle="Dual-authenticated transparent chain of custody"
              action={
                requisition.status === "IN_TRANSIT" && (
                  <button
                    onClick={() => setIsMilestoneModalOpen(true)}
                    className="btn-secondary text-[11px] py-1 px-2.5"
                  >
                    <span>+ Log Checkpoint</span>
                  </button>
                )
              }
            />

            <div className="py-2">
              <Timeline events={requisition.timeline || []} />
            </div>
          </Card>
        </div>
      </div>

      {/* Facility Supply Confirmation Modal */}
      {isConfirmModalOpen && (
        <Modal
          isOpen={isConfirmModalOpen}
          onClose={() => setIsConfirmModalOpen(false)}
          title={`Confirm Supply Ability: ${requisition.requisition_id}`}
          subtitle={`Requested by ${requisition.source_cpse} (${requisition.source_depot})`}
          maxWidth="lg"
        >
          <form onSubmit={handleConfirmSupply} className="space-y-4">
            <div className="p-3 rounded-lg bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 text-xs text-emerald-800 dark:text-emerald-300 leading-relaxed">
              <strong>Supply Confirmation:</strong> Confirming this requisition will issue an official CISF Electronic Material Gate Pass with SHA-256 seal and advance the transfer to APPROVED_FOR_DISPATCH.
            </div>

            <div>
              <label className="text-[11px] font-semibold text-[var(--text-secondary)] block mb-1">
                Facility Verification & Confirmation Notes
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
                  Driver License ID
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
                onClick={() => setIsConfirmModalOpen(false)}
                className="btn-secondary"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={actionLoading}
                className="btn-primary bg-emerald-600 hover:bg-emerald-700"
              >
                {actionLoading ? (
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
      {isDeclineModalOpen && (
        <Modal
          isOpen={isDeclineModalOpen}
          onClose={() => setIsDeclineModalOpen(false)}
          title={`Decline Procurement Requisition: ${requisition.requisition_id}`}
          subtitle={`Requested by ${requisition.source_cpse}`}
          maxWidth="md"
        >
          <form onSubmit={handleDeclineRequest} className="space-y-4">
            <div className="p-3 rounded-lg bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800 text-xs text-rose-800 dark:text-rose-300">
              Declining this requisition will immediately release the surplus stock reservation back to available inventory and notify the requesting engineer.
            </div>

            <div>
              <label className="text-[11px] font-semibold text-[var(--text-secondary)] block mb-1">
                Formal Reason for Declining
              </label>
              <textarea
                rows={3}
                value={declineReason}
                onChange={(e) => setDeclineReason(e.target.value)}
                className="app-input w-full text-xs"
                required
              />
            </div>

            <div className="flex items-center justify-end gap-2 pt-2 border-t border-[var(--border-subtle)]">
              <button
                type="button"
                onClick={() => setIsDeclineModalOpen(false)}
                className="btn-secondary"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={actionLoading}
                className="btn-primary bg-rose-600 hover:bg-rose-700"
              >
                {actionLoading ? (
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

      {/* Milestone Checkpoint Modal */}
      {isMilestoneModalOpen && (
        <Modal
          isOpen={isMilestoneModalOpen}
          onClose={() => setIsMilestoneModalOpen(false)}
          title="Log Transit Milestone Checkpoint"
          subtitle={`Consignment: ${requisition.requisition_id}`}
          maxWidth="md"
        >
          <form onSubmit={handleAddMilestone} className="space-y-4">
            <div>
              <label className="text-[11px] font-semibold text-[var(--text-secondary)] block mb-1">
                Milestone Title
              </label>
              <input
                type="text"
                value={milestoneTitle}
                onChange={(e) => setMilestoneTitle(e.target.value)}
                className="app-input w-full text-xs"
                required
              />
            </div>

            <div>
              <label className="text-[11px] font-semibold text-[var(--text-secondary)] block mb-1">
                Checkpoint Inspection Notes
              </label>
              <textarea
                rows={3}
                value={milestoneNotes}
                onChange={(e) => setMilestoneNotes(e.target.value)}
                className="app-input w-full text-xs"
                required
              />
            </div>

            <div className="flex items-center justify-end gap-2 pt-2 border-t border-[var(--border-subtle)]">
              <button
                type="button"
                onClick={() => setIsMilestoneModalOpen(false)}
                className="btn-secondary"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={actionLoading}
                className="btn-primary"
              >
                {actionLoading ? "Appending..." : "Append Milestone"}
              </button>
            </div>
          </form>
        </Modal>
      )}

      {/* CISF Gate Pass View Modal */}
      {requisition.gate_pass && isGatePassModalOpen && (
        <Modal
          isOpen={isGatePassModalOpen}
          onClose={() => setIsGatePassModalOpen(false)}
          title="Official CISF Electronic Material Gate Pass"
          subtitle={`Pass No: ${requisition.gate_pass.gate_pass_no}`}
          maxWidth="2xl"
        >
          <div className="space-y-4">
            <div className="printable-card p-4 rounded-lg border border-[var(--border-primary)] bg-white text-slate-900 space-y-4">
              {/* Header */}
              <div className="text-center border-b pb-3">
                <div className="font-bold text-xs uppercase tracking-wider text-slate-600">
                  Government of India • Ministry of Petroleum & Natural Gas
                </div>
                <div className="font-bold text-sm text-slate-900 mt-0.5">
                  CENTRAL INDUSTRIAL SECURITY FORCE (CISF)
                </div>
                <div className="text-[11px] text-slate-700">
                  Non-Returnable Outward Material Gate Pass (Inter-CPSE Movement)
                </div>
              </div>

              {/* Pass Metadata */}
              <div className="grid grid-cols-2 gap-3 text-xs">
                <div>
                  <span className="text-[10px] text-slate-500 block">Gate Pass No:</span>
                  <span className="font-mono font-bold">{requisition.gate_pass.gate_pass_no}</span>
                </div>
                <div>
                  <span className="text-[10px] text-slate-500 block">E-Way Bill No:</span>
                  <span className="font-mono font-bold">{requisition.gate_pass.gst_eway_bill_no}</span>
                </div>
                <div>
                  <span className="text-[10px] text-slate-500 block">Issuing Refinery:</span>
                  <span className="font-semibold">{requisition.gate_pass.issuing_depot} ({requisition.gate_pass.issuing_cpse})</span>
                </div>
                <div>
                  <span className="text-[10px] text-slate-500 block">Receiving Refinery:</span>
                  <span className="font-semibold">{requisition.gate_pass.receiving_depot} ({requisition.gate_pass.receiving_cpse})</span>
                </div>
                <div>
                  <span className="text-[10px] text-slate-500 block">Assigned Transporter & Vehicle:</span>
                  <span className="font-mono font-bold">{requisition.gate_pass.vehicle_no}</span>
                  <span className="text-[10px] text-slate-600 block">{requisition.gate_pass.transporter_name}</span>
                </div>
                <div>
                  <span className="text-[10px] text-slate-500 block">Driver Details:</span>
                  <span>{requisition.gate_pass.driver_name}</span>
                  <span className="text-[10px] text-slate-600 block font-mono">{requisition.gate_pass.driver_id_no}</span>
                </div>
              </div>

              {/* QR and Verification */}
              <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 flex items-center justify-between gap-4">
                <div className="text-xs space-y-1">
                  <div className="font-mono text-[10px] font-bold text-slate-700">
                    CISF Security Seal: {requisition.gate_pass.cisf_verification_seal}
                  </div>
                  <div className="font-mono text-[9px] text-slate-500 truncate max-w-sm">
                    SHA-256: {requisition.gate_pass.sha256_hash}
                  </div>
                  <div className="text-[10px] text-emerald-700 font-bold">
                    ✓ Cleared for Interstate CPSE Road Transit
                  </div>
                </div>

                {requisition.gate_pass.qr_code_svg && (
                  <div
                    className="w-16 h-16 shrink-0 bg-white p-1 rounded border"
                    dangerouslySetInnerHTML={{ __html: requisition.gate_pass.qr_code_svg }}
                  />
                )}
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 pt-2 border-t border-[var(--border-subtle)]">
              <button
                onClick={() => window.print()}
                className="btn-secondary text-xs flex items-center gap-1.5"
              >
                <Printer className="w-3.5 h-3.5" />
                <span>Print Official Gate Pass</span>
              </button>
              <button
                onClick={() => setIsGatePassModalOpen(false)}
                className="btn-primary text-xs"
              >
                Close
              </button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}
