"use client";

import React, { useState, useEffect, useMemo } from 'react';
import { Card, SideDrawer, Skeleton } from '@/components/ui';
import {
  ShieldCheck,
  Download,
  Search,
  Filter,
  CheckCircle2,
  Lock,
  RefreshCw,
  ChevronLeft,
  ChevronRight,
  AlertTriangle,
  X,
  Layers,
  FileCode,
} from 'lucide-react';
import { exportToCSV } from '@/lib/exportUtils';
import { api } from '@/lib/api';
import { ProtectedRoute } from '@/components/ProtectedRoute';

interface AuditLogEntry {
  id?: number | string;
  block_number?: number;
  timestamp: string;
  action_category?: string;
  category?: string;
  action: string;
  actor: string;
  cpse: string;
  depot?: string;
  reference_id?: string;
  hash?: string;
  current_hash?: string;
  prev_hash?: string;
  previous_hash?: string;
  payload?: any;
}

const CATEGORIES = [
  'ALL',
  'STATUS_CHANGE',
  'REQUISITION',
  'GATE_PASS',
  'DISPATCH',
  'MTC_INGEST',
  'DELIVERY',
];

const CPSE_LIST = ['ALL', 'OIL', 'IOCL', 'ONGC', 'BPCL', 'HPCL', 'GAIL', 'NRL'];

export default function AuditTrailPage() {
  const [logs, setLogs] = useState<AuditLogEntry[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Verification State
  const [chainValid, setChainValid] = useState<boolean | null>(null);
  const [verifying, setVerifying] = useState<boolean>(false);
  const [verificationStats, setVerificationStats] = useState<any>(null);

  // Filters & Search
  const [selectedCategory, setSelectedCategory] = useState<string>('ALL');
  const [selectedCpse, setSelectedCpse] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [page, setPage] = useState<number>(1);
  const pageSize = 25;
  const [totalCount, setTotalCount] = useState<number>(0);

  // Detail Inspector Drawer
  const [inspectEntry, setInspectEntry] = useState<AuditLogEntry | null>(null);

  // Fetch real audit entries
  const fetchAuditLogs = async () => {
    setLoading(true);
    setError(null);
    try {
      const skip = (page - 1) * pageSize;
      const res = await api.getAuditLogs({
        category: selectedCategory !== 'ALL' ? selectedCategory : undefined,
        cpse: selectedCpse !== 'ALL' ? selectedCpse : undefined,
        skip,
        limit: pageSize,
      });

      if (res && Array.isArray(res.items)) {
        setLogs(res.items);
        setTotalCount(res.total || res.items.length);
      } else if (Array.isArray(res)) {
        setLogs(res);
        setTotalCount(res.length);
      } else {
        setLogs([]);
        setTotalCount(0);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to fetch audit records');
      setLogs([]);
    } finally {
      setLoading(false);
    }
  };

  // Run cryptographic chain validation
  const runChainVerification = async () => {
    setVerifying(true);
    try {
      const res = await api.verifyAuditChain();
      setChainValid(Boolean(res.is_valid));
      setVerificationStats(res);
    } catch (err: any) {
      setChainValid(false);
      alert(`Chain verification failed: ${err.message}`);
    } finally {
      setVerifying(false);
    }
  };

  useEffect(() => {
    fetchAuditLogs();
    runChainVerification();
  }, [page, selectedCategory, selectedCpse]);

  // Client-side text filter on current page items
  const filteredLogs = useMemo(() => {
    if (!searchQuery.trim()) return logs;
    const q = searchQuery.toLowerCase();
    return logs.filter(
      (l) =>
        l.action?.toLowerCase().includes(q) ||
        l.actor?.toLowerCase().includes(q) ||
        l.reference_id?.toLowerCase().includes(q) ||
        l.hash?.toLowerCase().includes(q) ||
        l.current_hash?.toLowerCase().includes(q)
    );
  }, [logs, searchQuery]);

  const handleExportCSV = () => {
    if (filteredLogs.length === 0) {
      alert('No audit records to export.');
      return;
    }
    const flat = filteredLogs.map((l) => ({
      Block: l.block_number || l.id,
      Timestamp: l.timestamp,
      Category: l.action_category || l.category || 'SYSTEM',
      Action: l.action,
      Actor: l.actor,
      CPSE: l.cpse,
      Reference_ID: l.reference_id || '',
      Current_Hash: l.hash || l.current_hash || '',
      Previous_Hash: l.prev_hash || l.previous_hash || '',
    }));
    exportToCSV(flat, `samanvay_audit_ledger_${new Date().toISOString().slice(0, 10)}.csv`);
  };

  const totalPages = Math.ceil(totalCount / pageSize) || 1;

  return (
    <ProtectedRoute allowedRoles={['VIGILANCE_AUDITOR', 'SUPER_ADMIN']}>
      <div className="space-y-4 max-w-7xl mx-auto pb-10">
        {/* Header & Verification Bar */}
        <div className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-lg p-4 transition-colors">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-sm font-semibold text-zinc-900 dark:text-zinc-100 font-sans">
                  Sovereign Cryptographic Audit Ledger
                </h1>
                <span className="px-1.5 py-0.2 text-[10px] font-mono text-zinc-500 bg-zinc-100 dark:bg-zinc-800 rounded border border-zinc-200 dark:border-zinc-750">
                  SHA-256 Merkle Chain
                </span>
              </div>
              <p className="text-xs text-zinc-500 dark:text-zinc-400 font-mono mt-0.5">
                RFC-4180 audit records with linked block hashes. Validated against CAG oversight requirements.
              </p>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={runChainVerification}
                disabled={verifying}
                className={`px-2.5 py-1.5 rounded-md text-xs font-mono font-medium flex items-center gap-1.5 border transition-colors ${
                  chainValid
                    ? 'bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border-emerald-500/20'
                    : 'bg-zinc-100 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 border-zinc-200 dark:border-zinc-700'
                }`}
              >
                <RefreshCw size={12} className={verifying ? 'animate-spin' : ''} />
                <span>{chainValid ? 'Merkle Chain Valid' : 'Verify Chain'}</span>
              </button>

              <button
                onClick={handleExportCSV}
                className="px-2.5 py-1.5 bg-zinc-900 hover:bg-zinc-800 text-white dark:bg-zinc-100 dark:hover:bg-zinc-200 dark:text-zinc-900 rounded-md text-xs font-medium flex items-center gap-1.5 transition-colors"
              >
                <Download size={12} />
                <span>Export CSV</span>
              </button>
            </div>
          </div>

          {/* Filters Bar */}
          <div className="mt-3 flex flex-wrap items-center gap-2 text-xs font-mono">
            <div className="relative flex-1 min-w-[200px]">
              <Search size={13} className="absolute left-2.5 top-2 text-zinc-400" />
              <input
                type="text"
                placeholder="Search action, actor, SKU, or block hash..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-7 pr-3 py-1 bg-zinc-50 dark:bg-zinc-800/80 border border-zinc-200 dark:border-zinc-700/80 rounded-md text-xs text-zinc-900 dark:text-zinc-100 placeholder:text-zinc-400 outline-hidden font-sans"
              />
            </div>

            <select
              value={selectedCategory}
              onChange={(e) => {
                setSelectedCategory(e.target.value);
                setPage(1);
              }}
              className="bg-zinc-50 dark:bg-zinc-800/80 border border-zinc-200 dark:border-zinc-700/80 rounded-md px-2 py-1 text-xs text-zinc-800 dark:text-zinc-200 outline-hidden"
            >
              {CATEGORIES.map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>

            <select
              value={selectedCpse}
              onChange={(e) => {
                setSelectedCpse(e.target.value);
                setPage(1);
              }}
              className="bg-zinc-50 dark:bg-zinc-800/80 border border-zinc-200 dark:border-zinc-700/80 rounded-md px-2 py-1 text-xs text-zinc-800 dark:text-zinc-200 outline-hidden"
            >
              {CPSE_LIST.map((c) => (
                <option key={c} value={c}>{c === 'ALL' ? 'All CPSEs' : c}</option>
              ))}
            </select>
          </div>
        </div>

        {error && (
          <div className="p-2.5 bg-rose-500/10 border border-rose-500/20 text-rose-700 dark:text-rose-400 text-xs font-mono rounded-lg flex items-center justify-between">
            <span>{error}</span>
            <button onClick={fetchAuditLogs} className="underline font-semibold ml-2">Retry</button>
          </div>
        )}

        {/* Cryptographic Ledger Table (38px Compact Rows) */}
        <div className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-lg overflow-hidden shadow-2xs">
          <div className="overflow-x-auto">
            <table className="w-full text-left compact-table border-collapse">
              <thead>
                <tr className="border-b border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-900/80">
                  <th className="w-16">Block</th>
                  <th>Timestamp</th>
                  <th>Category</th>
                  <th>Action</th>
                  <th>Actor</th>
                  <th>CPSE</th>
                  <th>SHA-256 Hash</th>
                  <th className="text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-100 dark:divide-zinc-800/80 text-xs font-mono">
                {loading ? (
                  Array.from({ length: 10 }).map((_, i) => (
                    <tr key={i} className="h-[38px]">
                      <td><Skeleton className="h-4 w-10" /></td>
                      <td><Skeleton className="h-4 w-28" /></td>
                      <td><Skeleton className="h-4 w-20" /></td>
                      <td><Skeleton className="h-4 w-32" /></td>
                      <td><Skeleton className="h-4 w-20" /></td>
                      <td><Skeleton className="h-4 w-12" /></td>
                      <td><Skeleton className="h-4 w-36" /></td>
                      <td className="text-right"><Skeleton className="h-4 w-14 ml-auto" /></td>
                    </tr>
                  ))
                ) : filteredLogs.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="py-12 text-center text-zinc-400 font-mono text-xs">
                      No cryptographic audit records found matching current query.
                    </td>
                  </tr>
                ) : (
                  filteredLogs.map((log) => {
                    const blockNum = log.block_number || log.id || 1;
                    const cat = log.action_category || log.category || 'SYSTEM';
                    const hash = log.hash || log.current_hash || '0x...';

                    return (
                      <tr
                        key={log.id || `${blockNum}-${log.timestamp}`}
                        onClick={() => setInspectEntry(log)}
                        className="hover:bg-zinc-50 dark:hover:bg-zinc-800/50 cursor-pointer transition-colors"
                      >
                        <td className="tabular-nums font-semibold text-zinc-900 dark:text-zinc-100">
                          #{blockNum}
                        </td>

                        <td className="text-zinc-500 whitespace-nowrap text-[11px]">
                          {log.timestamp ? new Date(log.timestamp).toLocaleString('en-IN', { dateStyle: 'short', timeStyle: 'medium' }) : '—'}
                        </td>

                        <td>
                          <span className="px-1.5 py-0.2 text-[10px] font-mono rounded bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-400 border border-zinc-200 dark:border-zinc-700">
                            {cat}
                          </span>
                        </td>

                        <td className="text-zinc-800 dark:text-zinc-200 font-medium">
                          {log.action}
                        </td>

                        <td className="text-zinc-600 dark:text-zinc-400">
                          @{log.actor}
                        </td>

                        <td>
                          <span className="font-semibold text-zinc-800 dark:text-zinc-200">
                            {log.cpse}
                          </span>
                        </td>

                        <td className="text-zinc-400 font-mono text-[11px] truncate max-w-[160px]">
                          {hash}
                        </td>

                        <td className="text-right">
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              setInspectEntry(log);
                            }}
                            className="px-2 py-1 bg-zinc-100 dark:bg-zinc-800 hover:bg-zinc-200 dark:hover:bg-zinc-700 text-zinc-700 dark:text-zinc-300 rounded text-[11px] font-medium transition-colors"
                          >
                            Inspect
                          </button>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <div className="p-3 border-t border-zinc-200 dark:border-zinc-800 flex items-center justify-between text-xs font-mono bg-zinc-50/50 dark:bg-zinc-900/50">
            <span className="text-zinc-500">
              Page {page} of {totalPages} ({totalCount.toLocaleString('en-IN')} total entries)
            </span>

            <div className="flex items-center gap-2">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1 || loading}
                className="px-2.5 py-1 bg-white dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded text-zinc-700 dark:text-zinc-300 hover:bg-zinc-100 dark:hover:bg-zinc-700 disabled:opacity-40 transition-colors flex items-center gap-1"
              >
                <ChevronLeft size={13} /> Prev
              </button>
              <span className="px-2 font-semibold text-zinc-900 dark:text-zinc-100">{page}</span>
              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page >= totalPages || loading}
                className="px-2.5 py-1 bg-white dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded text-zinc-700 dark:text-zinc-300 hover:bg-zinc-100 dark:hover:bg-zinc-700 disabled:opacity-40 transition-colors flex items-center gap-1"
              >
                Next <ChevronRight size={13} />
              </button>
            </div>
          </div>
        </div>

        {/* ── SLIDING SIDE INSPECTOR DRAWER ────────────────────────────────── */}
        <SideDrawer
          isOpen={!!inspectEntry}
          onClose={() => setInspectEntry(null)}
          title={`Block #${inspectEntry?.block_number || inspectEntry?.id || '1'}`}
          subtitle={`${inspectEntry?.action_category || inspectEntry?.category || 'SYSTEM'} · ${inspectEntry?.cpse}`}
        >
          {inspectEntry && (
            <div className="space-y-4 font-mono text-xs">
              <div className="p-3 bg-zinc-50 dark:bg-zinc-800/60 rounded-lg border border-zinc-200 dark:border-zinc-800 space-y-1.5">
                <span className="text-[10px] text-zinc-400 uppercase">Operational Action</span>
                <p className="font-semibold text-zinc-900 dark:text-zinc-100 font-sans text-sm">
                  {inspectEntry.action}
                </p>
                <p className="text-zinc-500">
                  Executed by: <strong className="text-zinc-700 dark:text-zinc-300">@{inspectEntry.actor}</strong> ({inspectEntry.cpse})
                </p>
                <p className="text-zinc-400 text-[11px]">
                  Timestamp: {new Date(inspectEntry.timestamp).toISOString()}
                </p>
              </div>

              {/* Cryptographic Hashes */}
              <div>
                <h4 className="text-[11px] font-semibold uppercase text-zinc-400 mb-2">
                  Cryptographic Hashes
                </h4>
                <div className="p-3 bg-zinc-50 dark:bg-zinc-800/40 rounded-lg border border-zinc-200 dark:border-zinc-800 space-y-2">
                  <div>
                    <span className="text-[10px] text-zinc-400 block">Current Block Hash (SHA-256)</span>
                    <span className="text-[11px] text-zinc-800 dark:text-zinc-200 break-all select-all font-mono">
                      {inspectEntry.hash || inspectEntry.current_hash || '—'}
                    </span>
                  </div>
                  <div>
                    <span className="text-[10px] text-zinc-400 block">Previous Block Hash (Chain Link)</span>
                    <span className="text-[11px] text-zinc-500 break-all select-all font-mono">
                      {inspectEntry.prev_hash || inspectEntry.previous_hash || 'GENESIS_BLOCK_0000000000000000000000000000000000000000'}
                    </span>
                  </div>
                </div>
              </div>

              {/* Payload Data */}
              {inspectEntry.payload && (
                <div>
                  <h4 className="text-[11px] font-semibold uppercase text-zinc-400 mb-2">
                    Block Payload JSON
                  </h4>
                  <pre className="p-3 bg-zinc-950 text-zinc-300 text-[11px] rounded-lg overflow-x-auto max-h-60 border border-zinc-800">
                    {JSON.stringify(inspectEntry.payload, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          )}
        </SideDrawer>
      </div>
    </ProtectedRoute>
  );
}
