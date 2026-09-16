import React from "react";
import { TimelineEvent } from "@/lib/types";
import { formatDateTime } from "@/lib/formatters";
import { CheckCircle2, Clock, Truck, Package, XCircle, AlertCircle } from "lucide-react";

interface TimelineProps {
  events: TimelineEvent[];
  className?: string;
}

export function Timeline({ events, className = "" }: TimelineProps) {
  if (!events || events.length === 0) {
    return (
      <div className="text-xs text-[var(--text-muted)] italic py-2">
        No timeline events recorded yet.
      </div>
    );
  }

  const getEventIcon = (event: string) => {
    switch (event) {
      case "CREATED":
        return <Package className="w-3.5 h-3.5 text-blue-500" />;
      case "CONFIRMED":
        return <CheckCircle2 className="w-3.5 h-3.5 text-cyan-500" />;
      case "APPROVED":
        return <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />;
      case "DISPATCHED":
      case "IN_TRANSIT":
        return <Truck className="w-3.5 h-3.5 text-indigo-500" />;
      case "DELIVERED":
        return <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />;
      case "REJECTED":
        return <XCircle className="w-3.5 h-3.5 text-rose-500" />;
      default:
        return <Clock className="w-3.5 h-3.5 text-slate-400" />;
    }
  };

  return (
    <div className={`relative pl-6 space-y-6 before:absolute before:left-2.5 before:top-2 before:bottom-2 before:w-0.5 before:bg-[var(--border-primary)] ${className}`}>
      {events.map((evt, idx) => (
        <div key={idx} className="relative group">
          <div className="absolute -left-6 top-0.5 w-5 h-5 rounded-full bg-[var(--bg-secondary)] border-2 border-[var(--border-primary)] flex items-center justify-center">
            {getEventIcon(evt.event)}
          </div>
          <div>
            <div className="flex flex-wrap items-baseline gap-2">
              <span className="text-xs font-bold text-[var(--text-primary)]">{evt.title}</span>
              <span className="text-[10px] text-[var(--text-muted)] font-mono">
                {formatDateTime(evt.timestamp)}
              </span>
            </div>
            <div className="text-[11px] text-[var(--text-secondary)] mt-0.5">
              <span className="font-semibold text-[var(--accent-primary)]">{evt.actor_cpse}</span>
              {" • "}
              <span>{evt.actor}</span>
            </div>
            {evt.notes && (
              <p className="text-xs text-[var(--text-secondary)] mt-1.5 p-2 rounded-md bg-[var(--bg-tertiary)] border border-[var(--border-subtle)] leading-relaxed">
                {evt.notes}
              </p>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
