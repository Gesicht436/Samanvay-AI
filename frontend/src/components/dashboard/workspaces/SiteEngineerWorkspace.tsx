import React from 'react';
import Link from 'next/link';
import { Search, Upload, Truck } from 'lucide-react';
import { Card, Skeleton } from '@/components/ui';

interface SiteEngineerWorkspaceProps {
  requests: any[];
  loading: boolean;
  cpse: string;
}

export function SiteEngineerWorkspace({ requests, loading, cpse }: SiteEngineerWorkspaceProps) {
  return (
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
  );
}
