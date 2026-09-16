import React from "react";
import { Search } from "lucide-react";

interface EmptyStateProps {
  title: string;
  description?: string;
  icon?: React.ReactNode;
  action?: React.ReactNode;
  className?: string;
}

export function EmptyState({
  title,
  description,
  icon,
  action,
  className = "",
}: EmptyStateProps) {
  return (
    <div
      className={`flex flex-col items-center justify-center p-8 text-center bg-[var(--bg-secondary)] border border-[var(--border-primary)] rounded-lg ${className}`}
    >
      <div className="w-10 h-10 rounded-full bg-[var(--bg-tertiary)] flex items-center justify-center text-[var(--text-muted)] mb-3">
        {icon || <Search className="w-5 h-5" />}
      </div>
      <h4 className="text-sm font-semibold text-[var(--text-primary)]">{title}</h4>
      {description && (
        <p className="text-xs text-[var(--text-secondary)] mt-1 max-w-md">{description}</p>
      )}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}
