import React from 'react';

export default function DashboardLoading() {
  return (
    <div className="space-y-5 max-w-7xl mx-auto pb-10 animate-pulse">
      {/* Officer Persona Context Bar Skeleton */}
      <div className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-lg p-4 h-20" />

      {/* KPI Cards Strip Skeleton */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        {[...Array(4)].map((_, i) => (
          <div
            key={i}
            className="p-4 bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-xl space-y-2 h-28"
          >
            <div className="h-3 bg-zinc-200 dark:bg-zinc-800 rounded w-1/2" />
            <div className="h-6 bg-zinc-300 dark:bg-zinc-700 rounded w-2/3" />
            <div className="h-2.5 bg-zinc-200 dark:bg-zinc-800 rounded w-1/3" />
          </div>
        ))}
      </div>

      {/* Workspaces / Table Skeleton */}
      <div className="p-6 bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-xl h-96" />
    </div>
  );
}
