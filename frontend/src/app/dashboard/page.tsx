"use client";

import React, { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { useAuth } from '@/context/AuthContext';
import { useTheme } from '@/components/ThemeProvider';
import { ProtectedRoute } from '@/components/ProtectedRoute';
import { RefreshCw } from 'lucide-react';
import { api } from '@/lib/api';

import { KpiStrip } from '@/components/dashboard/KpiStrip';
import { SiteEngineerWorkspace } from '@/components/dashboard/workspaces/SiteEngineerWorkspace';
import { MaterialsManagerWorkspace } from '@/components/dashboard/workspaces/MaterialsManagerWorkspace';
import { TechnicalAuthorityWorkspace } from '@/components/dashboard/workspaces/TechnicalAuthorityWorkspace';
import { CisfWorkspace } from '@/components/dashboard/workspaces/CisfWorkspace';
import { VigilanceAuditorWorkspace } from '@/components/dashboard/workspaces/VigilanceAuditorWorkspace';
import { SuperAdminWorkspace } from '@/components/dashboard/workspaces/SuperAdminWorkspace';

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

  // Progressive parallel data loading: fast telemetry renders immediately without waiting on slow Merkle checks
  const loadDashboardData = useCallback(async () => {
    setLoading(true);
    setError(null);

    // 1. Stage 1: Fast inventory stats & active requisitions
    const stage1Promises = Promise.allSettled([
      api.getInventoryStats(),
      api.getRequests(cpse),
    ]).then(([statsRes, reqsRes]) => {
      if (statsRes.status === 'fulfilled') {
        setStats(statsRes.value);
      }
      if (reqsRes.status === 'fulfilled') {
        setRequests(Array.isArray(reqsRes.value) ? reqsRes.value : []);
      }
    });

    // 2. Stage 2: Parallel background streams (HITL, Audit logs, and cryptographic verification)
    const stage2Promises = Promise.allSettled([
      api.getHitlQueue(),
      api.getAuditLogs({ limit: 5 }),
      api.verifyAuditChain(),
    ]).then(([hitlRes, auditRes, verifyRes]) => {
      if (hitlRes.status === 'fulfilled') {
        setHitlQueue(Array.isArray(hitlRes.value) ? hitlRes.value : []);
      }
      if (auditRes.status === 'fulfilled') {
        setAuditLogs(Array.isArray(auditRes.value) ? auditRes.value : auditRes.value?.items || []);
      }
      if (verifyRes.status === 'fulfilled') {
        setAuditVerified(verifyRes.value?.is_valid ?? false);
      }
    });

    try {
      await Promise.allSettled([stage1Promises, stage2Promises]);
    } catch (err: any) {
      console.error('Failed to load dashboard data:', err);
      setError('Unable to load live telemetry from backend mesh.');
    } finally {
      setLoading(false);
    }
  }, [cpse]);

  useEffect(() => {
    loadDashboardData();
  }, [loadDashboardData]);

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

        {/* Global Live KPI Strip with progressive hydration */}
        <KpiStrip stats={stats} auditVerified={auditVerified} loading={loading && !stats} />

        {/* ── WORKSPACE VIEWS ACCORDING TO ROLE ──────────────────────────── */}
        {role === 'SITE_ENGINEER' && (
          <SiteEngineerWorkspace requests={requests} loading={loading} cpse={cpse} />
        )}

        {role === 'MATERIALS_MANAGER' && (
          <MaterialsManagerWorkspace requests={requests} loading={loading} cpse={cpse} />
        )}

        {role === 'TECHNICAL_AUTHORITY' && (
          <TechnicalAuthorityWorkspace hitlQueue={hitlQueue} loading={loading} />
        )}

        {role === 'CISF_SECURITY' && (
          <CisfWorkspace requests={requests} loading={loading} />
        )}

        {role === 'VIGILANCE_AUDITOR' && (
          <VigilanceAuditorWorkspace
            auditLogs={auditLogs}
            auditVerified={auditVerified}
            loading={loading}
          />
        )}

        {role === 'SUPER_ADMIN' && <SuperAdminWorkspace />}
      </div>
    </ProtectedRoute>
  );
}
