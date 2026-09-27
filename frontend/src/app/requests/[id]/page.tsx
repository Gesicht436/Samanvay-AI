"use client";

import React, { use, useState, useEffect } from 'react';
import Link from 'next/link';
import { Card } from '@/components/ui';
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
    try {
      await api.approveRequisition(id, { approved_by: user?.username || 'SYSTEM_OFFICER' });
      setActionMessage('Requisition approved successfully.');
      fetchDetail();
    } catch (err: any) {
      alert(`Approval error: ${err.message}`);
    } finally {
      setActionLoading(false);
    }
  };

  const handleIssueGatePass = async () => {
    setActionLoading(true);
    setActionMessage(null);
    try {
      await api.generateGatePass(id, {
        pass_type: 'NON-RETURNABLE-MUTUAL-AID',
        issuing_officer: `${user?.username || 'CISF_OFFICER'} (${user?.role || 'CISF_SECURITY'})`,
        vehicle_no: 'AS-01-EA-4102',
        driver_name: 'B. K. Sharma',
        driver_id: 'DL-04201988102',
        transporter_name: 'CONCOR Heavy Logistics',
      });
      setActionMessage('CISF Gate Pass generated with cryptographic seal.');
      fetchDetail();
    } catch (err: any) {
      alert(`Gate pass issuance error: ${err.message}`);
    } finally {
      setActionLoading(false);
    }
  };

  const handleDispatch = async () => {
    setActionLoading(true);
    try {
      await api.dispatchRequisition(id);
      setActionMessage('Requisition marked as DISPATCHED.');
      fetchDetail();
    } catch (err: any) {
      alert(`Dispatch error: ${err.message}`);
    } finally {
      setActionLoading(false);
    }
  };

  const handleDeliver = async () => {
    setActionLoading(true);
    try {
      await api.deliverRequisition(id);
      setActionMessage('Consignment confirmed as DELIVERED.');
      fetchDetail();
    } catch (err: any) {
      alert(`Delivery confirmation error: ${err.message}`);
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) {
    return (
      <ProtectedRoute allowedRoles={['SITE_ENGINEER', 'MATERIALS_MANAGER', 'TECHNICAL_AUTHORITY', 'CISF_SECURITY', 'VIGILANCE_AUDITOR', 'SUPER_ADMIN']}>
        <div className="py-24 text-center text-xs font-mono text-zinc-400">
          <RefreshCw className="animate-spin h-5 w-5 mx-auto mb-2 text-zinc-500" />
          <span>Loading requisition {id} from database...</span>
        </div>
      </ProtectedRoute>
    );
  }

  if (error || !req) {
    return (
      <ProtectedRoute allowedRoles={['SITE_ENGINEER', 'MATERIALS_MANAGER', 'TECHNICAL_AUTHORITY', 'CISF_SECURITY', 'VIGILANCE_AUDITOR', 'SUPER_ADMIN']}>
        <div className="max-w-2xl mx-auto py-12 text-center text-xs font-mono">
          <div className="p-4 bg-rose-500/10 border border-rose-500/20 rounded-lg text-rose-700 dark:text-rose-400 mb-4">
            {error || `Requisition ${id} not found.`}
          </div>
          <Link href="/requests" className="text-zinc-900 dark:text-zinc-100 hover:underline">
            &larr; Back to Consignments Hub
          </Link>
        </div>
      </ProtectedRoute>
    );
  }

  const currentStatus = req.status || 'REQUESTED';
  const stages = ['REQUESTED', 'APPROVED', 'GATE_PASS_ISSUED', 'DISPATCHED', 'DELIVERED'];
  const currentStageIndex = stages.indexOf(currentStatus);

  const qrData = JSON.stringify({
    req_id: req.requisition_id || id,
    sku: req.sku_code,
    qty: req.required_qty,
    origin: req.source_cpse,
    dest: req.requesting_cpse,
    gate_pass: req.gate_pass_id || 'PENDING',
    sha256: (req.audit_hash || '').slice(0, 16),
  });

  return (
    <ProtectedRoute allowedRoles={['SITE_ENGINEER', 'MATERIALS_MANAGER', 'TECHNICAL_AUTHORITY', 'CISF_SECURITY', 'VIGILANCE_AUDITOR', 'SUPER_ADMIN']}>
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
                <span className="px-1.5 py-0.2 rounded text-[10px] font-mono font-medium bg-zinc-100 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 border border-zinc-200 dark:border-zinc-700">
                  {currentStatus}
                </span>
              </div>
              <p className="text-xs font-mono text-zinc-500 mt-0.5">
                {req.source_cpse} &rarr; {req.requesting_cpse} · {new Date(req.created_at || Date.now()).toLocaleDateString('en-IN')}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {currentStatus === 'REQUESTED' && (
              <button
                onClick={handleApprove}
                disabled={actionLoading}
                className="px-2.5 py-1 bg-zinc-900 hover:bg-zinc-800 text-white dark:bg-zinc-100 dark:hover:bg-zinc-200 dark:text-zinc-900 rounded-md text-xs font-medium transition-colors disabled:opacity-50"
              >
                Approve Requisition
              </button>
            )}

            {currentStatus === 'APPROVED' && (
              <button
                onClick={handleIssueGatePass}
                disabled={actionLoading}
                className="px-2.5 py-1 bg-zinc-900 hover:bg-zinc-800 text-white dark:bg-zinc-100 dark:hover:bg-zinc-200 dark:text-zinc-900 rounded-md text-xs font-medium transition-colors disabled:opacity-50"
              >
                Issue CISF Gate Pass
              </button>
            )}

            {currentStatus === 'GATE_PASS_ISSUED' && (
              <button
                onClick={handleDispatch}
                disabled={actionLoading}
                className="px-2.5 py-1 bg-zinc-900 hover:bg-zinc-800 text-white dark:bg-zinc-100 dark:hover:bg-zinc-200 dark:text-zinc-900 rounded-md text-xs font-medium transition-colors disabled:opacity-50"
              >
                Confirm Dispatch
              </button>
            )}

            {currentStatus === 'DISPATCHED' && (
              <button
                onClick={handleDeliver}
                disabled={actionLoading}
                className="px-2.5 py-1 bg-emerald-600 hover:bg-emerald-700 text-white rounded-md text-xs font-medium transition-colors disabled:opacity-50"
              >
                Confirm Receipt & Reconcile
              </button>
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
      </div>
    </ProtectedRoute>
  );
}
