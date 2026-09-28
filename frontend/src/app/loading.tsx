import React from 'react';

export default function Loading() {
  return (
    <div className="max-w-7xl mx-auto p-6 space-y-6 animate-pulse">
      {/* Top Banner Skeleton */}
      <div className="h-16 bg-zinc-200 dark:bg-zinc-800 rounded-lg w-full" />

      {/* Metric Cards Skeleton Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="h-28 bg-zinc-200 dark:bg-zinc-800 rounded-xl p-4 space-y-3">
            <div className="h-4 bg-zinc-300 dark:bg-zinc-700 rounded w-1/2" />
            <div className="h-8 bg-zinc-300 dark:bg-zinc-700 rounded w-3/4" />
          </div>
        ))}
      </div>

      {/* Main Content Area Skeleton */}
      <div className="h-96 bg-zinc-200 dark:bg-zinc-800 rounded-xl" />
    </div>
  );
}
