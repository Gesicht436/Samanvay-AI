import React from 'react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  className?: string;
}

export function Card({ children, className, ...props }: CardProps) {
  return (
    <div
      className={cn("bg-white dark:bg-slate-800 rounded-lg shadow-sm border border-slate-200 dark:border-slate-700 p-4", className)}
      {...props}
    >
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
  const map: Record<number, { bg: string; text: string; border: string; label: string; sub: string }> = {
    1: {
      bg: 'bg-emerald-50 dark:bg-emerald-950/60',
      text: 'text-emerald-700 dark:text-emerald-300',
      border: 'border-emerald-200 dark:border-emerald-800',
      label: 'Tier 1',
      sub: 'Direct Substitute',
    },
    2: {
      bg: 'bg-amber-50 dark:bg-amber-950/60',
      text: 'text-amber-700 dark:text-amber-300',
      border: 'border-amber-200 dark:border-amber-800',
      label: 'Tier 2',
      sub: 'Conditional Match',
    },
    3: {
      bg: 'bg-rose-50 dark:bg-rose-950/60',
      text: 'text-rose-700 dark:text-rose-300',
      border: 'border-rose-200 dark:border-rose-800',
      label: 'Tier 3',
      sub: 'Incompatible',
    },
  };
  const config = map[tier] || {
    bg: 'bg-slate-100 dark:bg-slate-800',
    text: 'text-slate-700 dark:text-slate-300',
    border: 'border-slate-200 dark:border-slate-700',
    label: 'Unknown',
    sub: 'Unrated',
  };

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 px-2.5 py-0.5 text-xs font-mono font-semibold rounded-full border shadow-xs transition-colors",
        config.bg,
        config.text,
        config.border
      )}
      title={`Compatibility Rating: ${config.label} (${config.sub})`}
    >
      <span className="w-1.5 h-1.5 rounded-full bg-current opacity-80" />
      <span>{config.label}</span>
      <span className="text-[10px] opacity-75 hidden sm:inline">· {config.sub}</span>
    </span>
  );
}

export interface KpiCardProps {
  title?: string;
  label?: string;
  value: string | number;
  unit?: string;
  subtext?: string;
  delta?: string;
  deltaType?: 'positive' | 'negative' | 'warning' | 'neutral';
  isPositive?: boolean;
  icon?: React.ComponentType<{ size?: number; className?: string }> | React.ReactNode;
}

export function KpiCard({
  title,
  label,
  value,
  unit,
  subtext,
  delta,
  deltaType,
  isPositive,
  icon,
}: KpiCardProps) {
  const displayTitle = label || title;
  const isGood = deltaType ? deltaType === 'positive' : isPositive;
  const isWarn = deltaType === 'warning';

  const renderIcon = () => {
    if (!icon) return null;
    if (React.isValidElement(icon)) {
      return <div className="text-slate-400 dark:text-slate-500">{icon}</div>;
    }
    const IconComponent = icon as React.ComponentType<{ size?: number; className?: string }>;
    return <IconComponent size={18} className="text-slate-400 dark:text-slate-500" />;
  };

  return (
    <Card className="flex flex-col justify-between hover:border-slate-300 dark:hover:border-slate-600 transition-all duration-150">
      <div className="flex items-center justify-between text-slate-500 dark:text-slate-400 mb-2">
        <span className="text-xs font-mono font-semibold uppercase tracking-wider">{displayTitle}</span>
        {renderIcon()}
      </div>
      <div className="flex items-baseline gap-1.5">
        <span className="text-2xl font-bold font-mono tracking-tight text-slate-900 dark:text-slate-50">{value}</span>
        {unit && <span className="text-xs font-mono text-slate-500 dark:text-slate-400">{unit}</span>}
      </div>
      {subtext && (
        <div className="text-[11px] text-slate-500 dark:text-slate-400 mt-1 font-mono truncate">
          {subtext}
        </div>
      )}
      {delta && (
        <div className="mt-2 flex items-center gap-1 text-xs font-mono">
          <span
            className={cn(
              isWarn
                ? "text-amber-600 dark:text-amber-400"
                : isGood
                ? "text-emerald-600 dark:text-emerald-400"
                : "text-rose-600 dark:text-rose-400"
            )}
          >
            {delta}
          </span>
          {!subtext && <span className="text-slate-400 dark:text-slate-500">vs last month</span>}
        </div>
      )}
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
