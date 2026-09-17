import React from 'react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function Card({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={cn("bg-white dark:bg-slate-800 rounded-lg shadow border border-slate-200 dark:border-slate-700 p-4", className)}>
      {children}
    </div>
  );
}

export function Modal({ isOpen, onClose, children }: { isOpen: boolean; onClose: () => void; children: React.ReactNode }) {
  if (!isOpen) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
      <div className="bg-white dark:bg-slate-900 rounded-lg shadow-xl w-full max-w-lg overflow-hidden flex flex-col max-h-[90vh]">
        <div className="p-4 flex-1 overflow-y-auto">
          {children}
        </div>
        <div className="p-4 border-t border-slate-200 dark:border-slate-800 flex justify-end">
          <button onClick={onClose} className="px-4 py-2 bg-slate-200 dark:bg-slate-800 rounded hover:bg-slate-300 dark:hover:bg-slate-700">Close</button>
        </div>
      </div>
    </div>
  );
}

export function StatusBadge({ tier }: { tier: number }) {
  const map: Record<number, { color: string; label: string }> = {
    1: { color: 'bg-emerald-100 text-emerald-800 border-emerald-200', label: 'Tier 1' },
    2: { color: 'bg-amber-100 text-amber-800 border-amber-200', label: 'Tier 2' },
    3: { color: 'bg-rose-100 text-rose-800 border-rose-200', label: 'Tier 3' },
  };
  const config = map[tier] || { color: 'bg-slate-100 text-slate-800', label: 'Unknown' };
  
  return (
    <span className={cn("px-2 py-0.5 text-xs font-semibold rounded border", config.color)}>
      {config.label}
    </span>
  );
}

export function KpiCard({ title, value, unit }: { title: string; value: string | number; unit?: string }) {
  return (
    <Card className="flex flex-col">
      <span className="text-sm text-slate-500 uppercase font-semibold">{title}</span>
      <div className="mt-2 flex items-baseline gap-1">
        <span className="text-2xl font-bold font-mono">{value}</span>
        {unit && <span className="text-sm text-slate-400 font-mono">{unit}</span>}
      </div>
    </Card>
  );
}

export function Timeline({ events }: { events: { date: string; title: string; desc: string }[] }) {
  return (
    <div className="space-y-4">
      {events.map((e, i) => (
        <div key={i} className="flex gap-4">
          <div className="flex flex-col items-center">
            <div className="w-2.5 h-2.5 rounded-full bg-emerald-500 mt-1.5" />
            {i !== events.length - 1 && <div className="w-0.5 h-full bg-slate-200 dark:bg-slate-700 mt-2" />}
          </div>
          <div className="pb-4">
            <p className="text-xs text-slate-500 font-mono mb-1">{e.date}</p>
            <p className="font-semibold text-sm">{e.title}</p>
            <p className="text-sm text-slate-600 dark:text-slate-400">{e.desc}</p>
          </div>
        </div>
      ))}
    </div>
  );
}

export function EmptyState({ message }: { message: string }) {
  return (
    <div className="flex flex-col items-center justify-center p-12 text-slate-400 border-2 border-dashed border-slate-200 dark:border-slate-800 rounded-lg">
      <p className="text-sm font-medium">{message}</p>
    </div>
  );
}
