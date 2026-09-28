import React from 'react';
import Link from 'next/link';
import { Truck, Package, ArrowRight } from 'lucide-react';
import { Card, Skeleton } from '@/components/ui';

interface MaterialsManagerWorkspaceProps {
  requests: any[];
  loading: boolean;
  cpse: string;
}

export function MaterialsManagerWorkspace({ requests, loading, cpse }: MaterialsManagerWorkspaceProps) {
  const pendingRequests = requests.filter(
    (r) => r.status === 'PENDING_APPROVAL' || r.status === 'REQUESTED'
  );

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card title="Pending Loan Approvals (Stores Action)" icon={Truck}>
          {loading ? (
            <div className="space-y-2 py-2">
              <Skeleton className="h-8 w-full" />
              <Skeleton className="h-8 w-full" />
            </div>
          ) : pendingRequests.length === 0 ? (
            <div className="py-8 text-center text-xs text-zinc-400 font-mono">
              All inter-CPSE loan requests cleared for {cpse}. Zero pending backlogs.
            </div>
          ) : (
            <div className="divide-y divide-zinc-100 dark:divide-zinc-800/80">
              {pendingRequests.slice(0, 4).map((req) => (
                <div key={req.requisition_id || req.id} className="py-2.5 flex items-center justify-between gap-4 text-xs">
                  <div>
                    <p className="font-mono font-semibold text-zinc-900 dark:text-zinc-100">
                      {req.requisition_id || req.req_number || `REQ-${req.id}`}
                    </p>
                    <p className="text-zinc-500 dark:text-zinc-400 mt-0.5">
                      {req.target_cpse || req.requesting_cpse || 'Sister CPSE'} requesting <span className="font-mono">{req.sku_code}</span> (Qty: {req.required_qty ?? req.quantity_requested ?? 1})
                    </p>
                  </div>
                  <Link
                    href={`/requests/${req.requisition_id || req.id}`}
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
  );
}
