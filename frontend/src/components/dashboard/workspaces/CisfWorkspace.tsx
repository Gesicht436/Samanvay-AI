import React from 'react';
import Link from 'next/link';
import { QrCode, Truck } from 'lucide-react';
import { Card } from '@/components/ui';

interface CisfWorkspaceProps {
  requests: any[];
  loading: boolean;
}

export function CisfWorkspace({ requests }: CisfWorkspaceProps) {
  return (
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
            <div key={req.requisition_id || req.id} className="py-2.5 flex items-center justify-between gap-4 text-xs">
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-mono font-semibold text-zinc-900 dark:text-zinc-100">
                    {req.requisition_id || req.req_number || `REQ-${req.id}`}
                  </span>
                  <span className="text-zinc-400">|</span>
                  <span className="font-mono text-zinc-600 dark:text-zinc-400">
                    {req.source_cpse || req.fulfilling_cpse} &rarr; {req.target_cpse || req.requesting_cpse}
                  </span>
                </div>
                <p className="text-zinc-500 dark:text-zinc-400 mt-0.5">
                  Material: <span className="font-mono">{req.sku_code}</span> · Status: <span className="font-medium text-zinc-800 dark:text-zinc-200">{req.status?.replace(/_/g, ' ')}</span>
                </p>
              </div>
              <Link
                href={`/requests/${req.requisition_id || req.id}`}
                className="px-2.5 py-1 bg-zinc-900 hover:bg-zinc-800 text-white dark:bg-zinc-100 dark:hover:bg-zinc-200 dark:text-zinc-900 rounded text-xs font-medium transition-colors"
              >
                Inspect Gate Pass
              </Link>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
