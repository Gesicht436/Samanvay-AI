'use client';

import React, { useEffect } from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

export default function ErrorBoundary({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error('Next.js route error captured:', error);
  }, [error]);

  return (
    <div className="max-w-xl mx-auto my-16 p-6 bg-white dark:bg-zinc-900 border border-rose-300 dark:border-rose-900/50 rounded-2xl shadow-sm text-center space-y-4">
      <div className="w-12 h-12 bg-rose-100 dark:bg-rose-950/60 text-rose-600 dark:text-rose-400 rounded-full flex items-center justify-center mx-auto">
        <AlertTriangle size={24} />
      </div>
      <h2 className="text-base font-bold text-zinc-900 dark:text-zinc-100">
        Telemetry Node Connection Issue
      </h2>
      <p className="text-xs text-zinc-600 dark:text-zinc-400 max-w-md mx-auto leading-relaxed">
        {error?.message || 'Failed to communicate with the sovereign backend mesh.'}
      </p>
      <div className="pt-2">
        <button
          type="button"
          onClick={() => reset()}
          className="inline-flex items-center gap-2 px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold rounded-lg transition-colors shadow-xs"
        >
          <RefreshCw size={14} />
          <span>Retry Connection</span>
        </button>
      </div>
    </div>
  );
}
