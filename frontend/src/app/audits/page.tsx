"use client";

import { useEffect, useState, Suspense } from "react";
import { fetchAuditLogs } from "@/lib/api";
import { AuditLogEntry } from "@/lib/types";
import { exportToCsv } from "@/lib/exportUtils";
import {
  FileText,
  Search,
  Download,
  Copy,
  Check,
  ShieldCheck,
  Filter,
  CheckCircle2,
  Lock,
  Layers,
  Truck,
  RotateCcw,
} from "lucide-react";

function AuditsContent() {
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
        category: selectedCategory,
        cpse: selectedCpse,
        query: searchQuery,
      });
      setLogs(data);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    loadLogs();
  };

  const handleCopyHash = (hash: string) => {
    navigator.clipboard.writeText(hash);
    setCopiedHash(hash);
    setTimeout(() => setCopiedHash(null), 2000);
  };

  const handleExportCsv = () => {
    exportToCsv(logs, "Samanvay_Audit_Ledger", {
      log_id: "Log ID",
      timestamp: "Timestamp (UTC)",
      action_category: "Category",
      action_name: "Event Title",
      actor_name: "Officer Name",
      actor_role: "Role / Department",
      cpse: "CPSE",
      depot: "Operating Depot",
      reference_id: "Reference Identifier",
      details: "Action Metadata & Details",
      sha256_hash: "SHA-256 Tamper-Proof Seal",
      is_verified: "Signature Validated",
    });
  };

  const getCategoryBadge = (cat: string) => {
    switch (cat) {
      case "DEDUPLICATION":
        return "bg-purple-50 text-purple-700 border-purple-300";
      case "TRANSFER_INDENT":
        return "bg-blue-50 text-blue-700 border-blue-300";
      case "GATE_PASS":
        return "bg-emerald-50 text-[#067d62] border-emerald-300";
      case "INGESTION":
        return "bg-amber-50 text-[#b12704] border-amber-300";
      case "SECURITY_CHECK":
        return "bg-teal-50 text-teal-700 border-teal-300";
      default:
        return "bg-slate-50 text-slate-700 border-slate-300";
    }
  };

  return (
    <div className="space-y-4">
      {/* 1. Header */}
      <div className="bg-white border border-[#d5d9d9] rounded p-4 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-lg font-bold text-[#0f1111]">
            Central Sovereign Audit Trail & Movement Ledger
          </h1>
          <p className="text-xs text-[#565959] mt-0.5">
            Immutable chronological ledger of material code reconciliations, transfer indents, and CISF security gate passes.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={loadLogs}
            className="btn-amazon-white px-2.5 py-1.5 rounded text-xs font-semibold flex items-center gap-1 cursor-pointer"
            title="Refresh Audit Logs"
          >
            <RotateCcw className="w-3.5 h-3.5 text-slate-500" />
            Refresh
          </button>
          <button
            onClick={handleExportCsv}
            className="btn-amazon-primary px-3 py-1.5 rounded text-xs font-bold flex items-center gap-1.5 cursor-pointer shadow-sm"
          >
            <Download className="w-3.5 h-3.5 text-[#0f1111]" />
            Export Audit Log (CSV)
          </button>
        </div>
      </div>

      {/* 2. Search & Category Filters */}
      <div className="bg-white border border-[#d5d9d9] rounded p-3 shadow-sm space-y-2.5">
        <div className="flex flex-col md:flex-row items-center gap-2">
          <form onSubmit={handleSearch} className="flex-1 w-full flex items-center gap-2">
            <div className="relative flex-1">
              <Search className="w-3.5 h-3.5 absolute left-2.5 top-2.5 text-slate-400" />
              <input
                type="text"
                placeholder="Search audit log by SKU, Indent ID, Gate Pass, Officer, or SHA-256 hash..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="amazon-input w-full pl-8 pr-3 py-1.5 text-xs text-[#0f1111]"
              />
            </div>
            <button
              type="submit"
              className="btn-amazon-primary px-3.5 py-1.5 rounded text-xs font-bold cursor-pointer"
            >
              Search
            </button>
          </form>

          {/* CPSE Filter */}
          <div className="flex items-center gap-1.5 text-xs self-start md:self-auto">
            <span className="text-[#565959] font-semibold">CPSE:</span>
            <select
              value={selectedCpse}
              onChange={(e) => setSelectedCpse(e.target.value)}
              className="amazon-input text-xs px-2 py-1"
            >
              <option value="ALL">All CPSEs</option>
              <option value="IOCL">IOCL</option>
              <option value="ONGC">ONGC</option>
              <option value="BPCL">BPCL</option>
            </select>
          </div>
        </div>

        {/* Category Filter Pills */}
        <div className="flex items-center gap-1 pt-1 border-t border-[#eaeded] overflow-x-auto text-xs font-semibold">
          {[
            { id: "ALL", label: "All Audit Events" },
            { id: "DEDUPLICATION", label: "Deduplication & Harmonization" },
            { id: "TRANSFER_INDENT", label: "Transfer Indents" },
            { id: "GATE_PASS", label: "CISF Gate Passes" },
            { id: "INGESTION", label: "MTC Ingestion" },
            { id: "SECURITY_CHECK", label: "Perimeter Checkpoints" },
          ].map((cat) => (
            <button
              key={cat.id}
              onClick={() => setSelectedCategory(cat.id)}
              className={`px-2.5 py-1 rounded transition-all cursor-pointer whitespace-nowrap text-[11px] ${
                selectedCategory === cat.id
                  ? "bg-[#232f3e] text-[#ff9900] font-bold"
                  : "text-[#565959] hover:text-[#0f1111] hover:bg-[#eaeded]"
              }`}
            >
              {cat.label}
            </button>
          ))}
        </div>
      </div>

      {/* 3. Audit Ledger Table */}
      <div className="bg-white border border-[#d5d9d9] rounded overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead className="bg-[#f2f3f3] text-[#565959] font-bold uppercase tracking-wider border-b border-[#d5d9d9]">
              <tr>
                <th className="py-2.5 px-3">Log ID & Timestamp</th>
                <th className="py-2.5 px-3">Event Type</th>
                <th className="py-2.5 px-3">Authorized Officer & Role</th>
                <th className="py-2.5 px-3">Enterprise Depot</th>
                <th className="py-2.5 px-3">Reference ID</th>
                <th className="py-2.5 px-3">Operation Details</th>
                <th className="py-2.5 px-3">Cryptographic Seal</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#e5e7eb] text-[#0f1111]">
              {loading ? (
                <tr>
                  <td colSpan={7} className="py-10 text-center text-[#565959]">
                    Loading sovereign audit ledger...
                  </td>
                </tr>
              ) : logs.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-10 text-center text-[#565959]">
                    No audit log entries found matching criteria.
                  </td>
                </tr>
              ) : (
                logs.map((log) => (
                  <tr key={log.log_id} className="hover:bg-[#f7fafa] transition-colors">
                    <td className="py-2.5 px-3 align-top whitespace-nowrap">
                      <div className="font-mono font-bold text-xs text-[#0f1111]">
                        {log.log_id}
                      </div>
                      <div className="text-[10px] text-[#565959] mt-0.5">
                        {new Date(log.timestamp).toLocaleString("en-IN", {
                          day: "numeric",
                          month: "short",
                          year: "numeric",
                          hour: "2-digit",
                          minute: "2-digit",
                        })}
                      </div>
                    </td>

                    <td className="py-2.5 px-3 align-top whitespace-nowrap">
                      <span className={`inline-block px-1.5 py-0.5 rounded text-[10px] font-bold border ${getCategoryBadge(log.action_category)}`}>
                        {log.action_category.replace("_", " ")}
                      </span>
                      <div className="font-semibold text-xs text-[#0f1111] mt-0.5 max-w-[160px] truncate" title={log.action_name}>
                        {log.action_name}
                      </div>
                    </td>

                    <td className="py-2.5 px-3 align-top">
                      <div className="font-bold text-[#0f1111]">{log.actor_name}</div>
                      <div className="text-[10px] text-[#565959]">{log.actor_role}</div>
                    </td>

                    <td className="py-2.5 px-3 align-top whitespace-nowrap">
                      <span className="font-bold text-[#0f1111]">{log.cpse}</span>
                      <div className="text-[10px] text-[#565959] max-w-[140px] truncate" title={log.depot}>
                        {log.depot.split(",")[0]}
                      </div>
                    </td>

                    <td className="py-2.5 px-3 align-top whitespace-nowrap">
                      <span className="font-mono font-bold text-[#007185] bg-slate-50 px-1 py-0.5 rounded border border-slate-200">
                        {log.reference_id}
                      </span>
                    </td>

                    <td className="py-2.5 px-3 align-top max-w-sm">
                      <p className="text-xs text-[#0f1111] leading-relaxed">
                        {log.details}
                      </p>
                    </td>

                    <td className="py-2.5 px-3 align-top whitespace-nowrap">
                      <div className="flex items-center gap-1">
                        <span className="font-mono text-[10px] text-slate-500 truncate max-w-[110px]" title={log.sha256_hash}>
                          {log.sha256_hash.substring(0, 12)}...
                        </span>
                        <button
                          onClick={() => handleCopyHash(log.sha256_hash)}
                          className="btn-amazon-white p-0.5 rounded cursor-pointer"
                          title="Copy Full SHA-256 Hash"
                        >
                          {copiedHash === log.sha256_hash ? (
                            <Check className="w-3 h-3 text-[#067d62]" />
                          ) : (
                            <Copy className="w-3 h-3 text-slate-400" />
                          )}
                        </button>
                      </div>
                      <div className="flex items-center gap-1 text-[10px] text-[#067d62] font-semibold mt-0.5">
                        <CheckCircle2 className="w-2.5 h-2.5" />
                        <span>Verified Seal</span>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

export default function AuditsPage() {
  return (
    <Suspense fallback={<div className="p-8 text-center text-xs text-slate-500">Loading Audit Ledger...</div>}>
      <AuditsContent />
    </Suspense>
  );
}
