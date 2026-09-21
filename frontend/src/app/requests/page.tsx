"use client";

import React, { useState, useEffect, useMemo } from 'react';
import Link from 'next/link';
import { Card } from '@/components/ui';
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
} from 'lucide-react';
import { useTheme } from '@/components/ThemeProvider';
import { api } from '@/lib/api';

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
    <div className="flex flex-col space-y-4 max-w-[1600px] mx-auto pb-8">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-5 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl shadow-2xs">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-mono font-semibold text-emerald-700 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/60 px-2 py-0.5 rounded border border-emerald-200 dark:border-emerald-800">
              CONSIGNMENT HUB
            </span>
            <span className="text-xs font-mono text-slate-500">
              Active CPSE Node: {cpse}
            </span>
          </div>
          <h1 className="text-xl font-bold text-slate-900 dark:text-white tracking-tight">
            Inter-CPSE Consignments & Material Requisitions
          </h1>
          <p className="text-xs text-slate-600 dark:text-slate-400 mt-0.5">
            Audit-sealed transfer workflows, CISF gate passes, and mutual-aid dispatch tracking across CPSEs.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={fetchRequisitions}
            disabled={loading}
            className="p-2 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 border border-slate-300 dark:border-slate-700 rounded transition-colors"
            title="Refresh Requisitions"
          >
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
          </button>
          <Link
            href="/discover"
            className="px-3.5 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded text-xs font-mono font-semibold flex items-center gap-1.5 transition-colors"
          >
            <Plus size={14} />
            <span>New Requisition</span>
          </Link>
        </div>
      </div>

      {actionSuccess && (
        <div className="p-3 bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 text-emerald-800 dark:text-emerald-300 text-xs font-mono rounded-lg flex items-center justify-between">
          <span className="font-semibold">{actionSuccess}</span>
          <button onClick={() => setActionSuccess(null)} className="text-slate-500 hover:text-slate-700">&times;</button>
        </div>
      )}

      {error && (
        <div className="p-3 bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900 text-rose-800 dark:text-rose-300 text-xs font-mono rounded-lg flex items-center justify-between">
          <span>{error}</span>
          <button onClick={fetchRequisitions} className="underline font-semibold">Retry</button>
        </div>
      )}

      {/* Filter Strip */}
      <div className="p-3 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl flex items-center justify-between text-xs font-mono">
        <div className="flex items-center gap-2">
          <span className="text-slate-500">Filter Status:</span>
          {['ALL', 'PENDING', 'APPROVED', 'GATE_PASS_ISSUED', 'DISPATCHED', 'DELIVERED'].map((st) => (
            <button
              key={st}
              onClick={() => setStatusFilter(st)}
              className={`px-2.5 py-1 rounded text-[11px] font-semibold transition-colors ${
                statusFilter === st
                  ? 'bg-slate-900 dark:bg-white text-white dark:text-slate-900'
                  : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700'
              }`}
            >
              {st}
            </button>
          ))}
        </div>

        <span className="text-slate-500 text-[11px]">
          {filteredRequests.length} requisitions found
        </span>
      </div>

      {/* Requisitions Table */}
      <Card className="p-0 border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono border-collapse">
            <thead>
              <tr className="bg-slate-50 dark:bg-slate-800/60 border-b border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-400">
                <th className="py-2.5 px-3 font-semibold">REQUISITION ID</th>
                <th className="py-2.5 px-3 font-semibold">TARGET SKU</th>
                <th className="py-2.5 px-3 font-semibold">TRANSFER ROUTE</th>
                <th className="py-2.5 px-3 font-semibold text-center">QTY</th>
                <th className="py-2.5 px-3 font-semibold">URGENCY</th>
                <th className="py-2.5 px-3 font-semibold text-center">STATUS</th>
                <th className="py-2.5 px-3 font-semibold text-right">WORKFLOW ACTIONS</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60">
              {loading ? (
                <tr>
                  <td colSpan={7} className="py-16 text-center text-slate-500">
                    <RefreshCw className="animate-spin h-5 w-5 mx-auto mb-2 text-emerald-500" />
                    <span>Loading requisitions from PostgreSQL ledger...</span>
                  </td>
                </tr>
              ) : filteredRequests.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-16 text-center text-slate-500">
                    <p>No requisitions found in database.</p>
                    <Link
                      href="/discover"
                      className="mt-2 inline-block px-3 py-1.5 bg-emerald-600 text-white rounded text-xs font-semibold"
                    >
                      Search Surplus & Initiate First Requisition &rarr;
                    </Link>
                  </td>
                </tr>
              ) : (
                filteredRequests.map((req) => {
                  const reqId = req.requisition_id || req.id || '';
                  const isProcessing = actionLoadingId === reqId;

                  return (
                    <tr key={reqId} className="hover:bg-slate-50/80 dark:hover:bg-slate-800/40 transition-colors">
                      <td className="py-3 px-3">
                        <Link
                          href={`/requests/${reqId}`}
                          className="font-bold text-emerald-700 dark:text-emerald-400 hover:underline"
                        >
                          {reqId}
                        </Link>
                        {req.created_at && (
                          <div className="text-[10px] text-slate-400">
                            {new Date(req.created_at).toLocaleDateString('en-IN')}
                          </div>
                        )}
                      </td>

                      <td className="py-3 px-3">
                        <span className="font-semibold text-slate-800 dark:text-slate-200">{req.sku_code}</span>
                        {req.justification && (
                          <div className="text-[11px] text-slate-500 truncate max-w-[220px]" title={req.justification}>
                            {req.justification}
                          </div>
                        )}
                      </td>

                      <td className="py-3 px-3">
                        <div className="font-semibold text-slate-700 dark:text-slate-300">
                          {req.source_cpse} &rarr; {req.requesting_cpse}
                        </div>
                        <div className="text-[10px] text-slate-400">
                          Target: {req.target_depot || 'Central Stores'}
                        </div>
                      </td>

                      <td className="py-3 px-3 text-center font-bold text-slate-900 dark:text-slate-100">
                        {req.required_qty}
                      </td>

                      <td className="py-3 px-3">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                            req.urgency?.includes('EMERGENCY')
                              ? 'bg-rose-100 dark:bg-rose-950/80 text-rose-800 dark:text-rose-300'
                              : 'bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300'
                          }`}
                        >
                          {req.urgency || 'STANDARD'}
                        </span>
                      </td>

                      <td className="py-3 px-3 text-center">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                            req.status === 'DELIVERED'
                              ? 'bg-emerald-100 dark:bg-emerald-950/80 text-emerald-800 dark:text-emerald-300'
                              : req.status === 'DISPATCHED'
                              ? 'bg-blue-100 dark:bg-blue-950/80 text-blue-800 dark:text-blue-300'
                              : req.status === 'GATE_PASS_ISSUED'
                              ? 'bg-purple-100 dark:bg-purple-950/80 text-purple-800 dark:text-purple-300'
                              : req.status === 'APPROVED'
                              ? 'bg-amber-100 dark:bg-amber-950/80 text-amber-800 dark:text-amber-300'
                              : 'bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300'
                          }`}
                        >
                          {req.status}
                        </span>
                      </td>

                      <td className="py-3 px-3 text-right">
                        <div className="flex items-center justify-end gap-1.5">
                          {req.status === 'PENDING' && (
                            <button
                              onClick={() => handleApprove(reqId)}
                              disabled={isProcessing}
                              className="px-2.5 py-1 bg-emerald-600 hover:bg-emerald-700 text-white rounded text-[11px] font-semibold transition-colors disabled:opacity-50"
                            >
                              Approve
                            </button>
                          )}

                          {req.status === 'APPROVED' && (
                            <button
                              onClick={() => handleGenerateGatePass(reqId)}
                              disabled={isProcessing}
                              className="px-2.5 py-1 bg-purple-600 hover:bg-purple-700 text-white rounded text-[11px] font-semibold transition-colors disabled:opacity-50"
                            >
                              Issue Gate Pass
                            </button>
                          )}

                          {req.status === 'GATE_PASS_ISSUED' && (
                            <button
                              onClick={() => handleDispatch(reqId)}
                              disabled={isProcessing}
                              className="px-2.5 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded text-[11px] font-semibold transition-colors disabled:opacity-50"
                            >
                              Dispatch
                            </button>
                          )}

                          {req.status === 'DISPATCHED' && (
                            <button
                              onClick={() => handleDeliver(reqId)}
                              disabled={isProcessing}
                              className="px-2.5 py-1 bg-emerald-600 hover:bg-emerald-700 text-white rounded text-[11px] font-semibold transition-colors disabled:opacity-50"
                            >
                              Confirm Receipt
                            </button>
                          )}

                          <Link
                            href={`/requests/${reqId}`}
                            className="px-2.5 py-1 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 rounded text-[11px] transition-colors"
                          >
                            Details
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
      </Card>
    </div>
  );
}
