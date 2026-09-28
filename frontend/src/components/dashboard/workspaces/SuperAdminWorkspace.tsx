import React from 'react';
import Link from 'next/link';

export function SuperAdminWorkspace() {
  return (
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
            <span className="px-1.5 py-0.2 text-[9px] font-mono font-medium bg-zinc-900 text-white dark:bg-zinc-100 dark:text-zinc-900 rounded">
              ADMIN
            </span>
          </div>
          <p className="text-[11px] text-zinc-500 mt-1">Review pending registrations.</p>
        </Link>
      </div>
    </div>
  );
}
