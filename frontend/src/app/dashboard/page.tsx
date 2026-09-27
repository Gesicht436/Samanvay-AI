"use client";

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useAuth } from '@/context/AuthContext';
import { ProtectedRoute } from '@/components/ProtectedRoute';
import { Card, KpiCard, Skeleton, StatusBadge } from '@/components/ui';
import {
  Package,
  Radio,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  Upload,
  Search,
  Building2,
  Truck,
  RefreshCw,
  FileCheck2,
  ShieldCheck,
  Layers,
  FileSpreadsheet,
  QrCode,
  UserCheck,
  ShieldAlert,
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
      setError('Unable to load live telemetry from backend mesh.');
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
      <div className="space-y-5 max-w-7xl mx-auto pb-10">
        {/* Officer Persona & Node Context Bar */}
        <div className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-lg p-4 transition-colors">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-md bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900 flex items-center justify-center font-mono font-bold text-sm shrink-0">
                {user?.username ? user.username.slice(0, 2).toUpperCase() : 'SV'}
              </div>
              <div className="min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <h1 className="text-sm font-semibold text-zinc-900 dark:text-zinc-100 font-sans">
                    {user?.full_name || 'CPSE Authorized Personnel'}
                  </h1>
                  <span className="px-1.5 py-0.2 text-[10px] font-mono font-medium uppercase bg-zinc-100 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 rounded border border-zinc-200 dark:border-zinc-700">
                    {role.replace('_', ' ')}
                  </span>
                </div>
                <p className="text-xs text-zinc-500 dark:text-zinc-400 font-mono mt-0.5 truncate">
                  @{user?.username || 'officer'} · Active Node: <strong className="text-zinc-700 dark:text-zinc-300">{cpse}</strong> ({user?.depot_id || 'Depot Hub'})
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={loadDashboardData}
                disabled={loading}
                className="flex items-center gap-1.5 px-2.5 py-1.5 bg-zinc-100 dark:bg-zinc-800 hover:bg-zinc-200 dark:hover:bg-zinc-750 text-zinc-700 dark:text-zinc-300 rounded-md text-xs font-medium transition-colors"
                title="Refresh Live Telemetry"
              >
                <RefreshCw size={13} className={loading ? 'animate-spin' : ''} />
                <span>Sync Mesh</span>
              </button>
              <Link
                href="/login"
                className="px-2.5 py-1.5 border border-zinc-200 dark:border-zinc-700 hover:bg-zinc-50 dark:hover:bg-zinc-800 text-zinc-700 dark:text-zinc-300 rounded-md text-xs font-medium transition-colors"
              >
                Switch Persona
              </Link>
            </div>
          </div>
        </div>

        {error && (
          <div className="p-3 bg-rose-500/10 border border-rose-500/20 text-rose-700 dark:text-rose-400 text-xs font-mono rounded-lg">
            {error}
          </div>
        )}

        {/* Global Live KPI Strip (Strictly live backend telemetry, zero fake fallbacks) */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          <KpiCard
            title="Total Mesh Items"
            value={loading ? <Skeleton className="h-7 w-20" /> : (stats?.total_items?.toLocaleString() ?? '—')}
            subtext="Live PostgreSQL Catalog"
            icon={Package}
          />
          <KpiCard
            title="Active Surplus Spares"
            value={loading ? <Skeleton className="h-7 w-20" /> : (stats?.total_surplus?.toLocaleString() ?? '—')}
            subtext="Ready for Inter-CPSE Loan"
            icon={Radio}
            delta={stats?.total_surplus ? `${stats.total_surplus} available` : undefined}
            deltaType="positive"
          />
          <KpiCard
            title="Capital Unlocked"
            value={
              loading ? (
                <Skeleton className="h-7 w-24" />
              ) : stats?.capital_unlocked_cr !== undefined ? (
                `₹${stats.capital_unlocked_cr.toFixed(1)} Cr`
              ) : (
                '—'
              )
            }
            subtext="Idle Inventory Mobilized"
            icon={Building2}
            delta="Sovereign mesh"
            deltaType="positive"
          />
          <KpiCard
            title="Merkle Audit Ledger"
            value={
              loading ? (
                <Skeleton className="h-7 w-24" />
              ) : auditVerified ? (
                'SHA-256 Valid'
              ) : auditVerified === false ? (
                'Tamper Detected'
              ) : (
                'Verifying...'
              )
            }
            subtext="Tamper-Evident Chain"
            icon={CheckCircle2}
            delta={auditVerified ? '100% Sealed' : undefined}
            deltaType={auditVerified ? 'positive' : 'negative'}
          />
        </div>

        {/* ── WORKSPACE VIEWS ACCORDING TO ROLE ──────────────────────────── */}

        {/* 1. SITE ENGINEER WORKSPACE */}
        {role === 'SITE_ENGINEER' && (
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <Link
                href="/discover"
                className="p-4 bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-lg hover:border-zinc-400 dark:hover:border-zinc-600 transition-colors group"
              >
                <div className="flex items-center justify-between mb-2">
                  <Search size={18} className="text-zinc-700 dark:text-zinc-300" />
                  <span className="text-[10px] font-mono text-zinc-400 group-hover:text-zinc-900 dark:group-hover:text-zinc-100">
                    Launch &rarr;
                  </span>
                </div>
                <h3 className="font-semibold text-xs text-zinc-900 dark:text-zinc-100">Surplus Discovery</h3>
                <p className="text-[11px] text-zinc-500 dark:text-zinc-400 mt-1 leading-relaxed">
                  Query spare parts across CPSEs with 21 deterministic mechanical safety gate evaluations.
                </p>
              </Link>

              <Link
                href="/upload"
                className="p-4 bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-lg hover:border-zinc-400 dark:hover:border-zinc-600 transition-colors group"
              >
                <div className="flex items-center justify-between mb-2">
                  <Upload size={18} className="text-zinc-700 dark:text-zinc-300" />
                  <span className="text-[10px] font-mono text-zinc-400 group-hover:text-zinc-900 dark:group-hover:text-zinc-100">
                    Upload &rarr;
                  </span>
                </div>
                <h3 className="font-semibold text-xs text-zinc-900 dark:text-zinc-100">Smart MTC Intake</h3>
                <p className="text-[11px] text-zinc-500 dark:text-zinc-400 mt-1 leading-relaxed">
                  Mill Test Certificate OCR parsing, ladle chemistry verification, and ASTM specification checks.
                </p>
              </Link>

              <Link
                href="/requests"
                className="p-4 bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-lg hover:border-zinc-400 dark:hover:border-zinc-600 transition-colors group"
              >
                <div className="flex items-center justify-between mb-2">
                  <Truck size={18} className="text-zinc-700 dark:text-zinc-300" />
                  <span className="text-[10px] font-mono text-zinc-400 group-hover:text-zinc-900 dark:group-hover:text-zinc-100">
                    Track &rarr;
                  </span>
                </div>
                <h3 className="font-semibold text-xs text-zinc-900 dark:text-zinc-100">My Consignments</h3>
                <p className="text-[11px] text-zinc-500 dark:text-zinc-400 mt-1 leading-relaxed">
                  Track active inter-CPSE loan transfers, transit logistics, and gate pass approvals.
                </p>
              </Link>
            </div>

            {/* Active Requisitions */}
            <Card title="Active Spare Requisitions" icon={Truck}>
              {loading ? (
                <div className="space-y-2 py-2">
                  <Skeleton className="h-8 w-full" />
                  <Skeleton className="h-8 w-full" />
                  <Skeleton className="h-8 w-full" />
                </div>
              ) : requests.length === 0 ? (
                <div className="py-8 text-center text-xs text-zinc-400 font-mono">
                  No active loan requisitions for {cpse}. Use Surplus Discovery to find parts.
                </div>
              ) : (
                <div className="divide-y divide-zinc-100 dark:divide-zinc-800/80">
                  {requests.slice(0, 5).map((req: any) => (
                    <div key={req.id} className="py-2.5 flex items-center justify-between gap-4 text-xs">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-mono font-semibold text-zinc-900 dark:text-zinc-100">
                            {req.req_number || `REQ-${req.id}`}
                          </span>
                          <span className="text-zinc-400">·</span>
                          <span className="font-mono text-zinc-600 dark:text-zinc-400">
                            {req.requesting_cpse} &rarr; {req.fulfilling_cpse}
                          </span>
                        </div>
                        <p className="text-zinc-500 dark:text-zinc-400 mt-0.5">
                          SKU: <span className="font-mono text-zinc-800 dark:text-zinc-200">{req.sku_code}</span> (Qty: {req.quantity_requested})
                        </p>
                      </div>
                      <div className="text-right flex items-center gap-2">
                        <span className="px-2 py-0.5 text-[10px] font-mono rounded bg-zinc-100 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 border border-zinc-200 dark:border-zinc-700">
                          {req.status}
                        </span>
                        <Link
                          href={`/requests/${req.id}`}
                          className="text-[11px] font-medium text-zinc-900 dark:text-zinc-100 hover:underline"
                        >
                          View &rarr;
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
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Card title="Pending Loan Approvals (Stores Action)" icon={Truck}>
                {loading ? (
                  <div className="space-y-2 py-2">
                    <Skeleton className="h-8 w-full" />
                    <Skeleton className="h-8 w-full" />
                  </div>
                ) : requests.filter((r) => r.status === 'REQUESTED').length === 0 ? (
                  <div className="py-8 text-center text-xs text-zinc-400 font-mono">
                    All inter-CPSE loan requests cleared for {cpse}. Zero pending backlogs.
                  </div>
                ) : (
                  <div className="divide-y divide-zinc-100 dark:divide-zinc-800/80">
                    {requests
                      .filter((r) => r.status === 'REQUESTED')
                      .slice(0, 4)
                      .map((req) => (
                        <div key={req.id} className="py-2.5 flex items-center justify-between gap-4 text-xs">
                          <div>
                            <p className="font-mono font-semibold text-zinc-900 dark:text-zinc-100">
                              {req.req_number || `REQ-${req.id}`}
                            </p>
                            <p className="text-zinc-500 dark:text-zinc-400 mt-0.5">
                              {req.requesting_cpse} requesting <span className="font-mono">{req.sku_code}</span> (Qty: {req.quantity_requested})
                            </p>
                          </div>
                          <Link
                            href={`/requests/${req.id}`}
                            className="px-2.5 py-1 bg-zinc-900 hover:bg-zinc-800 text-white dark:bg-zinc-100 dark:hover:bg-zinc-200 dark:text-zinc-900 rounded text-xs font-medium transition-colors"
                          >
                            Authorize
                          </Link>
                        </div>
                      ))}
                  </div>
                )}
              </Card>

              <Card title="Stock Ledger Actions" icon={Package}>
                <div className="space-y-3 text-xs">
                  <p className="text-zinc-600 dark:text-zinc-400 leading-relaxed">
                    Manage sovereign surplus stock (&gt;180 days idle), review reservation holds, and coordinate emergency inter-refinery dispatches.
                  </p>
                  <div className="pt-1 flex flex-col gap-2">
                    <Link
                      href="/inventory"
                      className="py-1.5 px-3 bg-zinc-900 hover:bg-zinc-800 text-white dark:bg-zinc-100 dark:hover:bg-zinc-200 dark:text-zinc-900 font-medium text-xs rounded-md flex items-center justify-between transition-colors"
                    >
                      <span>Open Live Stock Ledger</span>
                      <ArrowRight size={13} />
                    </Link>
                    <Link
                      href="/discover"
                      className="py-1.5 px-3 bg-zinc-100 dark:bg-zinc-800 hover:bg-zinc-200 dark:hover:bg-zinc-700 text-zinc-700 dark:text-zinc-300 font-medium text-xs rounded-md flex items-center justify-between transition-colors"
                    >
                      <span>Search Sister CPSE Surplus Stock</span>
                      <ArrowRight size={13} />
                    </Link>
                  </div>
                </div>
              </Card>
            </div>
          </div>
        )}

        {/* 3. TECHNICAL AUTHORITY WORKSPACE */}
        {role === 'TECHNICAL_AUTHORITY' && (
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <div className="p-4 bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-lg">
                <FileCheck2 size={18} className="text-zinc-700 dark:text-zinc-300 mb-2" />
                <h3 className="font-semibold text-xs text-zinc-900 dark:text-zinc-100">
                  HITL Triage Queue
                </h3>
                <p className="text-[11px] text-zinc-500 dark:text-zinc-400 mt-1">
                  {hitlQueue.length} items flagged with 80%–94% compatibility requiring QA-QC metallurgical sign-off.
                </p>
                <Link
                  href="/inventory"
                  className="mt-2.5 inline-flex items-center gap-1 text-xs font-medium text-zinc-900 dark:text-zinc-100 hover:underline"
                >
                  Open Triage Desk &rarr;
                </Link>
              </div>

              <div className="p-4 bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-lg">
                <Layers size={18} className="text-zinc-700 dark:text-zinc-300 mb-2" />
                <h3 className="font-semibold text-xs text-zinc-900 dark:text-zinc-100">
                  21 Safety Gates
                </h3>
                <p className="text-[11px] text-zinc-500 dark:text-zinc-400 mt-1">
                  ASME B16.5, ASTM A105 vs IS 2062 metallurgy DAG, and API 6D dimensional zero-tolerance.
                </p>
                <Link
                  href="/discover"
                  className="mt-2.5 inline-flex items-center gap-1 text-xs font-medium text-zinc-900 dark:text-zinc-100 hover:underline"
                >
                  Evaluate Pairwise Rules &rarr;
                </Link>
              </div>

              <div className="p-4 bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-lg">
                <ShieldAlert size={18} className="text-zinc-700 dark:text-zinc-300 mb-2" />
                <h3 className="font-semibold text-xs text-zinc-900 dark:text-zinc-100">
                  MTC Ladle Chemistry
                </h3>
                <p className="text-[11px] text-zinc-500 dark:text-zinc-400 mt-1">
                  IIW carbon equivalent weldability (&le;0.43%) and PREN pitting resistance (&ge;32) compliance.
                </p>
                <Link
                  href="/upload"
                  className="mt-2.5 inline-flex items-center gap-1 text-xs font-medium text-zinc-900 dark:text-zinc-100 hover:underline"
                >
                  MTC Document Review &rarr;
                </Link>
              </div>
            </div>

            <Card title="Pending HITL Tolerance Discrepancies" icon={AlertTriangle}>
              {hitlQueue.length === 0 ? (
                <div className="py-8 text-center text-xs text-zinc-400 font-mono">
                  Zero pending triage disputes. All mechanical tolerances evaluated deterministic.
                </div>
              ) : (
                <div className="divide-y divide-zinc-100 dark:divide-zinc-800/80">
                  {hitlQueue.slice(0, 5).map((item: any) => (
                    <div key={item.id} className="py-2.5 flex items-center justify-between gap-4 text-xs">
                      <div>
                        <span className="font-mono font-semibold text-zinc-900 dark:text-zinc-100">
                          {item.sku_code}
                        </span>
                        <p className="text-zinc-500 dark:text-zinc-400 mt-0.5">
                          {item.raw_description || item.description}
                        </p>
                      </div>
                      <Link
                        href="/inventory"
                        className="px-2.5 py-1 bg-zinc-100 dark:bg-zinc-800 hover:bg-zinc-200 dark:hover:bg-zinc-700 text-zinc-800 dark:text-zinc-200 rounded text-xs font-medium"
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
          <div className="space-y-4">
            <div className="p-4 bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-lg">
              <div className="flex items-center gap-2 mb-1.5">
                <QrCode size={18} className="text-zinc-700 dark:text-zinc-300" />
                <h3 className="font-semibold text-xs text-zinc-900 dark:text-zinc-100">
                  CISF Perimeter Gate Pass Terminal
                </h3>
              </div>
              <p className="text-xs text-zinc-500 dark:text-zinc-400 leading-relaxed max-w-3xl">
                Digital verification and tamper-evident stamping of inter-CPSE consignment transport passes. All passes feature offline air-gapped SVG QR bit-matrices containing SHA-256 digital seals.
              </p>
              <div className="mt-3">
                <Link
                  href="/requests"
                  className="py-1.5 px-3 bg-zinc-900 hover:bg-zinc-800 text-white dark:bg-zinc-100 dark:hover:bg-zinc-200 dark:text-zinc-900 font-medium text-xs rounded-md inline-flex items-center gap-1.5 transition-colors"
                >
                  <QrCode size={13} />
                  <span>Open Active Gate Passes Queue</span>
                </Link>
              </div>
            </div>

            <Card title="Consignments Ready for Gate Verification" icon={Truck}>
              <div className="divide-y divide-zinc-100 dark:divide-zinc-800/80">
                {requests.slice(0, 5).map((req) => (
                  <div key={req.id} className="py-2.5 flex items-center justify-between gap-4 text-xs">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-mono font-semibold text-zinc-900 dark:text-zinc-100">
                          {req.req_number || `REQ-${req.id}`}
                        </span>
                        <span className="text-zinc-400">|</span>
                        <span className="font-mono text-zinc-600 dark:text-zinc-400">
                          {req.fulfilling_cpse} &rarr; {req.requesting_cpse}
                        </span>
                      </div>
                      <p className="text-zinc-500 dark:text-zinc-400 mt-0.5">
                        Material: <span className="font-mono">{req.sku_code}</span> · Status: <span className="font-medium text-zinc-800 dark:text-zinc-200">{req.status}</span>
                      </p>
                    </div>
                    <Link
                      href={`/requests/${req.id}`}
                      className="px-2.5 py-1 bg-zinc-900 hover:bg-zinc-800 text-white dark:bg-zinc-100 dark:hover:bg-zinc-200 dark:text-zinc-900 rounded text-xs font-medium transition-colors"
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
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <div className="p-4 bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-lg">
                <ShieldCheck size={18} className="text-zinc-700 dark:text-zinc-300 mb-2" />
                <h3 className="font-semibold text-xs text-zinc-900 dark:text-zinc-100">
                  SHA-256 Merkle Ledger
                </h3>
                <p className="text-[11px] text-zinc-500 dark:text-zinc-400 mt-1">
                  Verification status: <strong className="text-zinc-900 dark:text-zinc-100">{auditVerified ? '100% VALID' : 'VERIFYING'}</strong>
                </p>
                <Link
                  href="/audit"
                  className="mt-2.5 inline-flex items-center gap-1 text-xs font-medium text-zinc-900 dark:text-zinc-100 hover:underline"
                >
                  Verify Merkle Hash Chain &rarr;
                </Link>
              </div>

              <div className="p-4 bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-lg">
                <FileSpreadsheet size={18} className="text-zinc-700 dark:text-zinc-300 mb-2" />
                <h3 className="font-semibold text-xs text-zinc-900 dark:text-zinc-100">
                  CAG Statutory Export
                </h3>
                <p className="text-[11px] text-zinc-500 dark:text-zinc-400 mt-1">
                  RFC 4180 audit ledger export with previous block hash continuity.
                </p>
                <Link
                  href="/audit"
                  className="mt-2.5 inline-flex items-center gap-1 text-xs font-medium text-zinc-900 dark:text-zinc-100 hover:underline"
                >
                  Download Audit CSV &rarr;
                </Link>
              </div>

              <div className="p-4 bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-lg">
                <Building2 size={18} className="text-zinc-700 dark:text-zinc-300 mb-2" />
                <h3 className="font-semibold text-xs text-zinc-900 dark:text-zinc-100">
                  Cross-CPSE Price Masking
                </h3>
                <p className="text-[11px] text-zinc-500 dark:text-zinc-400 mt-1">
                  Commercial values stripped on inter-entity discovery to prevent anti-competitive leakage.
                </p>
                <Link
                  href="/inventory"
                  className="mt-2.5 inline-flex items-center gap-1 text-xs font-medium text-zinc-900 dark:text-zinc-100 hover:underline"
                >
                  Review Ledger &rarr;
                </Link>
              </div>
            </div>

            <Card title="Recent Sovereign Audit Trail Blocks" icon={ShieldCheck}>
              <div className="divide-y divide-zinc-100 dark:divide-zinc-800/80 font-mono text-xs">
                {auditLogs.slice(0, 5).map((log: any) => (
                  <div key={log.id || log.log_id} className="py-2 flex items-center justify-between gap-4">
                    <div>
                      <span className="font-semibold text-zinc-900 dark:text-zinc-100">
                        {log.log_id || `LOG-${log.id}`}
                      </span>
                      <p className="text-[11px] text-zinc-500 mt-0.5">
                        {log.action_name} by @{log.actor_name} ({log.cpse})
                      </p>
                    </div>
                    <span className="text-[10px] text-zinc-400 truncate max-w-[200px]">
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
          <div className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
              <Link
                href="/inventory"
                className="p-3.5 bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-lg hover:border-zinc-400 dark:hover:border-zinc-600 transition-colors"
              >
                <h4 className="font-semibold text-xs text-zinc-900 dark:text-zinc-100">Master Catalog</h4>
                <p className="text-[11px] text-zinc-500 mt-1">View inventory across all CPSEs.</p>
              </Link>
              <Link
                href="/discover"
                className="p-3.5 bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-lg hover:border-zinc-400 dark:hover:border-zinc-600 transition-colors"
              >
                <h4 className="font-semibold text-xs text-zinc-900 dark:text-zinc-100">Compatibility Mesh</h4>
                <p className="text-[11px] text-zinc-500 mt-1">Run vector + deterministic rules.</p>
              </Link>
              <Link
                href="/audit"
                className="p-3.5 bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-lg hover:border-zinc-400 dark:hover:border-zinc-600 transition-colors"
              >
                <h4 className="font-semibold text-xs text-zinc-900 dark:text-zinc-100">Audit Trail</h4>
                <p className="text-[11px] text-zinc-500 mt-1">Cryptographic ledger records.</p>
              </Link>
              <Link
                href="/admin/users"
                className="p-3.5 bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-lg hover:border-zinc-400 dark:hover:border-zinc-600 transition-colors"
              >
                <div className="flex items-center justify-between">
                  <h4 className="font-semibold text-xs text-zinc-900 dark:text-zinc-100">User Approvals</h4>
                  <span className="px-1.5 py-0.2 text-[9px] font-mono font-medium bg-zinc-900 text-white dark:bg-zinc-100 dark:text-zinc-900 rounded">ADMIN</span>
                </div>
                <p className="text-[11px] text-zinc-500 mt-1">Review pending registrations.</p>
              </Link>
            </div>
          </div>
        )}
      </div>
    </ProtectedRoute>
  );
}
