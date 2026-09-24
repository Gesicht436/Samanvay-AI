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
import { ProtectedRoute } from '@/components/ProtectedRoute';

export default function RequisitionDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const { cpse } = useTheme();

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
    try {
      await api.approveRequisition(id, { approved_by: `OFFICER_${cpse}` });
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
    try {
      await api.generateGatePass(id, {
        pass_type: 'NON-RETURNABLE-MUTUAL-AID',
        officer: `CISF_OFFICER_${cpse}`,
        vehicle_reg: 'AS-01-EA-4102',
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
        <div className="py-24 text-center text-xs font-mono text-slate-500">
          <RefreshCw className="animate-spin h-6 w-6 mx-auto mb-2 text-emerald-500" />
          <span>Loading requisition {id} from database...</span>
        </div>
      </ProtectedRoute>
    );
  }

  if (error || !req) {
    return (
      <ProtectedRoute allowedRoles={['SITE_ENGINEER', 'MATERIALS_MANAGER', 'TECHNICAL_AUTHORITY', 'CISF_SECURITY', 'VIGILANCE_AUDITOR', 'SUPER_ADMIN']}>
        <div className="max-w-2xl mx-auto py-12 text-center text-xs font-mono">
          <div className="p-4 bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900 rounded-xl text-rose-800 dark:text-rose-300 mb-4">
            {error || `Requisition ${id} not found.`}
          </div>
          <Link href="/requests" className="text-emerald-600 dark:text-emerald-400 hover:underline">
            &larr; Back to Requisitions Hub
          </Link>
        </div>
      </ProtectedRoute>
    );
  }

  const currentStatus = req.status || 'PENDING';
  const stages = ['PENDING', 'APPROVED', 'GATE_PASS_ISSUED', 'DISPATCHED', 'DELIVERED'];
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
      <div className="flex flex-col space-y-5 max-w-[1400px] mx-auto pb-10">
      {/* Top Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 bg-white dark:bg-slate-900 p-4 rounded-xl border border-slate-200 dark:border-slate-800 shadow-2xs">
        <div className="flex items-center gap-3">
          <Link
            href="/requests"
            className="p-1.5 hover:bg-slate-100 dark:hover:bg-slate-800 rounded text-slate-500 transition-colors"
            title="Back to Requisitions"
          >
            <ArrowLeft size={18} />
          </Link>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-bold font-mono text-slate-900 dark:text-white">
                Requisition {req.requisition_id || id}
              </h1>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-slate-100 dark:bg-slate-800 text-slate-800 dark:text-slate-200">
                {currentStatus}
              </span>
            </div>
            <p className="text-xs font-mono text-slate-500">
              {req.source_cpse} &rarr; {req.requesting_cpse} · Created {new Date(req.created_at || Date.now()).toLocaleString('en-IN')}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {currentStatus === 'PENDING' && (
            <button
              onClick={handleApprove}
              disabled={actionLoading}
              className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded text-xs font-mono font-semibold transition-colors disabled:opacity-50"
            >
              Approve Requisition
            </button>
          )}

          {currentStatus === 'APPROVED' && (
            <button
              onClick={handleIssueGatePass}
              disabled={actionLoading}
              className="px-3 py-1.5 bg-purple-600 hover:bg-purple-700 text-white rounded text-xs font-mono font-semibold transition-colors disabled:opacity-50"
            >
              Issue CISF Gate Pass
            </button>
          )}

          {currentStatus === 'GATE_PASS_ISSUED' && (
            <button
              onClick={handleDispatch}
              disabled={actionLoading}
              className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded text-xs font-mono font-semibold transition-colors disabled:opacity-50"
            >
              Confirm Dispatch
            </button>
          )}

          {currentStatus === 'DISPATCHED' && (
            <button
              onClick={handleDeliver}
              disabled={actionLoading}
              className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded text-xs font-mono font-semibold transition-colors disabled:opacity-50"
            >
              Confirm Receipt & Reconcile
            </button>
          )}

          <button
            onClick={() => window.print()}
            className="px-3 py-1.5 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 border border-slate-300 dark:border-slate-700 rounded text-xs font-mono font-semibold flex items-center gap-1.5 no-print transition-colors"
          >
            <Printer size={13} />
            <span>Print Pass</span>
          </button>
        </div>
      </div>

      {actionMessage && (
        <div className="p-3 bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 text-emerald-800 dark:text-emerald-300 text-xs font-mono rounded-lg flex items-center justify-between">
          <span>{actionMessage}</span>
          <button onClick={() => setActionMessage(null)} className="text-slate-500 hover:text-slate-700">&times;</button>
        </div>
      )}

      {/* Workflow Progression Stepper */}
      <Card className="p-5 border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900">
        <h2 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-500 mb-4">
          Transfer Lifecycle Milestones
        </h2>

        <div className="grid grid-cols-1 sm:grid-cols-5 gap-3 text-xs font-mono">
          {[
            { stage: 'PENDING', label: '1. Logged', desc: 'Requisition initiated' },
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
                className={`p-3 rounded-lg border ${
                  isCurrent
                    ? 'border-emerald-500 bg-emerald-50/50 dark:bg-emerald-950/30'
                    : isDone
                    ? 'border-slate-300 dark:border-slate-700 bg-slate-50/40 dark:bg-slate-800/40'
                    : 'border-slate-200 dark:border-slate-800 opacity-50'
                }`}
              >
                <div className="flex items-center gap-1.5 mb-1">
                  {isDone ? (
                    <CheckCircle2 size={14} className="text-emerald-600 dark:text-emerald-400 shrink-0" />
                  ) : (
                    <Clock size={14} className="text-slate-400 shrink-0" />
                  )}
                  <span className="font-bold text-slate-900 dark:text-white">{s.label}</span>
                </div>
                <p className="text-[11px] text-slate-500">{s.desc}</p>
              </div>
            );
          })}
        </div>
      </Card>

      {/* Main Details Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        {/* Left Column: Requisition Parameters (7 Cols) */}
        <Card className="lg:col-span-7 p-5 border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 space-y-4">
          <h2 className="text-sm font-mono font-bold uppercase tracking-wider text-slate-900 dark:text-white pb-2 border-b border-slate-100 dark:border-slate-800">
            Material Specification & Transfer Details
          </h2>

          <div className="grid grid-cols-2 gap-3 text-xs font-mono">
            <div className="p-3 bg-slate-50 dark:bg-slate-800 rounded border border-slate-200 dark:border-slate-700">
              <span className="text-slate-400 block text-[11px]">Material SKU</span>
              <span className="font-bold text-slate-900 dark:text-white">{req.sku_code}</span>
            </div>

            <div className="p-3 bg-slate-50 dark:bg-slate-800 rounded border border-slate-200 dark:border-slate-700">
              <span className="text-slate-400 block text-[11px]">Required Quantity</span>
              <span className="font-bold text-slate-900 dark:text-white">{req.required_qty} Units</span>
            </div>

            <div className="p-3 bg-slate-50 dark:bg-slate-800 rounded border border-slate-200 dark:border-slate-700">
              <span className="text-slate-400 block text-[11px]">Fulfilling Node (Source)</span>
              <span className="font-bold text-slate-900 dark:text-white">{req.source_cpse}</span>
            </div>

            <div className="p-3 bg-slate-50 dark:bg-slate-800 rounded border border-slate-200 dark:border-slate-700">
              <span className="text-slate-400 block text-[11px]">Requesting Node</span>
              <span className="font-bold text-slate-900 dark:text-white">{req.requesting_cpse}</span>
            </div>

            <div className="p-3 bg-slate-50 dark:bg-slate-800 rounded border border-slate-200 dark:border-slate-700 col-span-2">
              <span className="text-slate-400 block text-[11px]">Target Receiving Depot</span>
              <span className="font-semibold text-slate-800 dark:text-slate-200">{req.target_depot || 'Central Engineering Stores'}</span>
            </div>

            <div className="p-3 bg-slate-50 dark:bg-slate-800 rounded border border-slate-200 dark:border-slate-700 col-span-2">
              <span className="text-slate-400 block text-[11px]">Operational Justification</span>
              <p className="text-slate-800 dark:text-slate-200 mt-0.5">{req.justification || 'Mutual aid spare transfer under MoPNG directive.'}</p>
            </div>
          </div>

          <div className="pt-2 border-t border-slate-100 dark:border-slate-800 text-xs font-mono text-slate-500 flex items-center justify-between">
            <span>Audit Trail Block Reference:</span>
            <span className="font-mono text-emerald-700 dark:text-emerald-400 truncate max-w-[240px]" title={req.audit_hash}>
              {req.audit_hash ? req.audit_hash.slice(0, 24) + '...' : 'Sealed in Genesis Block'}
            </span>
          </div>
        </Card>

        {/* Right Column: CISF Gate Pass & QR Clearance (5 Cols) */}
        <Card className="lg:col-span-5 p-5 border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-2 border-b border-slate-100 dark:border-slate-800 mb-4">
              <h2 className="text-sm font-mono font-bold uppercase tracking-wider text-slate-900 dark:text-white flex items-center gap-1.5">
                <ShieldCheck size={16} className="text-emerald-600 dark:text-emerald-400" />
                CISF Security Clearance Gate Pass
              </h2>
            </div>

            <div className="flex flex-col items-center justify-center p-4 bg-slate-50 dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 mb-4">
              <div className="p-2 bg-white rounded border border-slate-200 shadow-2xs mb-2">
                <QRCodeSVG value={qrData} size={130} />
              </div>
              <span className="text-[10px] font-mono text-slate-500">
                Scan for instant CISF gate biometric verification
              </span>
            </div>

            <div className="space-y-2 text-xs font-mono">
              <div className="flex justify-between py-1 border-b border-slate-100 dark:border-slate-800">
                <span className="text-slate-500">Gate Pass ID:</span>
                <span className="font-bold text-slate-900 dark:text-white">
                  {req.gate_pass_id || `GP-NR-${req.requisition_id || id}`}
                </span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-100 dark:border-slate-800">
                <span className="text-slate-500">Pass Classification:</span>
                <span className="font-semibold text-slate-800 dark:text-slate-200">
                  NON-RETURNABLE MUTUAL AID
                </span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-100 dark:border-slate-800">
                <span className="text-slate-500">Carrier Vehicle:</span>
                <span className="font-semibold text-slate-800 dark:text-slate-200">
                  {req.vehicle_reg || 'AS-01-EA-4102'}
                </span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-100 dark:border-slate-800">
                <span className="text-slate-500">Security Clearance:</span>
                <span className="font-bold text-emerald-700 dark:text-emerald-400">
                  DIGITALLY AUTHORIZED
                </span>
              </div>
            </div>
          </div>

          <div className="pt-4 border-t border-slate-100 dark:border-slate-800 text-[11px] font-mono text-slate-400 text-center">
            Valid under MoPNG Inter-CPSE Material Sharing Protocol
          </div>
        </Card>
      </div>
      </div>
    </ProtectedRoute>
  );
}
