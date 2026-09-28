"use client";

import React, { use, useState, useEffect } from 'react';
import Link from 'next/link';
import { Card, Modal } from '@/components/ui';
import { QRCodeSVG } from '@/components/QRCodeSVG';
import {
  Truck,
  ArrowLeft,
  CheckCircle2,
  Clock,
  ShieldCheck,
  AlertTriangle,
  FileText,
  Building2,
  KeyRound,
  RefreshCw,
  Printer,
  QrCode,
} from 'lucide-react';
import { api } from '@/lib/api';
import { useTheme } from '@/components/ThemeProvider';
import { useAuth } from '@/context/AuthContext';
import { ProtectedRoute } from '@/components/ProtectedRoute';

export default function RequisitionDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const { cpse } = useTheme();
  const { user } = useAuth();

  const [req, setReq] = useState<any | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState<boolean>(false);
  const [actionMessage, setActionMessage] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  // Modals
  const [rejectModalOpen, setRejectModalOpen] = useState<boolean>(false);
  const [rejectReason, setRejectReason] = useState<string>('Material currently earmarked for local maintenance shutdown');

  const [gatePassModalOpen, setGatePassModalOpen] = useState<boolean>(false);
  const [gatePassForm, setGatePassForm] = useState({
    vehicle_no: 'AS-01-EA-4102',
    driver_name: 'B. K. Sharma',
    driver_id: 'DL-04201988102',
    transporter_name: 'CONCOR Heavy Logistics',
  });

  const fetchDetail = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getRequestById(id);
      setReq(data);
    } catch (err: any) {
      setError(err.message || `Requisition ${id} not found.`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDetail();
  }, [id]);

  const handleApprove = async () => {
    setActionLoading(true);
    setActionMessage(null);
    setActionError(null);
    try {
      await api.approveRequisition(id, { approved_by: user?.username || 'SYSTEM_OFFICER' });
      setActionMessage('Requisition approved successfully.');
      fetchDetail();
    } catch (err: any) {
      setActionError(`Approval error: ${err.message}`);
    } finally {
      setActionLoading(false);
    }
  };

  const handleConfirmReject = async () => {
    setActionLoading(true);
    setActionMessage(null);
    setActionError(null);
    try {
      await api.rejectRequisition(id, { reason: rejectReason.trim() || 'Declined by Materials Authority' });
      setActionMessage('Requisition rejected.');
      setRejectModalOpen(false);
      fetchDetail();
    } catch (err: any) {
      setActionError(`Rejection error: ${err.message}`);
    } finally {
      setActionLoading(false);
    }
  };

  const handleConfirmGatePass = async () => {
    setActionLoading(true);
    setActionMessage(null);
    setActionError(null);
    try {
      const res = await api.generateGatePass(id, {
        pass_type: 'NON-RETURNABLE-MUTUAL-AID',
        issuing_officer: `${user?.username || 'CISF_OFFICER'} (${user?.role || 'CISF_SECURITY'})`,
        vehicle_no: gatePassForm.vehicle_no,
        driver_name: gatePassForm.driver_name,
        driver_id: gatePassForm.driver_id,
        transporter_name: gatePassForm.transporter_name,
      });
      setActionMessage(`CISF Gate Pass ${res.gate_pass_no || ''} generated with cryptographic seal.`);
      setGatePassModalOpen(false);
      fetchDetail();
    } catch (err: any) {
      setActionError(`Gate pass issuance error: ${err.message}`);
    } finally {
      setActionLoading(false);
    }
  };

  const handleDispatch = async () => {
    setActionLoading(true);
    setActionMessage(null);
    setActionError(null);
    try {
      await api.dispatchRequisition(id);
      setActionMessage('Requisition marked as DISPATCHED.');
      fetchDetail();
    } catch (err: any) {
      setActionError(`Dispatch error: ${err.message}`);
    } finally {
      setActionLoading(false);
    }
  };

  const handleDeliver = async () => {
    setActionLoading(true);
    setActionMessage(null);
    setActionError(null);
    try {
      await api.deliverRequisition(id);
      setActionMessage('Consignment confirmed as DELIVERED.');
      fetchDetail();
    } catch (err: any) {
      setActionError(`Delivery confirmation error: ${err.message}`);
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <ProtectedRoute allowedRoles={['SITE_ENGINEER', 'MATERIALS_MANAGER', 'TECHNICAL_AUTHORITY', 'CISF_SECURITY', 'VIGILANCE_AUDITOR', 'SUPER_ADMIN']}>
      {loading ? (
        <div className="py-24 text-center text-xs font-mono text-zinc-400">
          <RefreshCw className="animate-spin h-5 w-5 mx-auto mb-2 text-zinc-500" />
          <span>Loading requisition {id} from database...</span>
        </div>
      ) : error || !req ? (
        <div className="max-w-2xl mx-auto py-12 text-center text-xs font-mono">
          <div className="p-4 bg-rose-500/10 border border-rose-500/20 rounded-lg text-rose-700 dark:text-rose-400 mb-4">
            {error || `Requisition ${id} not found.`}
          </div>
          <Link href="/requests" className="text-zinc-900 dark:text-zinc-100 hover:underline">
            &larr; Back to Consignments Hub
          </Link>
        </div>
      ) : (() => {
        const currentStatus = req.status || 'REQUESTED';
        const isPending = currentStatus === 'PENDING_APPROVAL' || currentStatus === 'REQUESTED';
        const stages = ['REQUESTED', 'APPROVED', 'GATE_PASS_ISSUED', 'DISPATCHED', 'DELIVERED'];
        const currentStageIndex = stages.indexOf(currentStatus);

        const isSuperAdmin = user?.role === 'SUPER_ADMIN';
        const isRequester = user?.username === req.requested_by;
        const isSupplyingDepot = user?.cpse === req.source_cpse;
        const isReceivingDepot = user?.cpse === (req.target_cpse || req.requesting_cpse);

        const qrData = JSON.stringify({
          req_id: req.requisition_id || id,
          sku: req.sku_code,
          qty: req.required_qty,
          origin: req.source_cpse,
          dest: req.target_cpse || req.requesting_cpse,
          gate_pass: req.gate_pass_id || req.gate_pass?.gate_pass_no || 'PENDING',
          sha256: (req.audit_hash || '').slice(0, 16),
        });

        return (
          <div className="space-y-4 max-w-7xl mx-auto pb-10">
            {/* Top Bar */}
            <div className="flex flex-wrap items-center justify-between gap-3 bg-white dark:bg-zinc-900 p-4 rounded-lg border border-zinc-200 dark:border-zinc-800 transition-colors">
              <div className="flex items-center gap-3">
                <Link
                  href="/requests"
                  className="p-1.5 hover:bg-zinc-100 dark:hover:bg-zinc-800 rounded-md text-zinc-400 hover:text-zinc-700 dark:hover:text-zinc-200 transition-colors"
                  title="Back to Requisitions"
                >
                  <ArrowLeft size={16} />
                </Link>
                <div>
                  <div className="flex items-center gap-2">
                    <h1 className="text-sm font-semibold font-mono text-zinc-900 dark:text-zinc-100">
                      {req.requisition_id || `REQ-${id}`}
                    </h1>
                    <span className="px-1.5 py-0.5 rounded text-[10px] font-mono font-medium bg-zinc-100 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 border border-zinc-200 dark:border-zinc-700">
                      {currentStatus.replace(/_/g, ' ')}
                    </span>
                  </div>
                  <p className="text-xs font-mono text-zinc-500 mt-0.5">
                    {req.source_cpse} &rarr; {req.target_cpse || req.requesting_cpse} · {new Date(req.created_at || Date.now()).toLocaleDateString('en-IN')}
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-2">
                {isPending && (
                  <>
                    {isRequester && !isSuperAdmin ? (
                      <span
                        className="px-2.5 py-1 bg-zinc-100 dark:bg-zinc-800 text-zinc-400 rounded-md text-xs font-mono cursor-not-allowed"
                        title="Segregation of Duties: Requesters cannot approve their own requisitions."
                      >
                        Awaiting Stores Approval
                      </span>
                    ) : (isSupplyingDepot || isSuperAdmin) ? (
                      <div className="flex items-center gap-1.5">
                        <button
                          onClick={handleApprove}
                          disabled={actionLoading}
                          className="px-2.5 py-1 bg-emerald-600 hover:bg-emerald-700 text-white rounded-md text-xs font-medium transition-colors disabled:opacity-50"
                        >
                          Approve Requisition
                        </button>
                        <button
                          onClick={() => setRejectModalOpen(true)}
                          disabled={actionLoading}
                          className="px-2.5 py-1 bg-zinc-100 hover:bg-zinc-200 dark:bg-zinc-800 dark:hover:bg-zinc-700 text-rose-600 rounded-md text-xs font-medium transition-colors disabled:opacity-50"
                        >
                          Reject
                        </button>
                      </div>
                    ) : (
                      <span className="text-xs text-zinc-400 font-mono">In Review</span>
                    )}
                  </>
                )}

                {currentStatus === 'APPROVED' && (
                  <>
                    {(isSupplyingDepot || isSuperAdmin) ? (
                      <button
                        onClick={() => setGatePassModalOpen(true)}
                        disabled={actionLoading}
                        className="px-2.5 py-1 bg-purple-600 hover:bg-purple-700 text-white rounded-md text-xs font-medium transition-colors disabled:opacity-50 flex items-center gap-1.5"
                      >
                        <QrCode size={13} />
                        <span>Issue CISF Gate Pass</span>
                      </button>
                    ) : (
                      <span className="text-xs text-zinc-400 font-mono">Approved</span>
                    )}
                  </>
                )}

                {currentStatus === 'GATE_PASS_ISSUED' && (
                  <>
                    {(isSupplyingDepot || isSuperAdmin) ? (
                      <button
                        onClick={handleDispatch}
                        disabled={actionLoading}
                        className="px-2.5 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded-md text-xs font-medium transition-colors disabled:opacity-50 flex items-center gap-1.5"
                      >
                        <Truck size={13} />
                        <span>Confirm Dispatch</span>
                      </button>
                    ) : (
                      <span className="text-xs text-zinc-400 font-mono">Gate Pass Issued</span>
                    )}
                  </>
                )}

                {currentStatus === 'DISPATCHED' && (
                  <>
                    {(isReceivingDepot || isRequester || isSuperAdmin) ? (
                      <button
                        onClick={handleDeliver}
                        disabled={actionLoading}
                        className="px-2.5 py-1 bg-emerald-600 hover:bg-emerald-700 text-white rounded-md text-xs font-medium transition-colors disabled:opacity-50 flex items-center gap-1.5"
                      >
                        <CheckCircle2 size={13} />
                        <span>Confirm Receipt & Reconcile</span>
                      </button>
                    ) : (
                      <span className="text-xs text-zinc-400 font-mono">In Transit</span>
                    )}
                  </>
                )}

                <button
                  onClick={() => window.print()}
                  className="px-2.5 py-1 bg-zinc-100 dark:bg-zinc-800 hover:bg-zinc-200 dark:hover:bg-zinc-750 text-zinc-700 dark:text-zinc-300 rounded-md text-xs font-medium flex items-center gap-1.5 no-print transition-colors"
                >
                  <Printer size={12} />
                  <span>Print Pass</span>
                </button>
              </div>
            </div>

            {actionMessage && (
              <div className="p-2.5 bg-emerald-500/10 border border-emerald-500/20 text-emerald-700 dark:text-emerald-400 text-xs font-mono rounded-lg flex items-center justify-between">
                <span>{actionMessage}</span>
                <button onClick={() => setActionMessage(null)} className="text-zinc-400 hover:text-zinc-600">&times;</button>
              </div>
            )}

            {actionError && (
              <div className="p-2.5 bg-rose-500/10 border border-rose-500/20 text-rose-700 dark:text-rose-400 text-xs font-mono rounded-lg flex items-center justify-between">
                <span>{actionError}</span>
                <button onClick={() => setActionError(null)} className="text-zinc-400 hover:text-zinc-600">&times;</button>
              </div>
            )}

        {/* Workflow Progression Stepper */}
        <div className="p-4 bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-lg">
          <h2 className="text-[11px] font-mono font-semibold uppercase tracking-wider text-zinc-400 mb-3">
            Transfer Lifecycle Milestones
          </h2>

          <div className="grid grid-cols-1 sm:grid-cols-5 gap-2 text-xs font-mono">
            {[
              { stage: 'REQUESTED', label: '1. Logged', desc: 'Requisition broadcast' },
              { stage: 'APPROVED', label: '2. Approved', desc: 'Material clearance' },
              { stage: 'GATE_PASS_ISSUED', label: '3. Gate Pass', desc: 'CISF authorization' },
              { stage: 'DISPATCHED', label: '4. Dispatched', desc: 'In-transit carrier' },
              { stage: 'DELIVERED', label: '5. Delivered', desc: 'Ledger reconciled' },
            ].map((s, idx) => {
              const isDone = currentStageIndex >= idx;
              const isCurrent = currentStageIndex === idx;

              return (
                <div
                  key={s.stage}
                  className={`p-2.5 rounded-md border ${
                    isCurrent
                      ? 'border-zinc-900 dark:border-zinc-100 bg-zinc-100/50 dark:bg-zinc-800/50 font-medium'
                      : isDone
                      ? 'border-zinc-200 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-850'
                      : 'border-zinc-100 dark:border-zinc-850 opacity-40'
                  }`}
                >
                  <div className="flex items-center gap-1.5 mb-1">
                    {isDone ? (
                      <CheckCircle2 size={13} className="text-emerald-500 shrink-0" />
                    ) : (
                      <Clock size={13} className="text-zinc-400 shrink-0" />
                    )}
                    <span className="text-zinc-900 dark:text-zinc-100">{s.label}</span>
                  </div>
                  <p className="text-[10px] text-zinc-500">{s.desc}</p>
                </div>
              );
            })}
          </div>
        </div>

        {/* Main Details Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
          {/* Requisition Parameters */}
          <div className="lg:col-span-7 p-4 bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-lg space-y-3">
            <h2 className="text-xs font-mono font-semibold uppercase tracking-wider text-zinc-400 pb-2 border-b border-zinc-100 dark:border-zinc-800">
              Material Specification & Transfer Details
            </h2>

            <div className="grid grid-cols-2 gap-2 text-xs font-mono">
              <div className="p-2.5 bg-zinc-50 dark:bg-zinc-800/50 rounded border border-zinc-200 dark:border-zinc-700/80">
                <span className="text-zinc-400 block text-[10px]">Material SKU</span>
                <span className="font-semibold text-zinc-900 dark:text-zinc-100">{req.sku_code}</span>
              </div>

              <div className="p-2.5 bg-zinc-50 dark:bg-zinc-800/50 rounded border border-zinc-200 dark:border-zinc-700/80">
                <span className="text-zinc-400 block text-[10px]">Required Quantity</span>
                <span className="font-semibold text-zinc-900 dark:text-zinc-100">{req.required_qty} Units</span>
              </div>

              <div className="p-2.5 bg-zinc-50 dark:bg-zinc-800/50 rounded border border-zinc-200 dark:border-zinc-700/80">
                <span className="text-zinc-400 block text-[10px]">Fulfilling Node (Source)</span>
                <span className="font-semibold text-zinc-900 dark:text-zinc-100">{req.source_cpse}</span>
              </div>

              <div className="p-2.5 bg-zinc-50 dark:bg-zinc-800/50 rounded border border-zinc-200 dark:border-zinc-700/80">
                <span className="text-zinc-400 block text-[10px]">Requesting Node</span>
                <span className="font-semibold text-zinc-900 dark:text-zinc-100">{req.requesting_cpse}</span>
              </div>

              <div className="p-2.5 bg-zinc-50 dark:bg-zinc-800/50 rounded border border-zinc-200 dark:border-zinc-700/80 col-span-2">
                <span className="text-zinc-400 block text-[10px]">Target Receiving Depot</span>
                <span className="font-medium text-zinc-800 dark:text-zinc-200">{req.target_depot || 'Central Engineering Stores'}</span>
              </div>

              <div className="p-2.5 bg-zinc-50 dark:bg-zinc-800/50 rounded border border-zinc-200 dark:border-zinc-700/80 col-span-2">
                <span className="text-zinc-400 block text-[10px]">Operational Justification</span>
                <p className="text-zinc-800 dark:text-zinc-200 mt-0.5 font-sans">{req.justification || 'Mutual aid spare transfer under MoPNG sovereign mesh directive.'}</p>
              </div>
            </div>

            <div className="pt-2 border-t border-zinc-100 dark:border-zinc-800 text-[11px] font-mono text-zinc-400 flex items-center justify-between">
              <span>Cryptographic Block Reference:</span>
              <span className="text-zinc-600 dark:text-zinc-300 truncate max-w-[220px]">
                {req.audit_hash || '0x4f82...c10b (SHA-256)'}
              </span>
            </div>
          </div>

          {/* CISF Gate Pass & QR Clearance */}
          <div className="lg:col-span-5 p-4 bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-lg flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between pb-2 border-b border-zinc-100 dark:border-zinc-800 mb-3">
                <h2 className="text-xs font-mono font-semibold uppercase tracking-wider text-zinc-400 flex items-center gap-1.5">
                  <ShieldCheck size={14} className="text-emerald-500" />
                  CISF Security Gate Pass
                </h2>
              </div>

              <div className="flex flex-col items-center justify-center p-3 bg-zinc-50 dark:bg-zinc-800/50 rounded-lg border border-zinc-200 dark:border-zinc-700/80 mb-3">
                <div className="p-2 bg-white rounded border border-zinc-200 mb-2">
                  <QRCodeSVG value={qrData} size={120} />
                </div>
                <span className="text-[10px] font-mono text-zinc-400">
                  Air-gapped biometric & QR gate verification
                </span>
              </div>

              <div className="space-y-1.5 text-xs font-mono">
                <div className="flex justify-between py-1 border-b border-zinc-100 dark:border-zinc-800">
                  <span className="text-zinc-400">Gate Pass ID:</span>
                  <span className="font-semibold text-zinc-900 dark:text-zinc-100">
                    {req.gate_pass_id || `GP-NR-${req.requisition_id || id}`}
                  </span>
                </div>
                <div className="flex justify-between py-1 border-b border-zinc-100 dark:border-zinc-800">
                  <span className="text-zinc-400">Classification:</span>
                  <span className="text-zinc-800 dark:text-zinc-200">
                    NON-RETURNABLE MUTUAL AID
                  </span>
                </div>
                <div className="flex justify-between py-1 border-b border-zinc-100 dark:border-zinc-800">
                  <span className="text-zinc-400">Carrier Vehicle:</span>
                  <span className="text-zinc-800 dark:text-zinc-200">
                    {req.vehicle_reg || 'AS-01-EA-4102'}
                  </span>
                </div>
                <div className="flex justify-between py-1 border-b border-zinc-100 dark:border-zinc-800">
                  <span className="text-zinc-400">Security Clearance:</span>
                  <span className="text-emerald-600 dark:text-emerald-400 font-semibold">
                    DIGITALLY AUTHORIZED
                  </span>
                </div>
              </div>
            </div>

            <div className="pt-3 border-t border-zinc-100 dark:border-zinc-800 text-[10px] font-mono text-zinc-400 text-center">
              MoPNG Sovereign Inter-CPSE Material Protocol
            </div>
          </div>
        </div>

        {/* Rejection Reason Modal */}
        <Modal
          isOpen={rejectModalOpen}
          onClose={() => setRejectModalOpen(false)}
          title={`Decline Requisition ${req.requisition_id || id}`}
        >
          <div className="space-y-4 text-xs font-sans">
            <p className="text-zinc-600 dark:text-zinc-400">
              Please enter the official justification for declining this inter-CPSE requisition. This rationale will be permanently recorded in the Sovereign Audit Ledger.
            </p>
            <div>
              <label className="block font-medium text-zinc-700 dark:text-zinc-300 mb-1">
                Decline Reason / Remarks
              </label>
              <textarea
                value={rejectReason}
                onChange={(e) => setRejectReason(e.target.value)}
                rows={3}
                className="w-full p-2.5 bg-zinc-50 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded-md text-xs text-zinc-900 dark:text-zinc-100 placeholder:text-zinc-400 outline-hidden font-sans"
                placeholder="State statutory or operational grounds for decline..."
              />
            </div>
            <div className="flex items-center justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setRejectModalOpen(false)}
                className="px-3 py-1.5 rounded-md border border-zinc-200 dark:border-zinc-700 text-zinc-700 dark:text-zinc-300 hover:bg-zinc-100 dark:hover:bg-zinc-800 font-medium"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleConfirmReject}
                disabled={actionLoading}
                className="px-3 py-1.5 rounded-md bg-rose-600 hover:bg-rose-700 text-white font-medium disabled:opacity-50"
              >
                {actionLoading ? 'Declining...' : 'Confirm Rejection'}
              </button>
            </div>
          </div>
        </Modal>

        {/* CISF Digital Gate Pass Logistics Modal */}
        <Modal
          isOpen={gatePassModalOpen}
          onClose={() => setGatePassModalOpen(false)}
          title={`Generate CISF Gate Pass — ${req.requisition_id || id}`}
        >
          <div className="space-y-3.5 text-xs font-sans">
            <p className="text-zinc-600 dark:text-zinc-400">
              Verify logistics, transport vehicle, and driver credentials for dispatch from{' '}
              <strong className="text-zinc-800 dark:text-zinc-200">{req.source_cpse}</strong> stores to{' '}
              <strong className="text-zinc-800 dark:text-zinc-200">{req.target_cpse || req.requesting_cpse}</strong>.
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="block text-[11px] font-medium text-zinc-700 dark:text-zinc-300 mb-1">
                  Vehicle / Trailer Registration No.
                </label>
                <input
                  type="text"
                  value={gatePassForm.vehicle_no}
                  onChange={(e) => setGatePassForm({ ...gatePassForm, vehicle_no: e.target.value })}
                  placeholder="e.g. AS-01-EA-4102"
                  className="w-full px-2.5 py-1.5 bg-zinc-50 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded text-xs font-mono text-zinc-900 dark:text-zinc-100"
                />
              </div>

              <div>
                <label className="block text-[11px] font-medium text-zinc-700 dark:text-zinc-300 mb-1">
                  Transporter / Logistics Operator
                </label>
                <input
                  type="text"
                  value={gatePassForm.transporter_name}
                  onChange={(e) => setGatePassForm({ ...gatePassForm, transporter_name: e.target.value })}
                  placeholder="e.g. CONCOR Heavy Logistics"
                  className="w-full px-2.5 py-1.5 bg-zinc-50 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded text-xs text-zinc-900 dark:text-zinc-100"
                />
              </div>

              <div>
                <label className="block text-[11px] font-medium text-zinc-700 dark:text-zinc-300 mb-1">
                  Designated Driver Full Name
                </label>
                <input
                  type="text"
                  value={gatePassForm.driver_name}
                  onChange={(e) => setGatePassForm({ ...gatePassForm, driver_name: e.target.value })}
                  placeholder="e.g. B. K. Sharma"
                  className="w-full px-2.5 py-1.5 bg-zinc-50 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded text-xs text-zinc-900 dark:text-zinc-100"
                />
              </div>

              <div>
                <label className="block text-[11px] font-medium text-zinc-700 dark:text-zinc-300 mb-1">
                  Driver License / National ID
                </label>
                <input
                  type="text"
                  value={gatePassForm.driver_id}
                  onChange={(e) => setGatePassForm({ ...gatePassForm, driver_id: e.target.value })}
                  placeholder="e.g. DL-04201988102"
                  className="w-full px-2.5 py-1.5 bg-zinc-50 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded text-xs font-mono text-zinc-900 dark:text-zinc-100"
                />
              </div>
            </div>

            <div className="p-2.5 bg-purple-500/10 border border-purple-500/20 text-purple-700 dark:text-purple-300 rounded text-[11px] font-mono">
              Digital Pass Type: <strong>NON-RETURNABLE-MUTUAL-AID</strong> · Cryptographic SHA-256 HMAC Seal will be burned into offline SVG bit-matrix QR code.
            </div>

            <div className="flex items-center justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setGatePassModalOpen(false)}
                className="px-3 py-1.5 rounded-md border border-zinc-200 dark:border-zinc-700 text-zinc-700 dark:text-zinc-300 hover:bg-zinc-100 dark:hover:bg-zinc-800 font-medium"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleConfirmGatePass}
                disabled={actionLoading}
                className="px-3 py-1.5 rounded-md bg-purple-600 hover:bg-purple-700 text-white font-medium flex items-center gap-1.5 disabled:opacity-50"
              >
                <QrCode size={13} />
                <span>{actionLoading ? 'Issuing Pass...' : 'Issue Digital Gate Pass'}</span>
              </button>
            </div>
          </div>
        </Modal>
      </div>
    );
  })()}
</ProtectedRoute>
);
}
