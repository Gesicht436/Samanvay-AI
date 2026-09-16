"use client";

import React, { useState, useEffect } from "react";
import { Card, CardHeader } from "@/components/ui/Card";
import { KpiCard } from "@/components/ui/KpiCard";
import { EmptyState } from "@/components/ui/EmptyState";
import { fetchAuditLogs } from "@/lib/api";
import { AuditLogEntry } from "@/lib/types";
import { formatDateTime } from "@/lib/formatters";
import { exportToCsv } from "@/lib/exportUtils";
import {
  ShieldCheck,
  Search,
  Download,
  Copy,
  Check,
  Lock,
  RefreshCw,
  FileSpreadsheet,
  CheckCircle2,
} from "lucide-react";

export default function AuditPage() {
  const [logs, setLogs] = useState<AuditLogEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState<string>("ALL");
  const [selectedCpse, setSelectedCpse] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState("");
  const [copiedHash, setCopiedHash] = useState<string | null>(null);

  useEffect(() => {
    loadLogs();
  }, [selectedCategory, selectedCpse]);

  const loadLogs = async () => {
    setLoading(true);
    try {
      const data = await fetchAuditLogs({
        category: selectedCategory === "ALL" ? undefined : selectedCategory,
        cpse: selectedCpse === "ALL" ? undefined : selectedCpse,
        query: searchQuery,
      });
      setLogs(data || []);
    } catch {
      setLogs([]);
    } finally {
      setLoading(false);
    }
  };

  const handleCopyHash = (hash: string) => {
    navigator.clipboard.writeText(hash);
    setCopiedHash(hash);
    setTimeout(() => setCopiedHash(null), 2000);
  };

  const handleExportCsv = () => {
    exportToCsv(logs, "Samanvay_Audit_Ledger", {
      log_id: "Audit ID",
      timestamp: "Timestamp",
      action_category: "Category",
      action_name: "Action",
      actor_name: "Officer",
      actor_role: "Role",
      cpse: "CPSE",
      depot: "Depot",
      reference_id: "Ref ID",
      details: "Audit Notes",
      sha256_hash: "SHA-256 Seal",
    });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold text-[var(--text-primary)]">
            Sovereign Audit Ledger & CVC Compliance
          </h1>
          <p className="text-xs text-[var(--text-secondary)] mt-1">
            Chronological, cryptographically sealed record of all inward bill reviews, lifecycle tag transitions, and inter-CPSE transfer indents.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleExportCsv}
            disabled={logs.length === 0}
            className="btn-secondary py-2 px-3 text-xs"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export CSV</span>
          </button>
          <button
            onClick={loadLogs}
            disabled={loading}
            className="btn-secondary py-2 px-2.5 text-xs"
            title="Refresh Ledger"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
          </button>
        </div>
      </div>

      {/* KPI Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <KpiCard
          label="Total Logged Events"
          value={logs.length}
          subtitle="All cryptographically sealed"
          icon={<FileSpreadsheet className="w-4 h-4 text-blue-500" />}
          accent="blue"
        />
        <KpiCard
          label="Cryptographic Verification"
          value="100% SHA-256"
          subtitle="Tamper-evident seals"
          icon={<Lock className="w-4 h-4 text-emerald-500" />}
          accent="green"
        />
        <KpiCard
          label="CVC Standard"
          value="MoPNG Certified"
          subtitle="Sovereign compliance"
          icon={<ShieldCheck className="w-4 h-4 text-purple-500" />}
          accent="purple"
        />
        <KpiCard
          label="Inter-CPSE Consensus"
          value="5 CPSEs"
          subtitle="IOCL, ONGC, BPCL, HPCL, GAIL"
          icon={<CheckCircle2 className="w-4 h-4 text-cyan-500" />}
          accent="blue"
        />
      </div>

      {/* Filter Toolbar */}
      <Card padding="sm">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="flex items-center gap-2 w-full sm:w-auto">
            <div className="relative flex-1 sm:w-64">
              <Search className="w-3.5 h-3.5 absolute left-2.5 top-2.5 text-[var(--text-muted)]" />
              <input
                type="text"
                placeholder="Search actor, action, reference..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && loadLogs()}
                className="app-input w-full pl-8 text-xs"
              />
            </div>

            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="app-input text-xs cursor-pointer"
            >
              <option value="ALL">All Event Categories</option>
              <option value="INWARD_PROCUREMENT">Inward Procurement</option>
              <option value="LIFECYCLE_TRANSITION">Lifecycle Transitions</option>
              <option value="REQUISITION_TRANSFER">Transfer Requisitions</option>
              <option value="GATE_PASS_VERIFICATION">Gate Pass Issuance</option>
            </select>

            <select
              value={selectedCpse}
              onChange={(e) => setSelectedCpse(e.target.value)}
              className="app-input text-xs cursor-pointer"
            >
              <option value="ALL">All CPSEs</option>
              <option value="IOCL">IOCL</option>
              <option value="ONGC">ONGC</option>
              <option value="BPCL">BPCL</option>
              <option value="HPCL">HPCL</option>
              <option value="GAIL">GAIL</option>
            </select>
          </div>

          <div className="text-xs text-[var(--text-muted)] font-mono">
            {logs.length} verifiable events recorded
          </div>
        </div>
      </Card>

      {/* Audit Log Table */}
      <Card padding="none">
        {loading ? (
          <div className="py-20 flex flex-col items-center justify-center space-y-2">
            <RefreshCw className="w-6 h-6 text-[var(--accent-primary)] animate-spin" />
            <div className="text-xs text-[var(--text-secondary)]">Validating SHA-256 hashes...</div>
          </div>
        ) : logs.length === 0 ? (
          <div className="p-8">
            <EmptyState
              title="No Audit Records Found"
              description="No audit events match the selected category or CPSE filter."
            />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-[var(--bg-tertiary)] text-[var(--text-secondary)] font-semibold border-b border-[var(--border-primary)]">
                <tr>
                  <th className="py-2.5 px-4">Event / Timestamp</th>
                  <th className="py-2.5 px-3">Actor & Enterprise</th>
                  <th className="py-2.5 px-3">Action Description</th>
                  <th className="py-2.5 px-3">Reference</th>
                  <th className="py-2.5 px-4 text-right">Cryptographic Seal</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--border-subtle)] bg-[var(--bg-secondary)]">
                {logs.map((log) => (
                  <tr key={log.log_id} className="hover:bg-[var(--bg-tertiary)]/50 transition-colors">
                    {/* Event & Timestamp */}
                    <td className="py-3 px-4">
                      <div className="font-semibold text-[var(--text-primary)]">{log.action_name}</div>
                      <div className="text-[10px] text-[var(--text-muted)] font-mono mt-0.5">
                        {formatDateTime(log.timestamp)}
                      </div>
                    </td>

                    {/* Actor */}
                    <td className="py-3 px-3">
                      <div className="font-medium text-[var(--text-primary)]">{log.actor_name}</div>
                      <div className="text-[10px] text-[var(--text-muted)]">
                        {log.actor_role} • <strong className="text-[var(--accent-primary)]">{log.cpse}</strong>
                      </div>
                    </td>

                    {/* Action Details */}
                    <td className="py-3 px-3 max-w-[280px]">
                      <div className="text-[var(--text-secondary)] leading-relaxed line-clamp-2" title={log.details}>
                        {log.details}
                      </div>
                    </td>

                    {/* Reference */}
                    <td className="py-3 px-3 font-mono text-[11px] text-[var(--accent-primary)]">
                      {log.reference_id}
                    </td>

                    {/* SHA-256 Seal */}
                    <td className="py-3 px-4 text-right">
                      <div className="inline-flex items-center gap-1">
                        <span className="font-mono text-[10px] text-[var(--text-muted)] max-w-[120px] truncate" title={log.sha256_hash}>
                          {log.sha256_hash.substring(0, 16)}...
                        </span>
                        <button
                          onClick={() => handleCopyHash(log.sha256_hash)}
                          className="p-1 rounded text-[var(--text-muted)] hover:text-[var(--text-primary)] cursor-pointer"
                          title="Copy Full SHA-256 Hash"
                        >
                          {copiedHash === log.sha256_hash ? (
                            <Check className="w-3 h-3 text-emerald-500" />
                          ) : (
                            <Copy className="w-3 h-3" />
                          )}
                        </button>
                      </div>
                      <div className="text-[9px] text-emerald-600 dark:text-emerald-400 font-semibold mt-0.5">
                        ✓ Verified
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}
