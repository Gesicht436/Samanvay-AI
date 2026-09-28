import React from 'react';
import Link from 'next/link';
import { ShieldCheck, FileSpreadsheet, Building2 } from 'lucide-react';
import { Card } from '@/components/ui';

interface VigilanceAuditorWorkspaceProps {
  auditLogs: any[];
  auditVerified: boolean | null;
  loading: boolean;
}

export function VigilanceAuditorWorkspace({
  auditLogs,
  auditVerified,
}: VigilanceAuditorWorkspaceProps) {
  return (
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
  );
}
