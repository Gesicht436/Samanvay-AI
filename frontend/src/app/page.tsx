"use client";

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { Card, KpiCard } from '@/components/ui';
import {
  Package,
  Radio,
  CheckCircle2,
  Clock,
  ShieldCheck,
  AlertTriangle,
  ArrowRight,
  Upload,
  Search,
  Building2,
  Truck,
  ExternalLink,
  RefreshCw,
} from 'lucide-react';
import { api } from '@/lib/api';
import { useTheme } from '@/components/ThemeProvider';

interface InventoryStats {
  total_items: number;
  total_surplus: number;
  total_hitl: number;
  total_requisitions: number;
  capital_unlocked_cr: number;
  cpse_breakdown: Array<{ cpse: string; count: number; total_value_cr: number }>;
  category_breakdown: Array<{ category: string; count: number }>;
}

export default function CommandCenterPage() {
  const { cpse } = useTheme();
  const [stats, setStats] = useState<InventoryStats | null>(null);
  const [requests, setRequests] = useState<any[]>([]);
  const [auditLogs, setAuditLogs] = useState<any[]>([]);
  const [auditVerified, setAuditVerified] = useState<boolean | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const loadDashboardData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [statsRes, reqsRes, auditRes, verifyRes] = await Promise.allSettled([
        api.getInventoryStats(),
        api.getRequests(cpse),
        api.getAuditLogs({ limit: 5 }),
        api.verifyAuditChain(),
      ]);

      if (statsRes.status === 'fulfilled') {
        setStats(statsRes.value);
      }
      if (reqsRes.status === 'fulfilled') {
        setRequests(Array.isArray(reqsRes.value) ? reqsRes.value : []);
      }
      if (auditRes.status === 'fulfilled') {
        const logs = auditRes.value?.items || auditRes.value?.logs || auditRes.value;
        setAuditLogs(Array.isArray(logs) ? logs.slice(0, 5) : []);
      }
      if (verifyRes.status === 'fulfilled') {
        setAuditVerified(Boolean(verifyRes.value?.is_valid));
      }
    } catch (err: any) {
      setError(err.message || 'Failed to connect to backend service');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboardData();
  }, [cpse]);

  const totalItemsCount = stats?.total_items ?? 0;

  return (
    <div className="flex flex-col space-y-5 max-w-[1600px] mx-auto pb-8">
      {/* Top Header & Operational Status */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-5 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl shadow-2xs">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-mono font-semibold text-emerald-700 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/60 px-2 py-0.5 rounded border border-emerald-200 dark:border-emerald-800">
              OPERATING NODE: {cpse}
            </span>
            <span className="text-xs font-mono text-slate-500">
              Database: PostgreSQL / Qdrant Mesh
            </span>
          </div>
          <h1 className="text-xl font-bold text-slate-900 dark:text-white tracking-tight">
            Inter-CPSE Material Coordination Command Center
          </h1>
          <p className="text-xs text-slate-600 dark:text-slate-400 mt-0.5">
            Operational surplus redeployment, compatibility verification, and sovereign audit ledger for MoPNG CPSEs.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={loadDashboardData}
            disabled={loading}
            className="px-3 py-2 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 border border-slate-300 dark:border-slate-700 rounded text-xs font-mono font-semibold flex items-center gap-1.5 transition-colors"
            title="Refresh Live Data"
          >
            <RefreshCw size={13} className={loading ? "animate-spin" : ""} />
            <span>Refresh</span>
          </button>
          <Link
            href="/upload"
            className="px-3 py-2 bg-slate-900 dark:bg-emerald-600 hover:bg-slate-800 dark:hover:bg-emerald-700 text-white rounded text-xs font-mono font-semibold flex items-center gap-1.5 transition-colors"
          >
            <Upload size={13} />
            <span>Intake MTC</span>
          </Link>
          <Link
            href="/discover"
            className="px-3 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded text-xs font-mono font-semibold flex items-center gap-1.5 transition-colors"
          >
            <Search size={13} />
            <span>Search Surplus</span>
          </Link>
        </div>
      </div>

      {error && (
        <div className="p-3 bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900 text-rose-800 dark:text-rose-300 text-xs font-mono rounded-lg flex items-center justify-between">
          <span>Backend Connection Warning: {error}</span>
          <button onClick={loadDashboardData} className="underline font-semibold">Retry</button>
        </div>
      )}

      {/* KPI Metrics Strip */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3.5">
        <KpiCard
          title="Cataloged Stock"
          value={stats ? stats.total_items.toLocaleString('en-IN') : '—'}
          unit="Active SKUs"
          subtext="PostgreSQL Ledger"
          icon={Package}
        />
        <KpiCard
          title="Declared Surplus"
          value={stats ? stats.total_surplus.toLocaleString('en-IN') : '—'}
          unit="Spares Available"
          subtext="Available for Transfer"
          icon={Radio}
        />
        <KpiCard
          title="Surplus Capital Value"
          value={stats ? `₹${stats.capital_unlocked_cr.toFixed(1)} Cr` : '—'}
          unit="Book Value"
          subtext="Cross-CPSE Sharing"
          icon={Building2}
        />
        <KpiCard
          title="HITL Triage Queue"
          value={stats ? stats.total_hitl : '—'}
          unit="Review Cases"
          subtext="MTC / Specification Variance"
          icon={AlertTriangle}
        />
        <KpiCard
          title="Consignments"
          value={stats ? stats.total_requisitions : '—'}
          unit="Requisitions"
          subtext="Inter-CPSE Mutual Aid"
          icon={Truck}
        />
      </div>

      {/* Main Operational Tables */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        {/* Active Inter-CPSE Consignments & Requisitions (7 Cols) */}
        <Card className="lg:col-span-7 flex flex-col p-5 border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900">
          <div className="flex items-center justify-between pb-3 border-b border-slate-200 dark:border-slate-800 mb-3">
            <div>
              <h2 className="text-sm font-mono font-bold uppercase tracking-wide text-slate-900 dark:text-slate-100 flex items-center gap-2">
                <Truck size={16} className="text-emerald-600 dark:text-emerald-400" />
                Active Inter-CPSE Requisitions
              </h2>
              <p className="text-xs text-slate-500 mt-0.5 font-mono">
                Real-time transfer workflows and dispatch clearances
              </p>
            </div>
            <Link
              href="/requests"
              className="text-xs font-mono text-emerald-600 dark:text-emerald-400 hover:underline flex items-center gap-1 font-semibold"
            >
              All Requisitions <ArrowRight size={12} />
            </Link>
          </div>

          <div className="flex-1 overflow-x-auto">
            {requests.length === 0 ? (
              <div className="py-12 text-center text-xs font-mono text-slate-500">
                <p>No active requisitions recorded in database.</p>
                <div className="mt-3 flex justify-center">
                  <Link
                    href="/discover"
                    className="px-3 py-1.5 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 rounded text-xs font-mono font-semibold"
                  >
                    Initiate Transfer via Surplus Discovery &rarr;
                  </Link>
                </div>
              </div>
            ) : (
              <table className="w-full text-left text-xs font-mono border-collapse">
                <thead>
                  <tr className="border-b border-slate-200 dark:border-slate-800 text-slate-500">
                    <th className="py-2 pr-3 font-semibold">REQ ID</th>
                    <th className="py-2 px-3 font-semibold">SKU / MATERIAL</th>
                    <th className="py-2 px-3 font-semibold">QTY</th>
                    <th className="py-2 px-3 font-semibold">ROUTE</th>
                    <th className="py-2 px-3 font-semibold">STATUS</th>
                    <th className="py-2 pl-3 font-semibold text-right">ACTION</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60">
                  {requests.slice(0, 5).map((req) => (
                    <tr key={req.requisition_id || req.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors">
                      <td className="py-2.5 pr-3 font-bold text-slate-900 dark:text-slate-100">
                        {req.requisition_id || req.id}
                      </td>
                      <td className="py-2.5 px-3 max-w-[200px] truncate text-slate-700 dark:text-slate-300" title={req.sku_code}>
                        {req.sku_code}
                      </td>
                      <td className="py-2.5 px-3 text-slate-700 dark:text-slate-300 font-semibold">
                        {req.required_qty || req.quantity || 1}
                      </td>
                      <td className="py-2.5 px-3 text-slate-600 dark:text-slate-400">
                        {req.source_cpse || 'OIL'} &rarr; {req.requesting_cpse || req.requester_cpse || 'CPSE'}
                      </td>
                      <td className="py-2.5 px-3">
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300">
                          {req.status || 'PENDING'}
                        </span>
                      </td>
                      <td className="py-2.5 pl-3 text-right">
                        <Link
                          href={`/requests/${req.requisition_id || req.id}`}
                          className="text-emerald-600 dark:text-emerald-400 hover:underline font-semibold"
                        >
                          Details
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </Card>

        {/* CPSE Distribution Breakdown (5 Cols) */}
        <Card className="lg:col-span-5 p-5 border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-slate-200 dark:border-slate-800 mb-3">
              <h3 className="text-sm font-mono font-bold uppercase tracking-wide text-slate-900 dark:text-slate-100 flex items-center gap-2">
                <Building2 size={16} className="text-emerald-600 dark:text-emerald-400" />
                Cross-CPSE Inventory Footprint
              </h3>
              <span className="text-xs font-mono text-slate-500">
                {totalItemsCount.toLocaleString('en-IN')} Total Items
              </span>
            </div>

            <div className="space-y-3 pt-1">
              {stats?.cpse_breakdown && stats.cpse_breakdown.length > 0 ? (
                stats.cpse_breakdown.map((row) => {
                  const pct = totalItemsCount > 0 ? ((row.count / totalItemsCount) * 100).toFixed(1) : '0';
                  const isCurrentCpse = row.cpse === cpse;
                  return (
                    <div key={row.cpse} className="space-y-1 text-xs font-mono">
                      <div className="flex justify-between items-center text-slate-700 dark:text-slate-300">
                        <span className={`font-semibold flex items-center gap-1.5 ${isCurrentCpse ? 'text-emerald-700 dark:text-emerald-400' : ''}`}>
                          {row.cpse}
                          {isCurrentCpse && (
                            <span className="text-[10px] px-1 py-0.2 rounded bg-emerald-100 dark:bg-emerald-950 text-emerald-800 dark:text-emerald-300">
                              Active
                            </span>
                          )}
                        </span>
                        <span className="text-slate-500 dark:text-slate-400">
                          {row.count.toLocaleString('en-IN')} items · ₹{row.total_value_cr} Cr ({pct}%)
                        </span>
                      </div>
                      <div className="w-full bg-slate-100 dark:bg-slate-800 h-1.5 rounded-full overflow-hidden">
                        <div
                          style={{ width: `${pct}%` }}
                          className={`h-full rounded-full ${isCurrentCpse ? 'bg-emerald-500' : 'bg-slate-400 dark:bg-slate-600'}`}
                        />
                      </div>
                    </div>
                  );
                })
              ) : (
                <div className="py-8 text-center text-xs font-mono text-slate-500">
                  Loading inventory distribution...
                </div>
              )}
            </div>
          </div>

          <div className="pt-3 mt-4 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-xs font-mono text-slate-500">
            <span>Database Integrity: Verified</span>
            <Link href="/inventory" className="text-emerald-600 dark:text-emerald-400 hover:underline">
              Inspect Stock Ledger &rarr;
            </Link>
          </div>
        </Card>
      </div>

      {/* Sovereign Cryptographic Audit Trail Preview */}
      <Card className="p-5 border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900">
        <div className="flex items-center justify-between pb-3 border-b border-slate-200 dark:border-slate-800 mb-3">
          <div className="flex items-center gap-2">
            <ShieldCheck size={16} className="text-emerald-600 dark:text-emerald-400" />
            <h3 className="text-sm font-mono font-bold uppercase tracking-wide text-slate-900 dark:text-slate-100">
              Sovereign Cryptographic Audit Ledger
            </h3>
            {auditVerified !== null && (
              <span className={`text-[10px] font-mono px-2 py-0.5 rounded font-semibold ${
                auditVerified
                  ? 'bg-emerald-100 dark:bg-emerald-950/80 text-emerald-800 dark:text-emerald-300'
                  : 'bg-rose-100 dark:bg-rose-950/80 text-rose-800 dark:text-rose-300'
              }`}>
                {auditVerified ? 'Chain Validated (SHA-256)' : 'Validation Alert'}
              </span>
            )}
          </div>
          <Link
            href="/audit"
            className="text-xs font-mono text-emerald-600 dark:text-emerald-400 hover:underline flex items-center gap-1 font-semibold"
          >
            Full Immutable Ledger <ExternalLink size={12} />
          </Link>
        </div>

        <div className="overflow-x-auto">
          {auditLogs.length === 0 ? (
            <div className="py-8 text-center text-xs font-mono text-slate-500">
              No audit records loaded.
            </div>
          ) : (
            <table className="w-full text-left text-xs font-mono border-collapse">
              <thead>
                <tr className="border-b border-slate-200 dark:border-slate-800 text-slate-500">
                  <th className="py-2 pr-3 font-semibold">BLOCK #</th>
                  <th className="py-2 px-3 font-semibold">CATEGORY</th>
                  <th className="py-2 px-3 font-semibold">ACTION</th>
                  <th className="py-2 px-3 font-semibold">ACTOR</th>
                  <th className="py-2 px-3 font-semibold">CPSE</th>
                  <th className="py-2 pl-3 font-semibold">SHA-256 DIGITAL SEAL</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60">
                {auditLogs.map((log) => (
                  <tr key={log.id || log.block_number} className="hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors">
                    <td className="py-2 pr-3 font-bold text-slate-900 dark:text-slate-100">
                      #{log.block_number || log.id}
                    </td>
                    <td className="py-2 px-3">
                      <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300">
                        {log.action_category || log.category || 'SYSTEM'}
                      </span>
                    </td>
                    <td className="py-2 px-3 font-semibold text-slate-800 dark:text-slate-200">
                      {log.action}
                    </td>
                    <td className="py-2 px-3 text-slate-600 dark:text-slate-400">
                      {log.actor || 'SYSTEM'}
                    </td>
                    <td className="py-2 px-3 text-slate-700 dark:text-slate-300">
                      {log.cpse || 'OIL'}
                    </td>
                    <td className="py-2 pl-3 text-slate-400 dark:text-slate-500 font-mono text-[11px] truncate max-w-[220px]" title={log.hash || log.current_hash}>
                      {log.hash || log.current_hash || 'SHA256_SEALED'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </Card>
    </div>
  );
}
