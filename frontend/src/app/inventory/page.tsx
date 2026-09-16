"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { Card, CardHeader } from "@/components/ui/Card";
import { KpiCard } from "@/components/ui/KpiCard";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { Modal } from "@/components/ui/Modal";
import { EmptyState } from "@/components/ui/EmptyState";
import { useTheme } from "@/components/ThemeProvider";
import { fetchInventoryItems, updateInventoryItemStatus } from "@/lib/api";
import { formatInr, formatDateTime } from "@/lib/formatters";
import { InventoryItemRecord, InventoryItemStatus } from "@/lib/types";
import {
  Package,
  Search,
  Filter,
  RefreshCw,
  Clock,
  ArrowRight,
  ShieldCheck,
  Check,
  Radio,
  PlusCircle,
  Tag,
  CheckCircle2,
} from "lucide-react";

export default function InventoryPage() {
  const { activeCpse } = useTheme();

  const [items, setItems] = useState<InventoryItemRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successToast, setSuccessToast] = useState<string | null>(null);

  // Filters
  const [cpseFilter, setCpseFilter] = useState<string>("ALL");
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState<string>("");

  // Transition Action State
  const [activeItem, setActiveItem] = useState<InventoryItemRecord | null>(null);
  const [actionTargetStatus, setActionTargetStatus] = useState<InventoryItemStatus | null>(null);
  const [actionNote, setActionNote] = useState<string>("");
  const [isUpdating, setIsUpdating] = useState(false);

  useEffect(() => {
    loadItems();
  }, [cpseFilter, statusFilter]);

  const loadItems = async () => {
    setLoading(true);
    setErrorMsg(null);
    try {
      const data = await fetchInventoryItems({
        cpse: cpseFilter === "ALL" ? undefined : cpseFilter,
        status: statusFilter === "ALL" ? undefined : statusFilter,
      });
      setItems(data || []);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to load inventory assets.");
    } finally {
      setLoading(false);
    }
  };

  const handleOpenStatusModal = (item: InventoryItemRecord, newStatus: InventoryItemStatus) => {
    setActiveItem(item);
    setActionTargetStatus(newStatus);
    if (newStatus === "IDLE_SURPLUS") {
      setActionNote("Material not utilized during planned turnaround window; broadcasting to all CPSEs as active surplus.");
    } else if (newStatus === "CONSUMED") {
      setActionNote("Material installed in processing unit CDU-2 during maintenance shutdown.");
    } else {
      setActionNote("Standard lifecycle status transition update.");
    }
  };

  const handleConfirmStatusUpdate = async () => {
    if (!activeItem || !actionTargetStatus) return;
    setIsUpdating(true);
    try {
      await updateInventoryItemStatus(
        activeItem.id,
        actionTargetStatus,
        actionNote,
        "SITE_ENGINEER"
      );
      setSuccessToast(`Item ${activeItem.sku_code} transitioned to ${actionTargetStatus}!`);
      setTimeout(() => setSuccessToast(null), 4000);
      setActiveItem(null);
      setActionTargetStatus(null);
      loadItems();
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to update item status.");
    } finally {
      setIsUpdating(false);
    }
  };

  // Filtered in-memory search
  const filteredItems = items.filter((it) => {
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const matchSku = it.sku_code.toLowerCase().includes(q);
      const matchDesc = it.description.toLowerCase().includes(q);
      const matchDepot = it.depot_location.toLowerCase().includes(q);
      const matchPo = it.po_no?.toLowerCase().includes(q) || false;
      if (!matchSku && !matchDesc && !matchDepot && !matchPo) return false;
    }
    return true;
  });

  // KPI Counters
  const countToBeConsumed = items.filter((i) => i.status === "TO_BE_CONSUMED").length;
  const countInStorage = items.filter((i) => i.status === "IN_STORAGE").length;
  const countIdleSurplus = items.filter((i) => i.status === "IDLE_SURPLUS").length;
  const countConsumed = items.filter((i) => i.status === "CONSUMED").length;

  return (
    <div className="space-y-6">
      {/* Toast Notification */}
      {successToast && (
        <div className="fixed top-4 right-4 z-50 p-3 rounded-lg bg-emerald-600 text-white shadow-lg text-xs font-medium flex items-center gap-2 animate-in slide-in-from-top-2">
          <CheckCircle2 className="w-4 h-4" />
          <span>{successToast}</span>
        </div>
      )}

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold text-[var(--text-primary)]">
            Plant Inventory & Surplus Radar
          </h1>
          <p className="text-xs text-[var(--text-secondary)] mt-1">
            Track inward assets, manage turnaround consumption vs idle surplus transitions, and broadcast dormant materials across the sovereign CPSE network.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Link href="/upload" className="btn-primary py-2 px-3 text-xs">
            <PlusCircle className="w-3.5 h-3.5" />
            <span>Inward New Bill</span>
          </Link>
          <button
            onClick={loadItems}
            disabled={loading}
            className="btn-secondary py-2 px-2.5 text-xs"
            title="Refresh Inventory"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
          </button>
        </div>
      </div>

      {/* Lifecycle Flow Explanation Banner */}
      <div className="p-3.5 rounded-lg border border-[var(--border-subtle)] bg-[var(--bg-tertiary)]/40 text-xs text-[var(--text-secondary)] flex flex-col md:flex-row md:items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <Radio className="w-4 h-4 text-[var(--accent-primary)] shrink-0 animate-pulse" />
          <span>
            <strong>Sovereign Lifecycle Rule:</strong> Materials inwarded as <span className="font-semibold text-amber-700 dark:text-amber-300">To Be Consumed</span> are private to your facility. If unconsumed after 90 days, mark them as <span className="font-semibold text-emerald-700 dark:text-emerald-300">Idle Surplus</span> to broadcast them to ONGC, IOCL, BPCL, HPCL, and GAIL.
          </span>
        </div>
        <Link href="/discover" className="inline-flex items-center gap-1 text-[var(--accent-primary)] font-semibold hover:underline shrink-0">
          <span>Search sister surplus</span>
          <ArrowRight className="w-3 h-3" />
        </Link>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
        <KpiCard
          label="Total Tracked Assets"
          value={items.length}
          subtitle="All plant records"
          icon={<Package className="w-4 h-4 text-blue-500" />}
          accent="blue"
        />
        <KpiCard
          label="To Be Consumed"
          value={countToBeConsumed}
          subtitle="Private turnaround stock"
          icon={<Clock className="w-4 h-4 text-amber-500" />}
          accent="amber"
        />
        <KpiCard
          label="In Storage"
          value={countInStorage}
          subtitle="Warehouse buffer reserve"
          icon={<ShieldCheck className="w-4 h-4 text-blue-500" />}
          accent="blue"
        />
        <KpiCard
          label="Idle Surplus"
          value={countIdleSurplus}
          subtitle="Broadcasted on Radar"
          icon={<Radio className="w-4 h-4 text-emerald-500" />}
          accent="green"
        />
        <KpiCard
          label="Consumed"
          value={countConsumed}
          subtitle="Archived in plant units"
          icon={<Check className="w-4 h-4 text-slate-400" />}
          accent="default"
        />
      </div>

      {/* Filter & Search Toolbar */}
      <Card padding="sm">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="flex items-center gap-2 w-full sm:w-auto">
            {/* Search */}
            <div className="relative flex-1 sm:w-64">
              <Search className="w-3.5 h-3.5 absolute left-2.5 top-2.5 text-[var(--text-muted)]" />
              <input
                type="text"
                placeholder="Search SKU, desc, depot, PO#..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="app-input w-full pl-8 text-xs"
              />
            </div>

            {/* CPSE Filter */}
            <select
              value={cpseFilter}
              onChange={(e) => setCpseFilter(e.target.value)}
              className="app-input text-xs cursor-pointer"
            >
              <option value="ALL">All CPSEs</option>
              <option value="IOCL">IOCL Only</option>
              <option value="ONGC">ONGC Only</option>
              <option value="BPCL">BPCL Only</option>
              <option value="HPCL">HPCL Only</option>
              <option value="GAIL">GAIL Only</option>
            </select>

            {/* Status Filter */}
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="app-input text-xs cursor-pointer"
            >
              <option value="ALL">All Lifecycle Statuses</option>
              <option value="TO_BE_CONSUMED">To Be Consumed</option>
              <option value="IN_STORAGE">In Storage</option>
              <option value="IDLE_SURPLUS">Idle Surplus (Live)</option>
              <option value="RESERVED_TRANSFER">Reserved Transfer</option>
              <option value="CONSUMED">Consumed</option>
            </select>
          </div>

          <div className="text-xs text-[var(--text-muted)] font-mono">
            Showing {filteredItems.length} of {items.length} records
          </div>
        </div>
      </Card>

      {/* Inventory Table Card */}
      <Card padding="none">
        {loading ? (
          <div className="py-20 flex flex-col items-center justify-center space-y-2">
            <RefreshCw className="w-6 h-6 text-[var(--accent-primary)] animate-spin" />
            <div className="text-xs text-[var(--text-secondary)]">Loading sovereign inventory items...</div>
          </div>
        ) : filteredItems.length === 0 ? (
          <div className="p-8">
            <EmptyState
              title="No Inventory Records Found"
              description="No inventory items match the current search or filter criteria. Inward new procurement bills to populate."
              action={
                <Link href="/upload" className="btn-primary text-xs py-1.5 px-3">
                  Upload Procurement Bill
                </Link>
              }
            />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-[var(--bg-tertiary)] text-[var(--text-secondary)] font-semibold border-b border-[var(--border-primary)]">
                <tr>
                  <th className="py-2.5 px-4">SKU / Description</th>
                  <th className="py-2.5 px-3">Depot Location</th>
                  <th className="py-2.5 px-3">Traceability</th>
                  <th className="py-2.5 px-3 text-right">Available Qty</th>
                  <th className="py-2.5 px-3 text-right">Valuation</th>
                  <th className="py-2.5 px-3 text-center">Lifecycle Status</th>
                  <th className="py-2.5 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--border-subtle)] bg-[var(--bg-secondary)]">
                {filteredItems.map((item) => (
                  <tr key={item.id} className="hover:bg-[var(--bg-tertiary)]/50 transition-colors">
                    {/* SKU & Description */}
                    <td className="py-3 px-4 max-w-[280px]">
                      <div className="font-mono font-bold text-[var(--accent-primary)]">{item.sku_code}</div>
                      <div className="font-medium text-[var(--text-primary)] truncate mt-0.5" title={item.description}>
                        {item.description}
                      </div>
                      <div className="text-[10px] text-[var(--text-muted)] mt-0.5 space-x-2">
                        <span>{item.metallurgy || "ASTM A105"}</span>
                        <span>•</span>
                        <span>{item.size_nb_mm ? `${item.size_nb_mm}mm` : "DN100"}</span>
                        <span>•</span>
                        <span>{item.pressure_class ? `${item.pressure_class}#` : "300#"}</span>
                      </div>
                    </td>

                    {/* Depot Location */}
                    <td className="py-3 px-3">
                      <div className="font-semibold text-[var(--text-primary)]">{item.cpse}</div>
                      <div className="text-[11px] text-[var(--text-secondary)] truncate max-w-[180px]">
                        {item.depot_location}
                      </div>
                    </td>

                    {/* Traceability */}
                    <td className="py-3 px-3 font-mono text-[11px] text-[var(--text-secondary)]">
                      <div>PO: {item.po_no || "—"}</div>
                      <div className="text-emerald-600 dark:text-emerald-400">Heat: {item.heat_no || "—"}</div>
                    </td>

                    {/* Quantity */}
                    <td className="py-3 px-3 text-right font-mono font-bold text-sm text-[var(--text-primary)]">
                      {item.quantity}
                    </td>

                    {/* Valuation */}
                    <td className="py-3 px-3 text-right font-mono text-xs">
                      <div className="font-semibold text-[var(--text-primary)]">
                        {formatInr(item.total_value_inr || item.quantity * item.unit_cost_inr)}
                      </div>
                      <div className="text-[10px] text-[var(--text-muted)]">
                        @{formatInr(item.unit_cost_inr)}/ea
                      </div>
                    </td>

                    {/* Status Badge */}
                    <td className="py-3 px-3 text-center">
                      <StatusBadge status={item.status} />
                      {item.days_idle > 0 && item.status !== "CONSUMED" && (
                        <div className="text-[10px] text-amber-600 dark:text-amber-400 font-mono mt-1">
                          {item.days_idle}d idle
                        </div>
                      )}
                    </td>

                    {/* Actions */}
                    <td className="py-3 px-4 text-right">
                      <div className="flex items-center justify-end gap-1.5">
                        {item.status === "TO_BE_CONSUMED" || item.status === "IN_STORAGE" ? (
                          <button
                            onClick={() => handleOpenStatusModal(item, "IDLE_SURPLUS")}
                            className="btn-subtle text-[11px] py-1 px-2 text-emerald-700 dark:text-emerald-300 border-emerald-300 dark:border-emerald-800 bg-emerald-50 dark:bg-emerald-950/40"
                            title="Broadcast as Idle Surplus to all CPSEs"
                          >
                            <Radio className="w-3 h-3" />
                            <span>Mark Idle Surplus</span>
                          </button>
                        ) : null}

                        {item.status !== "CONSUMED" ? (
                          <button
                            onClick={() => handleOpenStatusModal(item, "CONSUMED")}
                            className="btn-secondary text-[11px] py-1 px-2"
                            title="Mark as Consumed in Refinery"
                          >
                            <Check className="w-3 h-3" />
                            <span>Mark Consumed</span>
                          </button>
                        ) : (
                          <span className="text-[11px] text-[var(--text-muted)] italic">Archived</span>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Status Transition Modal */}
      {activeItem && actionTargetStatus && (
        <Modal
          isOpen={true}
          onClose={() => {
            setActiveItem(null);
            setActionTargetStatus(null);
          }}
          title={`Confirm Status Transition: ${actionTargetStatus}`}
          subtitle={`Item: ${activeItem.sku_code} — ${activeItem.description}`}
          maxWidth="md"
        >
          <div className="space-y-4">
            <div className="p-3 rounded-lg bg-[var(--bg-tertiary)] border border-[var(--border-subtle)] text-xs space-y-1">
              <div className="flex justify-between">
                <span className="text-[var(--text-secondary)]">Current Status:</span>
                <StatusBadge status={activeItem.status} />
              </div>
              <div className="flex justify-between">
                <span className="text-[var(--text-secondary)]">New Status:</span>
                <StatusBadge status={actionTargetStatus} />
              </div>
              <div className="flex justify-between">
                <span className="text-[var(--text-secondary)]">Facility:</span>
                <span className="font-semibold text-[var(--text-primary)]">{activeItem.cpse} ({activeItem.depot_location})</span>
              </div>
            </div>

            {actionTargetStatus === "IDLE_SURPLUS" && (
              <div className="p-3 rounded-lg bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 text-xs text-emerald-800 dark:text-emerald-300 leading-relaxed">
                <strong>Broadcast Notice:</strong> Marking this spare as Idle Surplus will immediately mirror the node into Neo4j and publish it to the sister CPSE surplus discovery radar across IOCL, ONGC, BPCL, HPCL, and GAIL.
              </div>
            )}

            <div>
              <label className="text-[11px] font-semibold text-[var(--text-secondary)] block mb-1">
                Site Engineer Transition Justification Note
              </label>
              <textarea
                rows={3}
                value={actionNote}
                onChange={(e) => setActionNote(e.target.value)}
                className="app-input w-full text-xs"
                placeholder="Specify reason for status transition..."
              />
            </div>

            <div className="flex items-center justify-end gap-2 pt-2 border-t border-[var(--border-subtle)]">
              <button
                onClick={() => {
                  setActiveItem(null);
                  setActionTargetStatus(null);
                }}
                className="btn-secondary"
              >
                Cancel
              </button>
              <button
                onClick={handleConfirmStatusUpdate}
                disabled={isUpdating}
                className="btn-primary"
              >
                {isUpdating ? (
                  <>
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                    <span>Updating Ledger...</span>
                  </>
                ) : (
                  <>
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>Confirm Transition</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}
