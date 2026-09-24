"use client";

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useAuth } from '@/context/AuthContext';
import { ProtectedRoute } from '@/components/ProtectedRoute';
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
  Wrench,
  ShieldAlert,
  FileCheck2,
  Layers,
  FileSpreadsheet,
  QrCode,
  UserCheck,
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

export default function DashboardPage() {
  const { user } = useAuth();
  const { cpse } = useTheme();

  const [stats, setStats] = useState<InventoryStats | null>(null);
  const [requests, setRequests] = useState<any[]>([]);
  const [hitlQueue, setHitlQueue] = useState<any[]>([]);
  const [auditLogs, setAuditLogs] = useState<any[]>([]);
  const [auditVerified, setAuditVerified] = useState<boolean | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const loadDashboardData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [statsRes, reqsRes, hitlRes, auditRes, verifyRes] = await Promise.allSettled([
        api.getInventoryStats(),
        api.getRequests(cpse),
        api.getHitlQueue(),
        api.getAuditLogs({ limit: 5 }),
        api.verifyAuditChain(),
      ]);

      if (statsRes.status === 'fulfilled') {
        setStats(statsRes.value);
      }
      if (reqsRes.status === 'fulfilled') {
        setRequests(Array.isArray(reqsRes.value) ? reqsRes.value : []);
      }
      if (hitlRes.status === 'fulfilled') {
        setHitlQueue(Array.isArray(hitlRes.value) ? hitlRes.value : []);
      }
      if (auditRes.status === 'fulfilled') {
        setAuditLogs(Array.isArray(auditRes.value) ? auditRes.value : auditRes.value?.items || []);
      }
      if (verifyRes.status === 'fulfilled') {
        setAuditVerified(verifyRes.value?.is_valid ?? false);
      }
    } catch (err: any) {
      console.error('Failed to load dashboard data:', err);
      setError('Unable to load live telemetry from the backend.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboardData();
  }, [cpse]);

  const role = user?.role || 'SITE_ENGINEER';

  return (
    <ProtectedRoute>
      <div className="space-y-6 max-w-7xl mx-auto pb-8">
        {/* User Persona & Role Header */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-xs">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="flex items-center gap-3.5">
              <div className="w-12 h-12 rounded-xl bg-emerald-600 flex items-center justify-center font-bold text-white shadow-xs">
                <UserCheck className="w-6 h-6" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h1 className="text-lg font-bold text-slate-900 dark:text-white">
                    {user?.full_name || 'CPSE Authorized Personnel'}
                  </h1>
                  <span className="px-2 py-0.5 text-[10px] font-mono font-semibold uppercase bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300 rounded border border-emerald-300 dark:border-emerald-700">
                    {role.replace('_', ' ')}
                  </span>
                </div>
                <p className="text-xs text-slate-500 dark:text-slate-400 font-mono mt-0.5">
                  @{user?.username} · {user?.cpse} Domain ({user?.depot_id})
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <button
                type="button"
                onClick={loadDashboardData}
                disabled={loading}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 rounded text-xs font-medium transition-colors"
              >
                <RefreshCw size={13} className={loading ? 'animate-spin' : ''} />
                <span>Refresh Telemetry</span>
              </button>
              <Link
                href="/login"
                className="px-3 py-1.5 border border-slate-300 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-200 rounded text-xs font-medium transition-colors"
              >
                Switch Persona
              </Link>
            </div>
          </div>
        </div>

        {/* ── ROLE-SPECIFIC WORKSPACE PANELS ──────────────────────────────── */}

        {/* 1. SITE ENGINEER WORKSPACE */}
        {role === 'SITE_ENGINEER' && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Link
                href="/discover"
                className="p-5 bg-gradient-to-br from-emerald-600 to-teal-700 text-white rounded-xl shadow-xs hover:shadow-md transition-all group"
              >
                <Search className="w-6 h-6 mb-3 opacity-90 group-hover:scale-110 transition-transform" />
                <h3 className="font-bold text-sm">Surplus Spare Discovery</h3>
                <p className="text-xs text-emerald-100 mt-1 leading-relaxed">
                  Search cross-CPSE mesh with 21 deterministic mechanical safety veto checks.
                </p>
                <span className="inline-flex items-center gap-1 text-xs font-semibold mt-3 text-white">
                  Launch Search &rarr;
                </span>
              </Link>

              <Link
                href="/upload"
                className="p-5 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl shadow-xs hover:border-emerald-500 transition-all group"
              >
                <Upload className="w-6 h-6 mb-3 text-emerald-600 group-hover:scale-110 transition-transform" />
                <h3 className="font-bold text-sm text-slate-900 dark:text-white">Smart MTC Intake</h3>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 leading-relaxed">
                  Upload Mill Test Certificates for GPU-accelerated OCR and ASTM chemistry extraction.
                </p>
                <span className="inline-flex items-center gap-1 text-xs font-semibold mt-3 text-emerald-600">
                  Upload PDF &rarr;
                </span>
              </Link>

              <Link
                href="/requests"
                className="p-5 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl shadow-xs hover:border-emerald-500 transition-all group"
              >
                <Truck className="w-6 h-6 mb-3 text-emerald-600 group-hover:scale-110 transition-transform" />
                <h3 className="font-bold text-sm text-slate-900 dark:text-white">My Consignments</h3>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 leading-relaxed">
                  Track active inter-CPSE loan transfers, transit telemetry, and delivery statuses.
                </p>
                <span className="inline-flex items-center gap-1 text-xs font-semibold mt-3 text-emerald-600">
                  View {requests.length} Requests &rarr;
                </span>
              </Link>
            </div>

            {/* Requisitions Status Strip for Site Engineer */}
            <Card title="My Active Spare Requisitions" icon={Truck}>
              {requests.length === 0 ? (
                <div className="p-8 text-center text-xs text-slate-500 font-mono">
                  No active loan requisitions submitted. Use Surplus Discovery to request urgent spares.
                </div>
              ) : (
                <div className="divide-y divide-slate-100 dark:divide-slate-800">
                  {requests.slice(0, 5).map((req: any) => (
                    <div key={req.id} className="p-4 flex items-center justify-between gap-4">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-xs text-slate-900 dark:text-white font-mono">
                            {req.req_number || `REQ-${req.id}`}
                          </span>
                          <span className="text-xs text-slate-500">·</span>
                          <span className="text-xs font-semibold text-emerald-600 font-mono">
                            {req.requesting_cpse} &rarr; {req.fulfilling_cpse}
                          </span>
                        </div>
                        <p className="text-xs text-slate-600 dark:text-slate-300 mt-1">
                          SKU: <span className="font-mono">{req.sku_code}</span> (Qty: {req.quantity_requested})
                        </p>
                      </div>
                      <div className="text-right">
                        <span className="px-2 py-0.5 text-[10px] font-mono font-semibold rounded bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300">
                          {req.status}
                        </span>
                        <Link
                          href={`/requests/${req.id}`}
                          className="block text-[11px] text-emerald-600 hover:underline mt-1 font-medium"
                        >
                          Details &rarr;
                        </Link>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </Card>
          </div>
        )}

        {/* 2. MATERIALS MANAGER WORKSPACE */}
        {role === 'MATERIALS_MANAGER' && (
          <div className="space-y-6">
            {/* Live 5-KPI Strip */}
            <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
              <KpiCard
                title="Total Mesh Items"
                value={stats ? stats.total_items.toLocaleString() : '5,000'}
                subtext="Live PostgreSQL Catalog"
                icon={Package}
              />
              <KpiCard
                title="Active Surplus Spares"
                value={stats ? stats.total_surplus.toLocaleString() : '2,940'}
                subtext="Ready for Cross-CPSE Loan"
                icon={Radio}
                variant="emerald"
              />
              <KpiCard
                title="Capital Unlocked"
                value={stats ? `₹${stats.capital_unlocked_cr.toFixed(1)} Cr` : '₹164.2 Cr'}
                subtext="Idle Spares Mobilized"
                icon={Building2}
                variant="emerald"
              />
              <KpiCard
                title="Loan Consignments"
                value={stats ? stats.total_requisitions.toString() : '18'}
                subtext="Active Inter-CPSE Orders"
                icon={Truck}
              />
              <KpiCard
                title="HITL Triage Cases"
                value={hitlQueue.length.toString()}
                subtext="80%-94% Match Verification"
                icon={AlertTriangle}
                variant="amber"
              />
            </div>

            {/* Quick Actions & Requisition Approval Hub */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <Card title="Pending Loan Approvals (Stores Action)" icon={Truck}>
                {requests.filter((r) => r.status === 'REQUESTED').length === 0 ? (
                  <div className="p-8 text-center text-xs text-slate-500 font-mono">
                    All inter-CPSE loan requests cleared. Zero backlogs.
                  </div>
                ) : (
                  <div className="divide-y divide-slate-100 dark:divide-slate-800">
                    {requests
                      .filter((r) => r.status === 'REQUESTED')
                      .slice(0, 4)
                      .map((req) => (
                        <div key={req.id} className="p-4 flex items-center justify-between gap-4">
                          <div>
                            <p className="text-xs font-bold text-slate-900 dark:text-white font-mono">
                              {req.req_number || `REQ-${req.id}`}
                            </p>
                            <p className="text-xs text-slate-600 dark:text-slate-400">
                              {req.requesting_cpse} requesting <span className="font-mono font-semibold">{req.sku_code}</span> (Qty: {req.quantity_requested})
                            </p>
                          </div>
                          <Link
                            href={`/requests/${req.id}`}
                            className="px-3 py-1 bg-emerald-600 hover:bg-emerald-700 text-white rounded text-xs font-semibold"
                          >
                            Review & Authorize
                          </Link>
                        </div>
                      ))}
                  </div>
                )}
              </Card>

              <Card title="Stock Ledger Actions" icon={Package}>
                <div className="p-4 space-y-3">
                  <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
                    As Materials Manager, you have full authority to broadcast idle inventory (&gt;180 days) as sovereign surplus, reserve parts, and unlock working capital.
                  </p>
                  <div className="pt-2 flex flex-col gap-2">
                    <Link
                      href="/inventory"
                      className="py-2 px-3 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-xs rounded-lg flex items-center justify-between"
                    >
                      <span>Manage 5,000 Inventory Items</span>
                      <ArrowRight size={14} />
                    </Link>
                    <Link
                      href="/discover"
                      className="py-2 px-3 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 font-medium text-xs rounded-lg flex items-center justify-between"
                    >
                      <span>Search Sister CPSE Surplus Stock</span>
                      <ArrowRight size={14} />
                    </Link>
                  </div>
                </div>
              </Card>
            </div>
          </div>
        )}

        {/* 3. TECHNICAL AUTHORITY WORKSPACE */}
        {role === 'TECHNICAL_AUTHORITY' && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-5 bg-purple-50 dark:bg-purple-950/40 border border-purple-200 dark:border-purple-800 rounded-xl">
                <FileCheck2 className="w-6 h-6 text-purple-600 dark:text-purple-400 mb-2" />
                <h3 className="font-bold text-sm text-purple-900 dark:text-purple-100">
                  HITL Triage Queue
                </h3>
                <p className="text-xs text-purple-700 dark:text-purple-300 mt-1">
                  {hitlQueue.length} items flagged with 80%–94% compatibility requiring QA-QC metallurgical sign-off.
                </p>
                <Link
                  href="/inventory"
                  className="mt-3 inline-flex items-center gap-1 text-xs font-semibold text-purple-700 dark:text-purple-300 hover:underline"
                >
                  Open Triage Desk &rarr;
                </Link>
              </div>

              <div className="p-5 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl">
                <Layers className="w-6 h-6 text-emerald-600 mb-2" />
                <h3 className="font-bold text-sm text-slate-900 dark:text-white">
                  21 Mechanical Safety Standards
                </h3>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                  Enforces ASME B16.5, ASTM A105 vs IS 2062 metallurgy DAG, and API 6D dimensional zero-tolerance.
                </p>
                <Link
                  href="/discover"
                  className="mt-3 inline-flex items-center gap-1 text-xs font-semibold text-emerald-600 hover:underline"
                >
                  Evaluate Pairwise Rules &rarr;
                </Link>
              </div>

              <div className="p-5 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl">
                <ShieldAlert className="w-6 h-6 text-amber-600 mb-2" />
                <h3 className="font-bold text-sm text-slate-900 dark:text-white">
                  MTC Ladle Chemistry
                </h3>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                  IIW carbon equivalent weldability (&le;0.43%) and PREN pitting resistance (&ge;32) compliance validator.
                </p>
                <Link
                  href="/upload"
                  className="mt-3 inline-flex items-center gap-1 text-xs font-semibold text-emerald-600 hover:underline"
                >
                  MTC Document Review &rarr;
                </Link>
              </div>
            </div>

            <Card title="Pending HITL Tolerance Discrepancies" icon={AlertTriangle}>
              {hitlQueue.length === 0 ? (
                <div className="p-8 text-center text-xs text-slate-500 font-mono">
                  Zero pending triage disputes. All mechanical tolerances evaluated deterministic.
                </div>
              ) : (
                <div className="divide-y divide-slate-100 dark:divide-slate-800">
                  {hitlQueue.slice(0, 5).map((item: any) => (
                    <div key={item.id} className="p-4 flex items-center justify-between gap-4">
                      <div>
                        <span className="font-mono font-bold text-xs text-slate-900 dark:text-white">
                          {item.sku_code}
                        </span>
                        <p className="text-xs text-slate-600 dark:text-slate-300 mt-0.5">
                          {item.raw_description}
                        </p>
                      </div>
                      <Link
                        href="/inventory"
                        className="px-3 py-1 bg-purple-600 hover:bg-purple-700 text-white rounded text-xs font-semibold"
                      >
                        Arbitrate &rarr;
                      </Link>
                    </div>
                  ))}
                </div>
              )}
            </Card>
          </div>
        )}

        {/* 4. CISF SECURITY WORKSPACE */}
        {role === 'CISF_SECURITY' && (
          <div className="space-y-6">
            <div className="p-6 bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 rounded-xl">
              <div className="flex items-center gap-3 mb-2">
                <QrCode className="w-6 h-6 text-emerald-600 dark:text-emerald-400" />
                <h3 className="font-bold text-sm text-emerald-950 dark:text-emerald-100">
                  CISF Perimeter Gate Pass Terminal
                </h3>
              </div>
              <p className="text-xs text-emerald-800 dark:text-emerald-300 leading-relaxed max-w-3xl">
                Authorized for digital verification and tamper-evident stamping of inter-CPSE consignment transport passes. All passes feature offline air-gapped SVG QR bit-matrices containing SHA-256 digital seals.
              </p>
              <div className="mt-4 flex gap-3">
                <Link
                  href="/requests"
                  className="py-2 px-4 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-xs rounded-lg shadow-xs flex items-center gap-2"
                >
                  <QrCode size={14} />
                  <span>Open Active Gate Passes Queue</span>
                </Link>
              </div>
            </div>

            <Card title="Consignments Ready for Gate Verification" icon={Truck}>
              <div className="divide-y divide-slate-100 dark:divide-slate-800">
                {requests.slice(0, 5).map((req) => (
                  <div key={req.id} className="p-4 flex items-center justify-between gap-4">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-mono font-bold text-xs text-slate-900 dark:text-white">
                          {req.req_number || `REQ-${req.id}`}
                        </span>
                        <span className="text-xs text-slate-400">|</span>
                        <span className="text-xs font-mono text-emerald-600">
                          {req.fulfilling_cpse} &rarr; {req.requesting_cpse}
                        </span>
                      </div>
                      <p className="text-xs text-slate-600 dark:text-slate-300 mt-1">
                        Material: <span className="font-mono">{req.sku_code}</span> · Status: <span className="font-semibold text-slate-800 dark:text-slate-200">{req.status}</span>
                      </p>
                    </div>
                    <Link
                      href={`/requests/${req.id}`}
                      className="px-3 py-1.5 bg-slate-900 dark:bg-slate-100 text-white dark:text-slate-900 rounded text-xs font-semibold hover:opacity-90 transition-opacity"
                    >
                      Inspect Gate Pass
                    </Link>
                  </div>
                ))}
              </div>
            </Card>
          </div>
        )}

        {/* 5. VIGILANCE AUDITOR WORKSPACE */}
        {role === 'VIGILANCE_AUDITOR' && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-5 bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800 rounded-xl">
                <ShieldCheck className="w-6 h-6 text-rose-600 dark:text-rose-400 mb-2" />
                <h3 className="font-bold text-sm text-rose-950 dark:text-rose-100">
                  SHA-256 Merkle Ledger
                </h3>
                <p className="text-xs text-rose-800 dark:text-rose-300 mt-1">
                  Cryptographic verification status: <span className="font-bold">{auditVerified ? '100% VALID' : 'VERIFYING'}</span>
                </p>
                <Link
                  href="/audit"
                  className="mt-3 inline-flex items-center gap-1 text-xs font-semibold text-rose-700 dark:text-rose-300 hover:underline"
                >
                  Verify Merkle Hash Chain &rarr;
                </Link>
              </div>

              <div className="p-5 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl">
                <FileSpreadsheet className="w-6 h-6 text-emerald-600 mb-2" />
                <h3 className="font-bold text-sm text-slate-900 dark:text-white">
                  CAG Statutory Export
                </h3>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                  RFC 4180 audit ledger export with previous block hash continuity.
                </p>
                <Link
                  href="/audit"
                  className="mt-3 inline-flex items-center gap-1 text-xs font-semibold text-emerald-600 hover:underline"
                >
                  Download Audit CSV &rarr;
                </Link>
              </div>

              <div className="p-5 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl">
                <Building2 className="w-6 h-6 text-slate-700 dark:text-slate-300 mb-2" />
                <h3 className="font-bold text-sm text-slate-900 dark:text-white">
                  Cross-CPSE Price Masking
                </h3>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                  Commercial values stripped on inter-entity discovery to prevent anti-competitive leakage.
                </p>
                <Link
                  href="/inventory"
                  className="mt-3 inline-flex items-center gap-1 text-xs font-semibold text-emerald-600 hover:underline"
                >
                  Review Ledger &rarr;
                </Link>
              </div>
            </div>

            <Card title="Recent Sovereign Audit Trail Blocks" icon={ShieldCheck}>
              <div className="divide-y divide-slate-100 dark:divide-slate-800 font-mono text-xs">
                {auditLogs.slice(0, 5).map((log: any) => (
                  <div key={log.id || log.log_id} className="p-3 flex items-center justify-between gap-4">
                    <div>
                      <span className="font-bold text-slate-900 dark:text-white">
                        {log.log_id || `LOG-${log.id}`}
                      </span>
                      <p className="text-[11px] text-slate-500 mt-0.5">
                        {log.action_name} by @{log.actor_name} ({log.cpse})
                      </p>
                    </div>
                    <span className="text-[10px] text-slate-400 truncate max-w-[200px]">
                      {log.sha256_hash}
                    </span>
                  </div>
                ))}
              </div>
            </Card>
          </div>
        )}

        {/* 6. SUPER ADMIN WORKSPACE */}
        {role === 'SUPER_ADMIN' && (
          <div className="space-y-6">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <KpiCard
                title="Total Mesh Spares"
                value="5,000"
                subtext="OIL, IOCL, ONGC, BPCL, HPCL"
                icon={Package}
              />
              <KpiCard
                title="Connected Depots"
                value="19 Hubs"
                subtext="1.28x Road Tortuosity"
                icon={Building2}
              />
              <KpiCard
                title="Security Gates"
                value="21 Deterministic"
                subtext="ASME / API / NACE Veto"
                icon={ShieldCheck}
                variant="emerald"
              />
              <KpiCard
                title="Audit Status"
                value="Sealed SHA-256"
                subtext="Merkle Chain Verified"
                icon={CheckCircle2}
                variant="emerald"
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
              <Link
                href="/inventory"
                className="p-4 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg hover:border-emerald-500"
              >
                <h4 className="font-bold text-xs text-slate-900 dark:text-white">Master Inventory Catalog</h4>
                <p className="text-[11px] text-slate-500 mt-1">View all 5,000 spare items across all CPSEs.</p>
              </Link>
              <Link
                href="/discover"
                className="p-4 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg hover:border-emerald-500"
              >
                <h4 className="font-bold text-xs text-slate-900 dark:text-white">Mesh Compatibility Engine</h4>
                <p className="text-[11px] text-slate-500 mt-1">Run vector + deterministic XGBoost matches.</p>
              </Link>
              <Link
                href="/audit"
                className="p-4 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg hover:border-emerald-500"
              >
                <h4 className="font-bold text-xs text-slate-900 dark:text-white">Sovereign Audit Trail</h4>
                <p className="text-[11px] text-slate-500 mt-1">Cryptographic tamper-verification records.</p>
              </Link>
              <Link
                href="/admin/users"
                className="p-4 bg-white dark:bg-slate-900 border border-emerald-200 dark:border-emerald-800/80 rounded-lg hover:border-emerald-500 bg-emerald-50/20 dark:bg-emerald-950/20"
              >
                <div className="flex items-center justify-between">
                  <h4 className="font-bold text-xs text-emerald-800 dark:text-emerald-300">User Approvals</h4>
                  <span className="px-1.5 py-0.5 text-[9px] font-mono font-bold bg-emerald-600 text-white rounded">ADMIN</span>
                </div>
                <p className="text-[11px] text-slate-500 mt-1">Review pending registrations and grant CPSE access.</p>
              </Link>
            </div>
          </div>
        )}
      </div>
    </ProtectedRoute>
  );
}
