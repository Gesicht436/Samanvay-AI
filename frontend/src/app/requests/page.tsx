"use client";

import React, { useState, useEffect, useMemo } from 'react';
import Link from 'next/link';
import { Card, Skeleton, Modal } from '@/components/ui';
import {
  Truck,
  Inbox,
  Send,
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
  Building2,
  QrCode,
  User as UserIcon,
  ShieldAlert,
} from 'lucide-react';
import { useTheme } from '@/components/ThemeProvider';
import { useAuth } from '@/context/AuthContext';
import { api } from '@/lib/api';
import { ProtectedRoute } from '@/components/ProtectedRoute';

interface RequisitionItem {
  id?: string;
  requisition_id: string;
  sku_code: string;
  item_description?: string;
  source_cpse: string;
  source_depot?: string;
  source_unit?: string;
  target_cpse: string;
  target_depot?: string;
  required_qty: number;
  unit_cost_inr?: number;
  total_value_inr?: number;
  urgency_level?: string;
  urgency?: string;
  status: string;
  justification?: string;
  requested_by?: string;
  approved_by?: string;
  rejection_reason?: string;
  created_at?: string;
  audit_hash?: string;
}

export default function RequisitionsListPage() {
  const { cpse } = useTheme();
  const { user } = useAuth();
  const [requests, setRequests] = useState<RequisitionItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Tab & Filter States
  const [activeTab, setActiveTab] = useState<'OUTGOING' | 'INCOMING' | 'ALL'>('OUTGOING');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [superAdminCpseFilter, setSuperAdminCpseFilter] = useState<string>('ALL');
  const [superAdminDepotFilter, setSuperAdminDepotFilter] = useState<string>('');

  // Action states
  const [actionLoadingId, setActionLoadingId] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  // Rejection Modal State
  const [rejectModalReq, setRejectModalReq] = useState<RequisitionItem | null>(null);
  const [rejectReason, setRejectReason] = useState<string>('Material currently earmarked for local maintenance shutdown');

  // Gate Pass Modal State
  const [gatePassModalReq, setGatePassModalReq] = useState<RequisitionItem | null>(null);
  const [gatePassForm, setGatePassForm] = useState({
    vehicle_no: 'AS-01-EA-4102',
    driver_name: 'B. K. Sharma',
    driver_id: 'DL-04201988102',
    transporter_name: 'CONCOR Heavy Logistics',
  });

  const isSuperAdmin = user?.role === 'SUPER_ADMIN';
  const isAuditor = user?.role === 'AUDITOR' || user?.role === 'VIGILANCE_AUDITOR';

  // For Super Admin/Auditor default to ALL consignments, for regular users default to OUTGOING
  useEffect(() => {
    if (isSuperAdmin || isAuditor) {
      setActiveTab('ALL');
    } else {
      setActiveTab('OUTGOING');
    }
  }, [isSuperAdmin, isAuditor]);

  const fetchRequisitions = async () => {
    setLoading(true);
    setError(null);
    try {
      let res: any;
      if (isSuperAdmin || isAuditor) {
        res = await api.getRequests({
          cpse: superAdminCpseFilter !== 'ALL' ? superAdminCpseFilter : undefined,
          depot: superAdminDepotFilter.trim() ? superAdminDepotFilter.trim() : undefined,
        });
      } else {
        res = await api.getRequests();
      }
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
  }, [superAdminCpseFilter, superAdminDepotFilter]);

  const handleApprove = async (req: RequisitionItem) => {
    const reqId = req.requisition_id;
    setActionLoadingId(reqId);
    setActionSuccess(null);
    setActionError(null);
    try {
      await api.approveRequisition(reqId, { approved_by: user?.username || 'SYSTEM_OFFICER' });
      setActionSuccess(`Requisition ${reqId} approved successfully by ${user?.username || 'Materials Manager'}.`);
      fetchRequisitions();
    } catch (err: any) {
      setActionError(`Approval failed: ${err.message}`);
    } finally {
      setActionLoadingId(null);
    }
  };

  const handleOpenReject = (req: RequisitionItem) => {
    setRejectModalReq(req);
    setRejectReason('Material currently earmarked for local maintenance shutdown');
  };

  const handleConfirmReject = async () => {
    if (!rejectModalReq) return;
    const reqId = rejectModalReq.requisition_id;
    setActionLoadingId(reqId);
    setActionSuccess(null);
    setActionError(null);
    try {
      await api.rejectRequisition(reqId, { reason: rejectReason.trim() || 'Declined by Materials Authority' });
      setActionSuccess(`Requisition ${reqId} rejected.`);
      setRejectModalReq(null);
      fetchRequisitions();
    } catch (err: any) {
      setActionError(`Rejection failed: ${err.message}`);
    } finally {
      setActionLoadingId(null);
    }
  };

  const handleOpenGatePassModal = (req: RequisitionItem) => {
    setGatePassModalReq(req);
  };

  const handleConfirmGatePass = async () => {
    if (!gatePassModalReq) return;
    const reqId = gatePassModalReq.requisition_id;
    setActionLoadingId(reqId);
    setActionSuccess(null);
    setActionError(null);
    try {
      const res = await api.generateGatePass(reqId, {
        pass_type: 'NON-RETURNABLE-MUTUAL-AID',
        issuing_officer: `${user?.username || 'CISF_OFFICER'} (${user?.role || 'CISF_SECURITY'})`,
        vehicle_no: gatePassForm.vehicle_no,
        driver_name: gatePassForm.driver_name,
        driver_id: gatePassForm.driver_id,
        transporter_name: gatePassForm.transporter_name,
      });
      setActionSuccess(`CISF Non-Returnable Gate Pass ${res.gate_pass_no || ''} issued with SHA-256 seal.`);
      setGatePassModalReq(null);
      fetchRequisitions();
    } catch (err: any) {
      setActionError(`Gate pass generation failed: ${err.message}`);
    } finally {
      setActionLoadingId(null);
    }
  };

  const handleDispatch = async (req: RequisitionItem) => {
    const reqId = req.requisition_id;
    setActionLoadingId(reqId);
    setActionSuccess(null);
    setActionError(null);
    try {
      await api.dispatchRequisition(reqId);
      setActionSuccess(`Consignment ${reqId} flagged as DISPATCHED out of source depot.`);
      fetchRequisitions();
    } catch (err: any) {
      setActionError(`Dispatch failed: ${err.message}`);
    } finally {
      setActionLoadingId(null);
    }
  };

  const handleDeliver = async (req: RequisitionItem) => {
    const reqId = req.requisition_id;
    setActionLoadingId(reqId);
    setActionSuccess(null);
    setActionError(null);
    try {
      await api.deliverRequisition(reqId);
      setActionSuccess(`Consignment ${reqId} confirmed as DELIVERED & inventory ledger reconciled.`);
      fetchRequisitions();
    } catch (err: any) {
      setActionError(`Delivery failed: ${err.message}`);
    } finally {
      setActionLoadingId(null);
    }
  };

  // Scope Filtering by Tab (Outgoing vs Incoming vs All)
  const tabScopedRequests = useMemo(() => {
    if (!user) return requests;
    if (activeTab === 'ALL') return requests;

    if (activeTab === 'OUTGOING') {
      // Requisitions created by this user OR demanded for user's CPSE
      return requests.filter((r) => {
        const isMyUsername = r.requested_by === user.username;
        const isMyCpse = r.target_cpse === user.cpse;
        return isMyUsername || (isSuperAdmin ? false : isMyCpse);
      });
    }

    if (activeTab === 'INCOMING') {
      // Requisitions directed to user's depot or CPSE to release surplus
      return requests.filter((r) => {
        const matchesCpse = r.source_cpse === user.cpse;
        const matchesDepot = user.depot_id && r.source_depot?.toLowerCase().includes(user.depot_id.toLowerCase());
        return matchesCpse || matchesDepot;
      });
    }

    return requests;
  }, [requests, activeTab, user, isSuperAdmin]);

  // Secondary Search & Status Filter
  const filteredRequests = useMemo(() => {
    let result = tabScopedRequests;

    if (statusFilter !== 'ALL') {
      result = result.filter((r) => {
        const s = r.status?.toUpperCase();
        if (statusFilter === 'PENDING') {
          return s === 'PENDING_APPROVAL' || s === 'REQUESTED';
        }
        return s === statusFilter;
      });
    }

    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase().trim();
      result = result.filter(
        (r) =>
          r.requisition_id?.toLowerCase().includes(q) ||
          r.sku_code?.toLowerCase().includes(q) ||
          r.source_cpse?.toLowerCase().includes(q) ||
          r.target_cpse?.toLowerCase().includes(q) ||
          r.source_depot?.toLowerCase().includes(q) ||
          r.target_depot?.toLowerCase().includes(q) ||
          r.requested_by?.toLowerCase().includes(q)
      );
    }

    return result;
  }, [tabScopedRequests, statusFilter, searchQuery]);

  // Counts for tabs
  const outgoingCount = useMemo(() => {
    if (!user) return 0;
    return requests.filter((r) => r.requested_by === user.username || r.target_cpse === user.cpse).length;
  }, [requests, user]);

  const incomingCount = useMemo(() => {
    if (!user) return 0;
    return requests.filter((r) => r.source_cpse === user.cpse || (user.depot_id && r.source_depot?.toLowerCase().includes(user.depot_id.toLowerCase()))).length;
  }, [requests, user]);

  return (
    <ProtectedRoute allowedRoles={['SITE_ENGINEER', 'MATERIALS_MANAGER', 'TECHNICAL_AUTHORITY', 'CISF_SECURITY', 'VIGILANCE_AUDITOR', 'SUPER_ADMIN']}>
      <div className="space-y-4 max-w-7xl mx-auto pb-10">
        {/* Header Banner */}
        <div className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-lg p-4 transition-colors">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <div className="flex items-center gap-2 flex-wrap">
                <h1 className="text-sm font-semibold text-zinc-900 dark:text-zinc-100 font-sans">
                  Consignments & Inter-CPSE Requisitions
                </h1>
                <span className="px-2 py-0.5 text-[11px] font-mono text-zinc-600 dark:text-zinc-300 bg-zinc-100 dark:bg-zinc-800 rounded border border-zinc-200 dark:border-zinc-700">
                  Tenant: <span className="font-semibold text-zinc-900 dark:text-zinc-100">{user?.cpse || cpse}</span>
                  {user?.depot_id ? ` · ${user.depot_id}` : ''}
                </span>
                {isSuperAdmin && (
                  <span className="px-1.5 py-0.2 text-[10px] font-mono bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20 rounded">
                    SUPER_ADMIN GLOBAL ACCESS
                  </span>
                )}
              </div>
              <p className="text-xs text-zinc-500 dark:text-zinc-400 font-mono mt-1">
                Role-isolated mutual-aid consignment workflows, CISF gate passes, and multi-tenant audit chain.
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
                className="px-2.5 py-1.5 bg-zinc-900 hover:bg-zinc-800 text-white dark:bg-zinc-100 dark:hover:bg-zinc-200 dark:text-zinc-900 rounded-md text-xs font-medium flex items-center gap-1.5 transition-colors shadow-2xs"
              >
                <Plus size={13} />
                <span>New Requisition</span>
              </Link>
            </div>
          </div>

          {/* Persona Scoped Navigation Tabs */}
          <div className="mt-4 pt-3 border-t border-zinc-100 dark:border-zinc-800 flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              {/* Regular users: Outgoing vs Incoming tabs */}
              <button
                onClick={() => setActiveTab('OUTGOING')}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
                  activeTab === 'OUTGOING'
                    ? 'bg-zinc-900 text-white dark:bg-zinc-100 dark:text-zinc-900 shadow-xs'
                    : 'bg-zinc-100 dark:bg-zinc-800/80 text-zinc-600 dark:text-zinc-400 hover:bg-zinc-200 dark:hover:bg-zinc-700'
                }`}
              >
                <Send size={12} />
                <span>My Outgoing Requisitions</span>
                <span className={`ml-1 px-1.5 py-0.2 rounded-full text-[10px] font-mono ${
                  activeTab === 'OUTGOING'
                    ? 'bg-white/20 text-white dark:bg-zinc-900/20 dark:text-zinc-900'
                    : 'bg-zinc-200 dark:bg-zinc-700 text-zinc-700 dark:text-zinc-300'
                }`}>
                  {outgoingCount}
                </span>
              </button>

              <button
                onClick={() => setActiveTab('INCOMING')}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
                  activeTab === 'INCOMING'
                    ? 'bg-zinc-900 text-white dark:bg-zinc-100 dark:text-zinc-900 shadow-xs'
                    : 'bg-zinc-100 dark:bg-zinc-800/80 text-zinc-600 dark:text-zinc-400 hover:bg-zinc-200 dark:hover:bg-zinc-700'
                }`}
              >
                <Inbox size={12} />
                <span>Incoming Depot Requests</span>
                <span className={`ml-1 px-1.5 py-0.2 rounded-full text-[10px] font-mono ${
                  activeTab === 'INCOMING'
                    ? 'bg-white/20 text-white dark:bg-zinc-900/20 dark:text-zinc-900'
                    : 'bg-zinc-200 dark:bg-zinc-700 text-zinc-700 dark:text-zinc-300'
                }`}>
                  {incomingCount}
                </span>
              </button>

              {(isSuperAdmin || isAuditor) && (
                <button
                  onClick={() => setActiveTab('ALL')}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
                    activeTab === 'ALL'
                      ? 'bg-zinc-900 text-white dark:bg-zinc-100 dark:text-zinc-900 shadow-xs'
                      : 'bg-zinc-100 dark:bg-zinc-800/80 text-zinc-600 dark:text-zinc-400 hover:bg-zinc-200 dark:hover:bg-zinc-700'
                  }`}
                >
                  <Building2 size={12} />
                  <span>All CPSE Consignments (Global)</span>
                  <span className={`ml-1 px-1.5 py-0.2 rounded-full text-[10px] font-mono ${
                    activeTab === 'ALL'
                      ? 'bg-white/20 text-white dark:bg-zinc-900/20 dark:text-zinc-900'
                      : 'bg-zinc-200 dark:bg-zinc-700 text-zinc-700 dark:text-zinc-300'
                  }`}>
                    {requests.length}
                  </span>
                </button>
              )}
            </div>

            {/* Quick Search */}
            <div className="relative">
              <Search size={12} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-zinc-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Filter by SKU, REQ ID, depot..."
                className="pl-7 pr-2.5 py-1 text-xs font-mono bg-zinc-50 dark:bg-zinc-800/60 border border-zinc-200 dark:border-zinc-700 rounded-md w-56 focus:outline-hidden focus:border-zinc-400 dark:focus:border-zinc-500"
              />
            </div>
          </div>

          {/* Super Admin Global Controls */}
          {isSuperAdmin && activeTab === 'ALL' && (
            <div className="mt-3 pt-3 border-t border-dashed border-zinc-200 dark:border-zinc-800 flex items-center gap-3 text-xs font-mono">
              <span className="text-zinc-400 text-[11px]">Super Admin Filter:</span>
              <div className="flex items-center gap-1.5">
                <span>CPSE:</span>
                <select
                  value={superAdminCpseFilter}
                  onChange={(e) => setSuperAdminCpseFilter(e.target.value)}
                  className="bg-zinc-100 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded px-2 py-0.5 text-xs"
                >
                  <option value="ALL">All CPSEs</option>
                  <option value="OIL">OIL</option>
                  <option value="IOCL">IOCL</option>
                  <option value="ONGC">ONGC</option>
                  <option value="BPCL">BPCL</option>
                  <option value="HPCL">HPCL</option>
                  <option value="GAIL">GAIL</option>
                  <option value="NRL">NRL</option>
                </select>
              </div>

              <div className="flex items-center gap-1.5">
                <span>Depot query:</span>
                <input
                  type="text"
                  value={superAdminDepotFilter}
                  onChange={(e) => setSuperAdminDepotFilter(e.target.value)}
                  placeholder="e.g. Panipat, Uran"
                  className="bg-zinc-100 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded px-2 py-0.5 text-xs w-36"
                />
              </div>
            </div>
          )}

          {/* Status Filter Pills */}
          <div className="mt-3 flex items-center justify-between gap-2 text-xs font-mono pt-2 border-t border-zinc-100 dark:border-zinc-800">
            <div className="flex items-center gap-1.5 flex-wrap">
              <span className="text-zinc-400 text-[11px]">Lifecycle:</span>
              {['ALL', 'PENDING', 'APPROVED', 'GATE_PASS_ISSUED', 'DISPATCHED', 'DELIVERED', 'REJECTED'].map((st) => (
                <button
                  key={st}
                  onClick={() => setStatusFilter(st)}
                  className={`px-2 py-0.5 rounded text-[10px] font-medium transition-colors ${
                    statusFilter === st
                      ? 'bg-zinc-900 text-white dark:bg-zinc-100 dark:text-zinc-900'
                      : 'bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-400 hover:bg-zinc-200 dark:hover:bg-zinc-700'
                  }`}
                >
                  {st === 'PENDING' ? 'PENDING APPROVAL' : st.replace('_', ' ')}
                </button>
              ))}
            </div>

            <span className="text-[11px] text-zinc-400">
              Showing {filteredRequests.length} of {tabScopedRequests.length}
            </span>
          </div>
        </div>

        {/* Notifications */}
        {actionSuccess && (
          <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 text-emerald-700 dark:text-emerald-400 text-xs font-mono rounded-lg flex items-center justify-between">
            <div className="flex items-center gap-2">
              <CheckCircle2 size={14} className="shrink-0" />
              <span>{actionSuccess}</span>
            </div>
            <button onClick={() => setActionSuccess(null)} className="text-zinc-400 hover:text-zinc-600 ml-2">&times;</button>
          </div>
        )}

        {actionError && (
          <div className="p-3 bg-rose-500/10 border border-rose-500/20 text-rose-700 dark:text-rose-400 text-xs font-mono rounded-lg flex items-center justify-between">
            <div className="flex items-center gap-2">
              <ShieldAlert size={14} className="shrink-0" />
              <span>{actionError}</span>
            </div>
            <button onClick={() => setActionError(null)} className="text-zinc-400 hover:text-zinc-600 ml-2">&times;</button>
          </div>
        )}

        {error && (
          <div className="p-3 bg-rose-500/10 border border-rose-500/20 text-rose-700 dark:text-rose-400 text-xs font-mono rounded-lg flex items-center justify-between">
            <span>{error}</span>
            <button onClick={fetchRequisitions} className="underline font-semibold ml-2">Retry</button>
          </div>
        )}

        {/* Consignments Table */}
        <div className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-lg overflow-hidden shadow-2xs">
          <div className="overflow-x-auto">
            <table className="w-full text-left compact-table border-collapse">
              <thead>
                <tr className="border-b border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-900/80 text-[11px] font-mono text-zinc-500">
                  <th className="py-2.5 px-3">Requisition ID</th>
                  <th className="py-2.5 px-3">Item SKU / Spec</th>
                  <th className="py-2.5 px-3">Transfer Route</th>
                  <th className="py-2.5 px-3">Requester</th>
                  <th className="py-2.5 px-3 text-right">Qty</th>
                  <th className="py-2.5 px-3">Urgency</th>
                  <th className="py-2.5 px-3">Status</th>
                  <th className="py-2.5 px-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-100 dark:divide-zinc-800/80 text-xs font-mono">
                {loading ? (
                  Array.from({ length: 5 }).map((_, i) => (
                    <tr key={i} className="h-[46px]">
                      <td className="px-3"><Skeleton className="h-4 w-24" /></td>
                      <td className="px-3"><Skeleton className="h-4 w-36" /></td>
                      <td className="px-3"><Skeleton className="h-4 w-40" /></td>
                      <td className="px-3"><Skeleton className="h-4 w-20" /></td>
                      <td className="px-3 text-right"><Skeleton className="h-4 w-8 ml-auto" /></td>
                      <td className="px-3"><Skeleton className="h-4 w-16" /></td>
                      <td className="px-3"><Skeleton className="h-4 w-24" /></td>
                      <td className="px-3 text-right"><Skeleton className="h-4 w-28 ml-auto" /></td>
                    </tr>
                  ))
                ) : filteredRequests.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="py-16 text-center text-zinc-400 font-mono text-xs">
                      <Inbox className="h-8 w-8 mx-auto mb-2 text-zinc-300 dark:text-zinc-700" />
                      {activeTab === 'OUTGOING'
                        ? 'You have not created any outgoing requisitions yet. Use Surplus Discovery to request materials.'
                        : activeTab === 'INCOMING'
                        ? 'No incoming mutual-aid transfer requests pending for your depot.'
                        : 'No requisitions found matching current filter criteria.'}
                    </td>
                  </tr>
                ) : (
                  filteredRequests.map((req) => {
                    const reqId = req.requisition_id || req.id || '';
                    const isProcessing = actionLoadingId === reqId;
                    const isRequester = user?.username === req.requested_by;
                    const isSupplyingDepot = user?.cpse === req.source_cpse;
                    const isReceivingDepot = user?.cpse === req.target_cpse;

                    return (
                      <tr key={reqId} className="hover:bg-zinc-50 dark:hover:bg-zinc-800/50 transition-colors">
                        {/* 1. ID & Timestamp */}
                        <td className="py-2.5 px-3">
                          <Link
                            href={`/requests/${reqId}`}
                            className="font-semibold text-zinc-900 dark:text-zinc-100 hover:underline flex items-center gap-1"
                          >
                            <span>{reqId}</span>
                          </Link>
                          {req.created_at && (
                            <div className="text-[10px] text-zinc-400 font-sans">
                              {new Date(req.created_at).toLocaleString('en-IN', {
                                month: 'short',
                                day: 'numeric',
                                hour: '2-digit',
                                minute: '2-digit',
                              })}
                            </div>
                          )}
                        </td>

                        {/* 2. SKU & Spec */}
                        <td className="px-3">
                          <span className="font-semibold text-zinc-800 dark:text-zinc-200">{req.sku_code}</span>
                          {req.item_description && (
                            <div className="text-[11px] text-zinc-500 truncate max-w-[200px] font-sans" title={req.item_description}>
                              {req.item_description}
                            </div>
                          )}
                          {req.justification && (
                            <div className="text-[10px] text-zinc-400 italic truncate max-w-[200px] font-sans" title={req.justification}>
                              &ldquo;{req.justification}&rdquo;
                            </div>
                          )}
                        </td>

                        {/* 3. Transfer Route */}
                        <td className="px-3">
                          <div className="flex items-center gap-1.5 font-medium">
                            <span className="text-zinc-800 dark:text-zinc-200">{req.source_cpse}</span>
                            <ArrowRight size={11} className="text-zinc-400 shrink-0" />
                            <span className="text-zinc-800 dark:text-zinc-200">{req.target_cpse}</span>
                          </div>
                          <div className="text-[10px] text-zinc-400 truncate max-w-[200px]">
                            {req.source_depot || 'Main Depot'} &rarr; {req.target_depot || 'Receiving Depot'}
                          </div>
                        </td>

                        {/* 4. Requester */}
                        <td className="px-3">
                          <div className="flex items-center gap-1 text-zinc-700 dark:text-zinc-300">
                            <UserIcon size={11} className="text-zinc-400 shrink-0" />
                            <span className="font-medium truncate max-w-[100px]">{req.requested_by || 'Engineer'}</span>
                          </div>
                          {isRequester && (
                            <span className="px-1 py-0.2 rounded text-[9px] bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-500/20">
                              You
                            </span>
                          )}
                        </td>

                        {/* 5. Qty */}
                        <td className="px-3 text-right tabular-nums text-zinc-900 dark:text-zinc-100 font-semibold">
                          {req.required_qty}
                        </td>

                        {/* 6. Urgency */}
                        <td className="px-3">
                          <span
                            className={`px-1.5 py-0.5 rounded text-[10px] font-mono ${
                              (req.urgency_level || req.urgency)?.includes('EMERGENCY')
                                ? 'bg-rose-500/10 text-rose-600 dark:text-rose-400 border border-rose-500/20'
                                : 'bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-400'
                            }`}
                          >
                            {(req.urgency_level || req.urgency) || 'STANDARD'}
                          </span>
                        </td>

                        {/* 7. Status */}
                        <td className="px-3">
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
                                : req.status === 'REJECTED'
                                ? 'bg-rose-500/10 text-rose-600 dark:text-rose-400 border-rose-500/20'
                                : 'bg-zinc-500/10 text-zinc-600 dark:text-zinc-400 border-zinc-500/20'
                            }`}
                          >
                            <span className="w-1.5 h-1.5 rounded-full bg-current" />
                            <span>{req.status === 'PENDING_APPROVAL' ? 'PENDING' : req.status}</span>
                          </span>
                          {req.approved_by && (
                            <div className="text-[9px] text-zinc-400 truncate max-w-[120px]">
                              by: {req.approved_by}
                            </div>
                          )}
                        </td>

                        {/* 8. Role-Segregated Actions */}
                        <td className="px-3 text-right">
                          <div className="flex items-center justify-end gap-1.5">
                            {/* PENDING APPROVAL STAGE */}
                            {(req.status === 'PENDING_APPROVAL' || req.status === 'REQUESTED') && (
                              <>
                                {isRequester && !isSuperAdmin ? (
                                  <span
                                    className="px-2 py-1 bg-zinc-100 dark:bg-zinc-800 text-zinc-400 rounded text-[10px] font-mono cursor-not-allowed"
                                    title="Segregation of Duties: Requesters cannot approve their own requisitions. Supplying Materials Manager approval required."
                                  >
                                    Awaiting Approval
                                  </span>
                                ) : (isSupplyingDepot || isSuperAdmin) ? (
                                  <>
                                    <button
                                      onClick={() => handleApprove(req)}
                                      disabled={isProcessing}
                                      className="px-2 py-1 bg-emerald-600 hover:bg-emerald-700 text-white rounded text-[11px] font-medium transition-colors disabled:opacity-50"
                                      title="Approve Requisition (Materials Manager)"
                                    >
                                      Approve
                                    </button>
                                    <button
                                      onClick={() => handleOpenReject(req)}
                                      disabled={isProcessing}
                                      className="px-2 py-1 bg-zinc-100 hover:bg-zinc-200 dark:bg-zinc-800 dark:hover:bg-zinc-700 text-rose-600 rounded text-[11px] font-medium transition-colors disabled:opacity-50"
                                      title="Decline / Reject Requisition"
                                    >
                                      Reject
                                    </button>
                                  </>
                                ) : (
                                  <span className="text-[10px] text-zinc-400">In Review</span>
                                )}
                              </>
                            )}

                            {/* APPROVED STAGE: GATE PASS ISSUANCE */}
                            {req.status === 'APPROVED' && (
                              <>
                                {(isSupplyingDepot || isSuperAdmin) ? (
                                  <button
                                    onClick={() => handleOpenGatePassModal(req)}
                                    disabled={isProcessing}
                                    className="px-2 py-1 bg-purple-600 hover:bg-purple-700 text-white rounded text-[11px] font-medium transition-colors disabled:opacity-50 flex items-center gap-1"
                                    title="Generate CISF Security Gate Pass"
                                  >
                                    <QrCode size={11} />
                                    <span>Issue Pass</span>
                                  </button>
                                ) : (
                                  <span className="text-[10px] text-zinc-400">Approved</span>
                                )}
                              </>
                            )}

                            {/* GATE PASS ISSUED STAGE: DISPATCH */}
                            {req.status === 'GATE_PASS_ISSUED' && (
                              <>
                                {(isSupplyingDepot || isSuperAdmin) ? (
                                  <button
                                    onClick={() => handleDispatch(req)}
                                    disabled={isProcessing}
                                    className="px-2 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded text-[11px] font-medium transition-colors disabled:opacity-50 flex items-center gap-1"
                                    title="Dispatch Consignment out of Depot"
                                  >
                                    <Truck size={11} />
                                    <span>Dispatch</span>
                                  </button>
                                ) : (
                                  <span className="text-[10px] text-zinc-400">Pass Issued</span>
                                )}
                              </>
                            )}

                            {/* DISPATCHED STAGE: DELIVERY CONFIRMATION */}
                            {req.status === 'DISPATCHED' && (
                              <>
                                {(isReceivingDepot || isRequester || isSuperAdmin) ? (
                                  <button
                                    onClick={() => handleDeliver(req)}
                                    disabled={isProcessing}
                                    className="px-2 py-1 bg-emerald-600 hover:bg-emerald-700 text-white rounded text-[11px] font-medium transition-colors disabled:opacity-50"
                                    title="Confirm Receipt & Reconcile Inventory"
                                  >
                                    Confirm Receipt
                                  </button>
                                ) : (
                                  <span className="text-[10px] text-zinc-400">In Transit</span>
                                )}
                              </>
                            )}

                            {/* Always available: View full gate pass details */}
                            <Link
                              href={`/requests/${reqId}`}
                              className="px-2 py-1 bg-zinc-100 dark:bg-zinc-800 hover:bg-zinc-200 dark:hover:bg-zinc-700 text-zinc-700 dark:text-zinc-300 rounded text-[11px] transition-colors"
                              title="View Gate Pass & Digital Ledger Record"
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

        {/* Rejection Reason Modal */}
        <Modal
          isOpen={!!rejectModalReq}
          onClose={() => setRejectModalReq(null)}
          title={`Decline Consignment Requisition ${rejectModalReq?.requisition_id || ''}`}
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
                onClick={() => setRejectModalReq(null)}
                className="px-3 py-1.5 rounded-md border border-zinc-200 dark:border-zinc-700 text-zinc-700 dark:text-zinc-300 hover:bg-zinc-100 dark:hover:bg-zinc-800 font-medium"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleConfirmReject}
                disabled={actionLoadingId === rejectModalReq?.requisition_id}
                className="px-3 py-1.5 rounded-md bg-rose-600 hover:bg-rose-700 text-white font-medium disabled:opacity-50"
              >
                {actionLoadingId === rejectModalReq?.requisition_id ? 'Declining...' : 'Confirm Rejection'}
              </button>
            </div>
          </div>
        </Modal>

        {/* CISF Digital Gate Pass Logistics Modal */}
        <Modal
          isOpen={!!gatePassModalReq}
          onClose={() => setGatePassModalReq(null)}
          title={`Generate CISF Gate Pass — ${gatePassModalReq?.requisition_id || ''}`}
        >
          <div className="space-y-3.5 text-xs font-sans">
            <p className="text-zinc-600 dark:text-zinc-400">
              Verify logistics, transport vehicle, and driver credentials for dispatch from{' '}
              <strong className="text-zinc-800 dark:text-zinc-200">{gatePassModalReq?.source_cpse}</strong> stores to{' '}
              <strong className="text-zinc-800 dark:text-zinc-200">{gatePassModalReq?.target_cpse}</strong>.
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
                onClick={() => setGatePassModalReq(null)}
                className="px-3 py-1.5 rounded-md border border-zinc-200 dark:border-zinc-700 text-zinc-700 dark:text-zinc-300 hover:bg-zinc-100 dark:hover:bg-zinc-800 font-medium"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleConfirmGatePass}
                disabled={actionLoadingId === gatePassModalReq?.requisition_id}
                className="px-3 py-1.5 rounded-md bg-purple-600 hover:bg-purple-700 text-white font-medium flex items-center gap-1.5 disabled:opacity-50"
              >
                <QrCode size={13} />
                <span>{actionLoadingId === gatePassModalReq?.requisition_id ? 'Issuing Pass...' : 'Issue Digital Gate Pass'}</span>
              </button>
            </div>
          </div>
        </Modal>
      </div>
    </ProtectedRoute>
  );
}
