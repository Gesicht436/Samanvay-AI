import React from "react";

interface KpiCardProps {
  label: string;
  value: string | number;
  subtitle?: string;
  icon?: React.ReactNode;
  accent?: "default" | "blue" | "amber" | "green" | "purple";
  className?: string;
}

export function KpiCard({
  label,
  value,
  subtitle,
  icon,
  accent = "default",
  className = "",
}: KpiCardProps) {
  const accentBorder = {
    default: "hover:border-[var(--border-primary)]",
    blue: "hover:border-blue-300 dark:hover:border-blue-700",
    amber: "hover:border-amber-300 dark:hover:border-amber-700",
    green: "hover:border-emerald-300 dark:hover:border-emerald-700",
    purple: "hover:border-purple-300 dark:hover:border-purple-700",
  }[accent];

  return (
    <div
      className={`bg-[var(--bg-secondary)] border border-[var(--border-primary)] rounded-lg p-4 shadow-xs transition-all ${accentBorder} ${className}`}
    >
      <div className="flex items-center justify-between gap-2">
        <span className="text-xs font-medium text-[var(--text-secondary)]">{label}</span>
        {icon && <div className="text-[var(--text-muted)] shrink-0">{icon}</div>}
      </div>
      <div className="text-xl font-bold text-[var(--text-primary)] mt-1.5 font-mono">{value}</div>
      {subtitle && <div className="text-[11px] text-[var(--text-muted)] mt-0.5">{subtitle}</div>}
    </div>
  );
}
