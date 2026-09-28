import React from 'react';
import Link from 'next/link';
import { FileCheck2, Layers, ShieldAlert, AlertTriangle } from 'lucide-react';
import { Card } from '@/components/ui';

interface TechnicalAuthorityWorkspaceProps {
  hitlQueue: any[];
  loading: boolean;
}

export function TechnicalAuthorityWorkspace({ hitlQueue }: TechnicalAuthorityWorkspaceProps) {
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        <div className="p-4 bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-lg">
          <FileCheck2 size={18} className="text-zinc-700 dark:text-zinc-300 mb-2" />
          <h3 className="font-semibold text-xs text-zinc-900 dark:text-zinc-100">
            HITL Triage Queue
          </h3>
          <p className="text-[11px] text-zinc-500 dark:text-zinc-400 mt-1">
            {hitlQueue.length} items flagged with 80%–94% compatibility requiring QA-QC metallurgical sign-off.
          </p>
          <Link
            href="/inventory"
            className="mt-2.5 inline-flex items-center gap-1 text-xs font-medium text-zinc-900 dark:text-zinc-100 hover:underline"
          >
            Open Triage Desk &rarr;
          </Link>
        </div>

        <div className="p-4 bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-lg">
          <Layers size={18} className="text-zinc-700 dark:text-zinc-300 mb-2" />
          <h3 className="font-semibold text-xs text-zinc-900 dark:text-zinc-100">
            21 Safety Gates
          </h3>
          <p className="text-[11px] text-zinc-500 dark:text-zinc-400 mt-1">
            ASME B16.5, ASTM A105 vs IS 2062 metallurgy DAG, and API 6D dimensional zero-tolerance.
          </p>
          <Link
            href="/discover"
            className="mt-2.5 inline-flex items-center gap-1 text-xs font-medium text-zinc-900 dark:text-zinc-100 hover:underline"
          >
            Evaluate Pairwise Rules &rarr;
          </Link>
        </div>

        <div className="p-4 bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-lg">
          <ShieldAlert size={18} className="text-zinc-700 dark:text-zinc-300 mb-2" />
          <h3 className="font-semibold text-xs text-zinc-900 dark:text-zinc-100">
            MTC Ladle Chemistry
          </h3>
          <p className="text-[11px] text-zinc-500 dark:text-zinc-400 mt-1">
            IIW carbon equivalent weldability (&le;0.43%) and PREN pitting resistance (&ge;32) compliance.
          </p>
          <Link
            href="/upload"
            className="mt-2.5 inline-flex items-center gap-1 text-xs font-medium text-zinc-900 dark:text-zinc-100 hover:underline"
          >
            MTC Document Review &rarr;
          </Link>
        </div>
      </div>

      <Card title="Pending HITL Tolerance Discrepancies" icon={AlertTriangle}>
        {hitlQueue.length === 0 ? (
          <div className="py-8 text-center text-xs text-zinc-400 font-mono">
            Zero pending triage disputes. All mechanical tolerances evaluated deterministic.
          </div>
        ) : (
          <div className="divide-y divide-zinc-100 dark:divide-zinc-800/80">
            {hitlQueue.slice(0, 5).map((item: any) => (
              <div key={item.id} className="py-2.5 flex items-center justify-between gap-4 text-xs">
                <div>
                  <span className="font-mono font-semibold text-zinc-900 dark:text-zinc-100">
                    {item.sku_code}
                  </span>
                  <p className="text-zinc-500 dark:text-zinc-400 mt-0.5">
                    {item.raw_description || item.description}
                  </p>
                </div>
                <Link
                  href="/inventory"
                  className="px-2.5 py-1 bg-zinc-100 dark:bg-zinc-800 hover:bg-zinc-200 dark:hover:bg-zinc-700 text-zinc-800 dark:text-zinc-200 rounded text-xs font-medium"
                >
                  Arbitrate &rarr;
                </Link>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}
