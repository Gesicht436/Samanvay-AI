import React, { useEffect } from 'react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { X } from 'lucide-react';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  className?: string;
  title?: string;
  icon?: React.ComponentType<{ size?: number; className?: string }> | React.ReactNode;
  actions?: React.ReactNode;
}

export function Card({ children, className, title, icon, actions, ...props }: CardProps) {
  const renderIcon = () => {
    if (!icon) return null;
    if (React.isValidElement(icon)) {
      return icon;
    }
    const IconComponent = icon as React.ComponentType<{ size?: number; className?: string }>;
    return <IconComponent size={14} className="text-zinc-500 dark:text-zinc-400 shrink-0" />;
  };

  return (
    <div
      className={cn(
        "bg-white dark:bg-zinc-900/70 rounded-lg border border-zinc-200 dark:border-zinc-800 p-4 transition-colors",
        className
      )}
      {...props}
    >
      {(title || actions) && (
        <div className="flex items-center justify-between gap-2 pb-3 mb-3 border-b border-zinc-100 dark:border-zinc-800/80">
          <div className="flex items-center gap-2 min-w-0">
            {renderIcon()}
            {title && (
              <h3 className="text-xs font-mono font-semibold uppercase tracking-wider text-zinc-700 dark:text-zinc-300 truncate">
                {title}
              </h3>
            )}
          </div>
          {actions && <div className="shrink-0">{actions}</div>}
        </div>
      )}
      {children}
    </div>
  );
}

export function Modal({
  isOpen,
  onClose,
  title,
  children,
}: {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  children: React.ReactNode;
}) {
  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) onClose();
    };
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, [isOpen, onClose]);

  if (!isOpen) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4 animate-in fade-in duration-150">
      <div
        className="bg-white dark:bg-zinc-900 rounded-lg border border-zinc-200 dark:border-zinc-800 shadow-2xl w-full max-w-lg overflow-hidden flex flex-col max-h-[90vh]"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="p-4 border-b border-zinc-100 dark:border-zinc-800 flex items-center justify-between">
          <h3 className="text-sm font-semibold text-zinc-900 dark:text-zinc-100 font-sans">{title || 'Details'}</h3>
          <button
            onClick={onClose}
            className="p-1 rounded text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-200 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors"
          >
            <X size={15} />
          </button>
        </div>
        <div className="p-4 flex-1 overflow-y-auto">{children}</div>
      </div>
    </div>
  );
}

// Linear / Palantir style Sliding Side Inspector Drawer (480px)
export function SideDrawer({
  isOpen,
  onClose,
  title,
  subtitle,
  children,
  footer,
}: {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  subtitle?: string;
  children: React.ReactNode;
  footer?: React.ReactNode;
}) {
  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) onClose();
    };
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-hidden">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/40 backdrop-blur-[2px] transition-opacity duration-200"
        onClick={onClose}
      />

      <div className="fixed inset-y-0 right-0 max-w-full flex pl-10">
        <div className="w-screen max-w-lg bg-white dark:bg-zinc-900 border-l border-zinc-200 dark:border-zinc-800 shadow-2xl flex flex-col animate-in slide-in-from-right duration-200">
          {/* Header */}
          <div className="px-5 py-4 border-b border-zinc-100 dark:border-zinc-800/80 flex items-start justify-between bg-zinc-50/50 dark:bg-zinc-900/50">
            <div>
              <h2 className="text-sm font-semibold text-zinc-900 dark:text-zinc-100 font-sans tracking-tight">
                {title}
              </h2>
              {subtitle && (
                <p className="text-xs font-mono text-zinc-500 dark:text-zinc-400 mt-0.5">{subtitle}</p>
              )}
            </div>
            <button
              onClick={onClose}
              className="p-1.5 rounded-md text-zinc-400 hover:text-zinc-700 dark:hover:text-zinc-200 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors"
              title="Close (Esc)"
            >
              <X size={16} />
            </button>
          </div>

          {/* Scrollable Content */}
          <div className="flex-1 overflow-y-auto p-5 space-y-5 text-sm">{children}</div>

          {/* Optional Footer Actions */}
          {footer && (
            <div className="px-5 py-3.5 border-t border-zinc-100 dark:border-zinc-800/80 bg-zinc-50/50 dark:bg-zinc-900/50">
              {footer}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// Subtle Hairline Skeleton Loader
export function Skeleton({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("animate-pulse rounded bg-zinc-200/80 dark:bg-zinc-800/80", className)}
      {...props}
    />
  );
}

export function StatusBadge({
  tier,
  label,
  sub,
  className,
}: {
  tier?: number;
  label?: string;
  sub?: string;
  className?: string;
}) {
  const map: Record<number, { bg: string; text: string; border: string; dot: string; label: string; sub: string }> = {
    1: {
      bg: 'bg-emerald-500/10',
      text: 'text-emerald-700 dark:text-emerald-400',
      border: 'border-emerald-500/20',
      dot: 'bg-emerald-500',
      label: 'Tier 1',
      sub: 'Direct Substitute',
    },
    2: {
      bg: 'bg-amber-500/10',
      text: 'text-amber-700 dark:text-amber-400',
      border: 'border-amber-500/20',
      dot: 'bg-amber-500',
      label: 'Tier 2',
      sub: 'Conditional Match',
    },
    3: {
      bg: 'bg-rose-500/10',
      text: 'text-rose-700 dark:text-rose-400',
      border: 'border-rose-500/20',
      dot: 'bg-rose-500',
      label: 'Tier 3',
      sub: 'Incompatible',
    },
  };

  const config = (tier && map[tier]) || {
    bg: 'bg-zinc-500/10',
    text: 'text-zinc-700 dark:text-zinc-300',
    border: 'border-zinc-500/20',
    dot: 'bg-zinc-400',
    label: label || 'Unrated',
    sub: sub || '',
  };

  const displayLabel = label || config.label;
  const displaySub = sub !== undefined ? sub : config.sub;

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 px-2 py-0.5 text-xs font-mono font-medium rounded-full border transition-colors",
        config.bg,
        config.text,
        config.border,
        className
      )}
    >
      <span className={cn("w-1.5 h-1.5 rounded-full shrink-0", config.dot)} />
      <span>{displayLabel}</span>
      {displaySub && <span className="text-[10px] opacity-75 hidden sm:inline">· {displaySub}</span>}
    </span>
  );
}

export interface KpiCardProps {
  title?: string;
  label?: string;
  value: React.ReactNode;
  unit?: string;
  subtext?: string;
  delta?: string;
  deltaType?: 'positive' | 'negative' | 'warning' | 'neutral';
  isPositive?: boolean;
  icon?: React.ComponentType<{ size?: number; className?: string }> | React.ReactNode;
  variant?: 'emerald' | 'amber' | 'rose' | 'blue' | 'slate' | string;
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
      return <div className="text-zinc-400 dark:text-zinc-500">{icon}</div>;
    }
    const IconComponent = icon as React.ComponentType<{ size?: number; className?: string }>;
    return <IconComponent size={15} className="text-zinc-400 dark:text-zinc-500" />;
  };

  return (
    <Card className="flex flex-col justify-between hover:border-zinc-300 dark:hover:border-zinc-700 transition-colors">
      <div className="flex items-center justify-between text-zinc-500 dark:text-zinc-400 mb-2">
        <span className="text-[11px] font-mono font-medium uppercase tracking-wider text-zinc-500 dark:text-zinc-400 truncate">
          {displayTitle}
        </span>
        {renderIcon()}
      </div>
      <div className="flex items-baseline gap-1.5">
        <span className="text-2xl font-semibold font-mono tracking-tight tabular-nums text-zinc-900 dark:text-zinc-50">
          {value}
        </span>
        {unit && <span className="text-xs font-mono text-zinc-500 dark:text-zinc-400">{unit}</span>}
      </div>
      {subtext && (
        <div className="text-[11px] text-zinc-500 dark:text-zinc-400 mt-1 font-mono truncate">
          {subtext}
        </div>
      )}
      {delta && (
        <div className="mt-2 flex items-center gap-1.5 text-xs font-mono">
          <span
            className={cn(
              "font-medium",
              isWarn
                ? "text-amber-600 dark:text-amber-400"
                : isGood
                ? "text-emerald-600 dark:text-emerald-400"
                : "text-rose-600 dark:text-rose-400"
            )}
          >
            {delta}
          </span>
          {!subtext && <span className="text-zinc-400 dark:text-zinc-500">live</span>}
        </div>
      )}
    </Card>
  );
}

export function Timeline({ events }: { events: { date: string; title: string; desc: string }[] }) {
  return (
    <div className="space-y-4">
      {events.map((e, i) => (
        <div key={i} className="flex gap-3">
          <div className="flex flex-col items-center">
            <div className="w-2 h-2 rounded-full bg-emerald-500 mt-1.5 shrink-0" />
            {i !== events.length - 1 && <div className="w-px h-full bg-zinc-200 dark:bg-zinc-800 mt-1" />}
          </div>
          <div className="pb-3 text-xs">
            <p className="text-[11px] text-zinc-400 font-mono mb-0.5">{e.date}</p>
            <p className="font-medium text-zinc-900 dark:text-zinc-100">{e.title}</p>
            <p className="text-zinc-500 dark:text-zinc-400 mt-0.5">{e.desc}</p>
          </div>
        </div>
      ))}
    </div>
  );
}

export function EmptyState({
  title,
  message,
  action,
}: {
  title?: string;
  message: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="flex flex-col items-center justify-center p-10 text-center border border-dashed border-zinc-200 dark:border-zinc-800 rounded-lg bg-zinc-50/50 dark:bg-zinc-900/30">
      {title && <h4 className="text-xs font-mono font-semibold uppercase text-zinc-700 dark:text-zinc-300 mb-1">{title}</h4>}
      <p className="text-xs text-zinc-500 dark:text-zinc-400 max-w-sm">{message}</p>
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}
