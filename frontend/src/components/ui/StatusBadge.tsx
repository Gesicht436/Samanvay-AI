import React from "react";

export type StatusType =
  | "TO_BE_CONSUMED"
  | "IN_STORAGE"
  | "IDLE_SURPLUS"
  | "RESERVED_TRANSFER"
  | "CONSUMED"
  | "PENDING_APPROVAL"
  | "APPROVED_FOR_DISPATCH"
  | "IN_TRANSIT"
  | "DELIVERED"
  | "REJECTED"
  | "TIER_1_IDENTICAL"
  | "TIER_2_SUBSTITUTE"
  | "TIER_3_INCOMPATIBLE";

interface StatusBadgeProps {
  status: StatusType | string;
  label?: string;
  showDot?: boolean;
  className?: string;
}

export function StatusBadge({ status, label, showDot = true, className = "" }: StatusBadgeProps) {
  let text = label;
  let bgClass = "bg-slate-100 dark:bg-slate-800/80 text-slate-700 dark:text-slate-300 border-slate-200 dark:border-slate-700";
  let dotColor = "bg-slate-500";
  let pulse = false;

  switch (status) {
    case "TO_BE_CONSUMED":
      text = text || "To Be Consumed";
      bgClass = "bg-amber-50 dark:bg-amber-950/40 text-amber-800 dark:text-amber-300 border-amber-200 dark:border-amber-800/60";
      dotColor = "bg-amber-500";
      break;

    case "IN_STORAGE":
      text = text || "In Storage";
      bgClass = "bg-blue-50 dark:bg-blue-950/40 text-blue-800 dark:text-blue-300 border-blue-200 dark:border-blue-800/60";
      dotColor = "bg-blue-500";
      break;

    case "IDLE_SURPLUS":
      text = text || "Idle Surplus (Live)";
      bgClass = "bg-emerald-50 dark:bg-emerald-950/40 text-emerald-800 dark:text-emerald-300 border-emerald-200 dark:border-emerald-800/60";
      dotColor = "bg-emerald-500";
      pulse = true;
      break;

    case "CONSUMED":
      text = text || "Consumed";
      bgClass = "bg-slate-100 dark:bg-slate-800/60 text-slate-600 dark:text-slate-400 border-slate-200 dark:border-slate-700";
      dotColor = "bg-slate-400";
      break;

    case "RESERVED_TRANSFER":
      text = text || "Reserved Transfer";
      bgClass = "bg-purple-50 dark:bg-purple-950/40 text-purple-800 dark:text-purple-300 border-purple-200 dark:border-purple-800/60";
      dotColor = "bg-purple-500";
      break;

    case "PENDING_APPROVAL":
      text = text || "Pending Facility Action";
      bgClass = "bg-amber-50 dark:bg-amber-950/40 text-amber-800 dark:text-amber-300 border-amber-200 dark:border-amber-800/60";
      dotColor = "bg-amber-500";
      pulse = true;
      break;

    case "APPROVED_FOR_DISPATCH":
      text = text || "Supply Confirmed (Gate Pass)";
      bgClass = "bg-cyan-50 dark:bg-cyan-950/40 text-cyan-800 dark:text-cyan-300 border-cyan-200 dark:border-cyan-800/60";
      dotColor = "bg-cyan-500";
      break;

    case "IN_TRANSIT":
      text = text || "In Transit (Road/Rail)";
      bgClass = "bg-indigo-50 dark:bg-indigo-950/40 text-indigo-800 dark:text-indigo-300 border-indigo-200 dark:border-indigo-800/60";
      dotColor = "bg-indigo-500";
      pulse = true;
      break;

    case "DELIVERED":
      text = text || "Delivered at Depot";
      bgClass = "bg-emerald-50 dark:bg-emerald-950/40 text-emerald-800 dark:text-emerald-300 border-emerald-200 dark:border-emerald-800/60";
      dotColor = "bg-emerald-500";
      break;

    case "REJECTED":
      text = text || "Declined";
      bgClass = "bg-rose-50 dark:bg-rose-950/40 text-rose-800 dark:text-rose-300 border-rose-200 dark:border-rose-800/60";
      dotColor = "bg-rose-500";
      break;

    case "TIER_1_IDENTICAL":
      text = text || "Tier 1: Identical Spec";
      bgClass = "bg-emerald-50 dark:bg-emerald-950/40 text-emerald-800 dark:text-emerald-300 border-emerald-200 dark:border-emerald-800/60";
      dotColor = "bg-emerald-500";
      break;

    case "TIER_2_SUBSTITUTE":
      text = text || "Tier 2: Safe Substitute";
      bgClass = "bg-amber-50 dark:bg-amber-950/40 text-amber-800 dark:text-amber-300 border-amber-200 dark:border-amber-800/60";
      dotColor = "bg-amber-500";
      break;

    case "TIER_3_INCOMPATIBLE":
      text = text || "Tier 3: Incompatible";
      bgClass = "bg-rose-50 dark:bg-rose-950/40 text-rose-800 dark:text-rose-300 border-rose-200 dark:border-rose-800/60";
      dotColor = "bg-rose-500";
      break;

    default:
      text = text || status;
  }

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md text-[11px] font-semibold border ${bgClass} ${className}`}
    >
      {showDot && (
        <span
          className={`w-1.5 h-1.5 rounded-full shrink-0 ${dotColor} ${pulse ? "animate-pulse" : ""}`}
        />
      )}
      <span>{text}</span>
    </span>
  );
}
