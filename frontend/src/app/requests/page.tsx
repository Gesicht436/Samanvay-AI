"use client";

import React, { useState, useEffect, useMemo } from 'react';
import Link from 'next/link';
import { Card, Skeleton } from '@/components/ui';
import {
  Truck,
  Inbox,
  Clock,
  ShieldCheck,
  Search,
  Filter,
  CheckCircle2,
  XCircle,
  ArrowRight,
  AlertTriangle,
  FileText,
  RefreshCw,
  Plus,
  Send,
  Building2,
  QrCode,
} from 'lucide-react';
import { useTheme } from '@/components/ThemeProvider';
import { api } from '@/lib/api';
import { ProtectedRoute } from '@/components/ProtectedRoute';

interface RequisitionItem {
  id?: string;
  requisition_id: string;
  sku_code: string;
  source_cpse: string;
  requesting_cpse: string;
  target_depot?: string;
  required_qty: number;
  urgency: string;
  status: string;
  justification?: string;
  gate_pass_id?: string;
  created_at?: string;
  audit_hash?: string;
  carrier_name?: string;
  vehicle_reg?: string;
}

export default function RequisitionsListPage() {
  const { cpse } = useTheme();
  const [requests, setRequests] = useState<RequisitionItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [actionLoadingId, setActionLoadingId] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  const fetchRequisitions = async () => {
    setLoading(true);
    setError(null);
    try {
      const res: any = await api.getRequests();
      const list = Array.isArray(res) ? res : res?.items || [];
      setRequests(list);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch requisitions from backend');
      setRequests([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRequisitions();
  }, [cpse]);

  const handleApprove = async (reqId: string) => {
    setActionLoadingId(reqId);
    try {
      await api.approveRequisition(reqId, { approved_by: `GM_MATERIALS_${cpse}` });
      setActionSuccess(`Requisition ${reqId} approved successfully.`);
      fetchRequisitions();
    } catch (err: any) {
      alert(`Approval failed: ${err.message}`);
    } finally {
      setActionLoadingId(null);
    }
  };

  const handleGenerateGatePass = async (reqId: string) => {
    setActionLoadingId(reqId);
    try {
      await api.generateGatePass(reqId, {
        pass_type: 'NON-RETURNABLE-MUTUAL-AID',
        officer: `CISF_INSPECTOR_${cpse}`,
        vehicle_reg: 'AS-01-EA-4102',
      });
      setActionSuccess(`CISF Non-Returnable Gate Pass issued for ${reqId}.`);
      fetchRequisitions();
    } catch (err: any) {
      alert(`Gate pass generation failed: ${err.message}`);
    } finally {
      setActionLoadingId(null);
    }
  };

  const handleDispatch = async (reqId: string) => {
    setActionLoadingId(reqId);
    try {
      await api.dispatchRequisition(reqId);
      setActionSuccess(`Requisition ${reqId} marked as DISPATCHED.`);
      fetchRequisitions();
    } catch (err: any) {
      alert(`Dispatch failed: ${err.message}`);
    } finally {
      setActionLoadingId(null);
    }
  };

  const handleDeliver = async (reqId: string) => {
    setActionLoadingId(reqId);
    try {
      await api.deliverRequisition(reqId);
      setActionSuccess(`Requisition ${reqId} confirmed as DELIVERED & inventory reconciled.`);
      fetchRequisitions();
    } catch (err: any) {
      alert(`Delivery failed: ${err.message}`);
    } finally {
      setActionLoadingId(null);
    }
  };

  const filteredRequests = useMemo(() => {
    if (statusFilter === 'ALL') return requests;
    return requests.filter((r) => r.status?.toUpperCase() === statusFilter.toUpperCase());
  }, [requests, statusFilter]);

  return (
    <ProtectedRoute allowedRoles={['SITE_ENGINEER', 'MATERIALS_MANAGER', 'TECHNICAL_AUTHORITY', 'CISF_SECURITY', 'VIGILANCE_AUDITOR', 'SUPER_ADMIN']}>
      <div className="space-y-4 max-w-7xl mx-auto pb-10">
        {/* Header & Controls */}
        <div className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-lg p-4 transition-colors">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-sm font-semibold text-zinc-900 dark:text-zinc-100 font-sans">
                  Consignments & Inter-CPSE Requisitions
                </h1>
                <span className="px-1.5 py-0.2 text-[10px] font-mono text-zinc-500 bg-zinc-100 dark:bg-zinc-800 rounded border border-zinc-200 dark:border-zinc-750">
                  Node: {cpse}
                </span>
              </div>
              <p className="text-xs text-zinc-500 dark:text-zinc-400 font-mono mt-0.5">
                Audit-sealed mutual-aid consignment workflows, CISF gate passes, and road transit tracking.
              </p>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={fetchRequisitions}
                disabled={loading}
                className="p-1.5 bg-zinc-100 dark:bg-zinc-800 hover:bg-zinc-200 dark:hover:bg-zinc-750 text-zinc-700 dark:text-zinc-300 rounded-md transition-colors"
                title="Refresh Table"
              >
                <RefreshCw size={13} className={loading ? 'animate-spin' : ''} />
              </button>
              <Link
                href="/discover"
                className="px-2.5 py-1.5 bg-zinc-900 hover:bg-zinc-800 text-white dark:bg-zinc-100 dark:hover:bg-zinc-200 dark:text-zinc-900 rounded-md text-xs font-medium flex items-center gap-1.5 transition-colors"
              >
                <Plus size={13} />
                <span>New Requisition</span>
              </Link>
            </div>
          </div>

          {/* Status Filters Bar */}
          <div className="mt-3 flex items-center justify-between gap-2 text-xs font-mono">
            <div className="flex items-center gap-1.5 flex-wrap">
              <span className="text-zinc-400 text-[11px]">Filter:</span>
              {['ALL', 'REQUESTED', 'APPROVED', 'GATE_PASS_ISSUED', 'DISPATCHED', 'DELIVERED'].map((st) => (
                <button
                  key={st}
                  onClick={() => setStatusFilter(st)}
                  className={`px-2 py-0.5 rounded text-[10px] font-medium transition-colors ${
                    statusFilter === st
                      ? 'bg-zinc-900 text-white dark:bg-zinc-100 dark:text-zinc-900'
                      : 'bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-400 hover:bg-zinc-200 dark:hover:bg-zinc-700'
                  }`}
                >
                  {st.replace('_', ' ')}
                </button>
              ))}
            </div>

            <span className="text-[11px] text-zinc-400">
              {filteredRequests.length} records
            </span>
          </div>
        </div>

        {actionSuccess && (
          <div className="p-2.5 bg-emerald-500/10 border border-emerald-500/20 text-emerald-700 dark:text-emerald-400 text-xs font-mono rounded-lg flex items-center justify-between">
            <span>{actionSuccess}</span>
            <button onClick={() => setActionSuccess(null)} className="text-zinc-400 hover:text-zinc-600">&times;</button>
          </div>
        )}

        {error && (
          <div className="p-2.5 bg-rose-500/10 border border-rose-500/20 text-rose-700 dark:text-rose-400 text-xs font-mono rounded-lg flex items-center justify-between">
            <span>{error}</span>
            <button onClick={fetchRequisitions} className="underline font-semibold ml-2">Retry</button>
          </div>
        )}

        {/* Consignments Table (38px Compact Rows) */}
        <div className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-lg overflow-hidden shadow-2xs">
          <div className="overflow-x-auto">
            <table className="w-full text-left compact-table border-collapse">
              <thead>
                <tr className="border-b border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-900/80">
                  <th>Requisition ID</th>
                  <th>Part SKU</th>
                  <th>Route</th>
                  <th className="text-right">Qty</th>
                  <th>Urgency</th>
                  <th>Status</th>
                  <th className="text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-100 dark:divide-zinc-800/80 text-xs font-mono">
                {loading ? (
                  Array.from({ length: 5 }).map((_, i) => (
                    <tr key={i} className="h-[38px]">
                      <td><Skeleton className="h-4 w-24" /></td>
                      <td><Skeleton className="h-4 w-32" /></td>
                      <td><Skeleton className="h-4 w-28" /></td>
                      <td className="text-right"><Skeleton className="h-4 w-8 ml-auto" /></td>
                      <td><Skeleton className="h-4 w-16" /></td>
                      <td><Skeleton className="h-4 w-20" /></td>
                      <td className="text-right"><Skeleton className="h-4 w-28 ml-auto" /></td>
                    </tr>
                  ))
                ) : filteredRequests.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="py-12 text-center text-zinc-400 font-mono text-xs">
                      No requisitions found matching current filter.
                    </td>
                  </tr>
                ) : (
                  filteredRequests.map((req) => {
                    const reqId = req.requisition_id || req.id || '';
                    const isProcessing = actionLoadingId === reqId;

                    return (
                      <tr key={reqId} className="hover:bg-zinc-50 dark:hover:bg-zinc-800/50 transition-colors">
                        <td className="py-2">
                          <Link
                            href={`/requests/${reqId}`}
                            className="font-semibold text-zinc-900 dark:text-zinc-100 hover:underline"
                          >
                            {reqId}
                          </Link>
                          {req.created_at && (
                            <div className="text-[10px] text-zinc-400">
                              {new Date(req.created_at).toLocaleDateString('en-IN')}
                            </div>
                          )}
                        </td>

                        <td>
                          <span className="font-semibold text-zinc-800 dark:text-zinc-200">{req.sku_code}</span>
                          {req.justification && (
                            <div className="text-[11px] text-zinc-500 truncate max-w-[180px] font-sans" title={req.justification}>
                              {req.justification}
                            </div>
                          )}
                        </td>

                        <td>
                          <span className="text-zinc-700 dark:text-zinc-300 font-medium">
                            {req.source_cpse} &rarr; {req.requesting_cpse}
                          </span>
                        </td>

                        <td className="text-right tabular-nums text-zinc-900 dark:text-zinc-100 font-semibold">
                          {req.required_qty}
                        </td>

                        <td>
                          <span
                            className={`px-1.5 py-0.2 rounded text-[10px] font-mono ${
                              req.urgency?.includes('EMERGENCY')
                                ? 'bg-rose-500/10 text-rose-600 dark:text-rose-400 border border-rose-500/20'
                                : 'bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-400'
                            }`}
                          >
                            {req.urgency || 'STANDARD'}
                          </span>
                        </td>

                        <td>
                          <span
                            className={`inline-flex items-center gap-1 px-2 py-0.5 text-[10px] font-mono rounded-full border ${
                              req.status === 'DELIVERED'
                                ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20'
                                : req.status === 'DISPATCHED'
                                ? 'bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-500/20'
                                : req.status === 'GATE_PASS_ISSUED'
                                ? 'bg-purple-500/10 text-purple-600 dark:text-purple-400 border-purple-500/20'
                                : req.status === 'APPROVED'
                                ? 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/20'
                                : 'bg-zinc-500/10 text-zinc-600 dark:text-zinc-400 border-zinc-500/20'
                            }`}
                          >
                            <span className="w-1.5 h-1.5 rounded-full bg-current" />
                            <span>{req.status}</span>
                          </span>
                        </td>

                        <td className="text-right">
                          <div className="flex items-center justify-end gap-1.5">
                            {req.status === 'REQUESTED' && (
                              <button
                                onClick={() => handleApprove(reqId)}
                                disabled={isProcessing}
                                className="px-2 py-1 bg-zinc-900 hover:bg-zinc-800 text-white dark:bg-zinc-100 dark:hover:bg-zinc-200 dark:text-zinc-900 rounded text-[11px] font-medium transition-colors disabled:opacity-50"
                              >
                                Approve
                              </button>
                            )}

                            {req.status === 'APPROVED' && (
                              <button
                                onClick={() => handleGenerateGatePass(reqId)}
                                disabled={isProcessing}
                                className="px-2 py-1 bg-zinc-900 hover:bg-zinc-800 text-white dark:bg-zinc-100 dark:hover:bg-zinc-200 dark:text-zinc-900 rounded text-[11px] font-medium transition-colors disabled:opacity-50"
                              >
                                Issue Pass
                              </button>
                            )}

                            {req.status === 'GATE_PASS_ISSUED' && (
                              <button
                                onClick={() => handleDispatch(reqId)}
                                disabled={isProcessing}
                                className="px-2 py-1 bg-zinc-900 hover:bg-zinc-800 text-white dark:bg-zinc-100 dark:hover:bg-zinc-200 dark:text-zinc-900 rounded text-[11px] font-medium transition-colors disabled:opacity-50"
                              >
                                Dispatch
                              </button>
                            )}

                            {req.status === 'DISPATCHED' && (
                              <button
                                onClick={() => handleDeliver(reqId)}
                                disabled={isProcessing}
                                className="px-2 py-1 bg-emerald-600 hover:bg-emerald-700 text-white rounded text-[11px] font-medium transition-colors disabled:opacity-50"
                              >
                                Confirm
                              </button>
                            )}

                            <Link
                              href={`/requests/${reqId}`}
                              className="px-2 py-1 bg-zinc-100 dark:bg-zinc-800 hover:bg-zinc-200 dark:hover:bg-zinc-700 text-zinc-700 dark:text-zinc-300 rounded text-[11px] transition-colors"
                            >
                              Gate Pass
                            </Link>
                          </div>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </ProtectedRoute>
  );
}
