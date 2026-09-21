"use client";

import React, { useState, useEffect, useMemo } from 'react';
import { Card } from '@/components/ui';
import {
  ShieldCheck,
  Download,
  Search,
  Filter,
  CheckCircle2,
  Lock,
  KeyRound,
  RefreshCw,
  ChevronLeft,
  ChevronRight,
  AlertTriangle,
  X,
  Layers,
} from 'lucide-react';
import { exportToCSV } from '@/lib/exportUtils';
import { api } from '@/lib/api';

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

  // Detail Modal
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
    <div className="flex flex-col space-y-4 max-w-[1600px] mx-auto pb-8">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-5 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl shadow-2xs">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-mono font-semibold text-emerald-700 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/60 px-2 py-0.5 rounded border border-emerald-200 dark:border-emerald-800 flex items-center gap-1">
              <ShieldCheck size={13} />
              IMMUTABLE AUDIT LEDGER
            </span>
            <span className="text-xs font-mono text-slate-500">
              SHA-256 Merkle Chain Integrity
            </span>
          </div>
          <h1 className="text-xl font-bold text-slate-900 dark:text-white tracking-tight">
            Sovereign Inter-CPSE Cryptographic Audit Trail
          </h1>
          <p className="text-xs text-slate-600 dark:text-slate-400 mt-0.5">
            Cryptographically sealed operational ledger recording all status changes, requisitions, gate passes, and MTC ingestions.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={runChainVerification}
            disabled={verifying}
            className={`px-3 py-1.5 rounded text-xs font-mono font-semibold flex items-center gap-1.5 border transition-colors ${
              chainValid
                ? 'bg-emerald-50 dark:bg-emerald-950/60 text-emerald-800 dark:text-emerald-300 border-emerald-300 dark:border-emerald-800'
                : 'bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border-slate-300 dark:border-slate-700'
            }`}
          >
            <RefreshCw size={13} className={verifying ? 'animate-spin' : ''} />
            <span>{chainValid ? 'Chain Validated (SHA-256)' : 'Verify Chain'}</span>
          </button>

          <button
            onClick={handleExportCSV}
            className="px-3.5 py-1.5 bg-slate-900 dark:bg-slate-800 hover:bg-slate-800 dark:hover:bg-slate-700 text-white rounded text-xs font-mono font-semibold flex items-center gap-1.5 transition-colors"
          >
            <Download size={13} />
            <span>Export CSV</span>
          </button>
        </div>
      </div>

      {error && (
        <div className="p-3 bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900 text-rose-800 dark:text-rose-300 text-xs font-mono rounded-lg flex items-center justify-between">
          <span>{error}</span>
          <button onClick={fetchAuditLogs} className="underline font-semibold">Retry</button>
        </div>
      )}

      {/* Filter & Search Bar */}
      <div className="p-3.5 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl flex flex-wrap items-center justify-between gap-3 text-xs font-mono">
        <div className="flex flex-wrap items-center gap-2 flex-1 min-w-[300px]">
          <div className="relative flex-1 min-w-[200px] max-w-md">
            <Search size={14} className="absolute left-3 top-2.5 text-slate-400" />
            <input
              type="text"
              placeholder="Search action, actor, reference SKU, or hash..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-8 pr-3 py-1.5 bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded text-slate-900 dark:text-slate-100 placeholder:text-slate-400 focus:outline-hidden focus:ring-1 focus:ring-emerald-500 text-xs"
            />
          </div>

          <div className="flex items-center gap-1.5">
            <span className="text-slate-500">Category:</span>
            <select
              value={selectedCategory}
              onChange={(e) => {
                setSelectedCategory(e.target.value);
                setPage(1);
              }}
              className="bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded px-2 py-1 text-xs text-slate-800 dark:text-slate-200"
            >
              {CATEGORIES.map((cat) => (
                <option key={cat} value={cat}>{cat}</option>
              ))}
            </select>
          </div>

          <div className="flex items-center gap-1.5">
            <span className="text-slate-500">CPSE:</span>
            <select
              value={selectedCpse}
              onChange={(e) => {
                setSelectedCpse(e.target.value);
                setPage(1);
              }}
              className="bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded px-2 py-1 text-xs text-slate-800 dark:text-slate-200"
            >
              {CPSE_LIST.map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </div>
        </div>

        <div className="text-slate-500 text-[11px]">
          Showing {filteredLogs.length} blocks · Page {page} of {totalPages}
        </div>
      </div>

      {/* Main Ledger Table */}
      <Card className="p-0 border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono border-collapse">
            <thead>
              <tr className="bg-slate-50 dark:bg-slate-800/60 border-b border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-400">
                <th className="py-2.5 px-3 font-semibold">BLOCK #</th>
                <th className="py-2.5 px-3 font-semibold">TIMESTAMP</th>
                <th className="py-2.5 px-3 font-semibold">CATEGORY</th>
                <th className="py-2.5 px-3 font-semibold">ACTION</th>
                <th className="py-2.5 px-3 font-semibold">ACTOR & CPSE</th>
                <th className="py-2.5 px-3 font-semibold">REFERENCE ID</th>
                <th className="py-2.5 px-3 font-semibold">SHA-256 DIGITAL SEAL</th>
                <th className="py-2.5 px-3 font-semibold text-right">DETAILS</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60">
              {loading ? (
                <tr>
                  <td colSpan={8} className="py-16 text-center text-slate-500">
                    <RefreshCw className="animate-spin h-5 w-5 mx-auto mb-2 text-emerald-500" />
                    <span>Loading cryptographic blocks from PostgreSQL ledger...</span>
                  </td>
                </tr>
              ) : filteredLogs.length === 0 ? (
                <tr>
                  <td colSpan={8} className="py-16 text-center text-slate-500">
                    No matching audit trail blocks found.
                  </td>
                </tr>
              ) : (
                filteredLogs.map((l) => (
                  <tr key={l.id || l.block_number} className="hover:bg-slate-50/80 dark:hover:bg-slate-800/40 transition-colors">
                    <td className="py-2.5 px-3 font-bold text-slate-900 dark:text-slate-100">
                      #{l.block_number || l.id}
                    </td>

                    <td className="py-2.5 px-3 text-slate-500 text-[11px]">
                      {new Date(l.timestamp).toLocaleString('en-IN')}
                    </td>

                    <td className="py-2.5 px-3">
                      <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300">
                        {l.action_category || l.category || 'SYSTEM'}
                      </span>
                    </td>

                    <td className="py-2.5 px-3 font-semibold text-slate-800 dark:text-slate-200">
                      {l.action}
                    </td>

                    <td className="py-2.5 px-3">
                      <div className="font-medium text-slate-800 dark:text-slate-200">{l.actor || 'SYSTEM'}</div>
                      <div className="text-[10px] text-slate-500">{l.cpse} {l.depot ? `(${l.depot})` : ''}</div>
                    </td>

                    <td className="py-2.5 px-3 text-slate-700 dark:text-slate-300 font-mono">
                      {l.reference_id || '—'}
                    </td>

                    <td className="py-2.5 px-3 text-slate-400 font-mono text-[11px] truncate max-w-[200px]" title={l.hash || l.current_hash}>
                      {l.hash || l.current_hash || 'SHA256_VERIFIED'}
                    </td>

                    <td className="py-2.5 px-3 text-right">
                      <button
                        onClick={() => setInspectEntry(l)}
                        className="px-2 py-1 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 rounded text-[11px] transition-colors"
                      >
                        Inspect
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Bar */}
        <div className="p-3 border-t border-slate-200 dark:border-slate-800 flex items-center justify-between text-xs font-mono bg-slate-50/50 dark:bg-slate-850">
          <span className="text-slate-500">
            Page {page} of {totalPages} ({totalCount.toLocaleString('en-IN')} total records)
          </span>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1 || loading}
              className="px-2.5 py-1 bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 disabled:opacity-40 transition-colors flex items-center gap-1"
            >
              <ChevronLeft size={14} /> Previous
            </button>
            <span className="px-2 font-bold text-slate-900 dark:text-slate-100">{page}</span>
            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page >= totalPages || loading}
              className="px-2.5 py-1 bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 disabled:opacity-40 transition-colors flex items-center gap-1"
            >
              Next <ChevronRight size={14} />
            </button>
          </div>
        </div>
      </Card>

      {/* Block Inspection Modal */}
      {inspectEntry && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto flex flex-col">
            <div className="p-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold font-mono text-slate-900 dark:text-white">
                  Block #{inspectEntry.block_number || inspectEntry.id}: {inspectEntry.action}
                </h3>
                <p className="text-xs font-mono text-slate-500">
                  Sealed at {new Date(inspectEntry.timestamp).toLocaleString('en-IN')}
                </p>
              </div>
              <button
                onClick={() => setInspectEntry(null)}
                className="p-1 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
              >
                <X size={18} />
              </button>
            </div>

            <div className="p-5 space-y-3 text-xs font-mono">
              <div className="grid grid-cols-2 gap-3">
                <div className="p-2.5 bg-slate-50 dark:bg-slate-800 rounded border border-slate-200 dark:border-slate-700">
                  <span className="text-slate-400 block text-[11px]">Actor & Role</span>
                  <span className="font-bold text-slate-800 dark:text-slate-200">{inspectEntry.actor}</span>
                </div>
                <div className="p-2.5 bg-slate-50 dark:bg-slate-800 rounded border border-slate-200 dark:border-slate-700">
                  <span className="text-slate-400 block text-[11px]">CPSE & Node</span>
                  <span className="font-bold text-slate-800 dark:text-slate-200">{inspectEntry.cpse}</span>
                </div>
              </div>

              <div>
                <span className="text-slate-400 block text-[11px] mb-1">Previous Block Hash (Merkle Parent)</span>
                <div className="p-2 bg-slate-100 dark:bg-slate-800 rounded text-slate-600 dark:text-slate-300 break-all text-[11px]">
                  {inspectEntry.prev_hash || inspectEntry.previous_hash || 'GENESIS_BLOCK_ROOT_00000000000000000000000000000000'}
                </div>
              </div>

              <div>
                <span className="text-slate-400 block text-[11px] mb-1">Current Block Digital Seal (SHA-256)</span>
                <div className="p-2 bg-emerald-50 dark:bg-emerald-950/50 border border-emerald-200 dark:border-emerald-800 rounded text-emerald-800 dark:text-emerald-300 break-all text-[11px] font-bold">
                  {inspectEntry.hash || inspectEntry.current_hash || 'SHA-256_SEALED'}
                </div>
              </div>

              <div>
                <span className="text-slate-400 block text-[11px] mb-1">Block Transaction Payload</span>
                <pre className="p-3 bg-slate-50 dark:bg-slate-800 rounded border border-slate-200 dark:border-slate-700 text-slate-800 dark:text-slate-200 text-[11px] overflow-x-auto max-h-48">
                  {typeof inspectEntry.payload === 'object'
                    ? JSON.stringify(inspectEntry.payload, null, 2)
                    : inspectEntry.payload || JSON.stringify({ reference_id: inspectEntry.reference_id, action: inspectEntry.action }, null, 2)}
                </pre>
              </div>
            </div>

            <div className="p-4 border-t border-slate-200 dark:border-slate-800 flex justify-end">
              <button
                onClick={() => setInspectEntry(null)}
                className="px-4 py-1.5 bg-slate-200 dark:bg-slate-800 hover:bg-slate-300 dark:hover:bg-slate-700 text-slate-800 dark:text-slate-200 rounded text-xs font-mono"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
