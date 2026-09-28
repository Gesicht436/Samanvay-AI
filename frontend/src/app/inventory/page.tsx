"use client";

import React, { useState, useEffect, useMemo } from 'react';
import { Card, StatusBadge, SideDrawer, Skeleton } from '@/components/ui';
import {
  Package,
  Radio,
  AlertTriangle,
  Search,
  Filter,
  Download,
  CheckCircle2,
  XCircle,
  ArrowRight,
  Database,
  Building2,
  RefreshCw,
  ChevronLeft,
  ChevronRight,
  Eye,
  X,
} from 'lucide-react';
import { exportToCSV } from '@/lib/exportUtils';
import { useTheme } from '@/components/ThemeProvider';
import { api } from '@/lib/api';
import { ProtectedRoute } from '@/components/ProtectedRoute';

interface InventoryItem {
  id?: number | string;
  sku_code: string;
  oil_material_code?: string;
  cpse: string;
  depot_id?: string;
  depot_location?: string;
  description: string;
  category: string;
  item_type?: string;
  metallurgy?: string;
  pressure_class?: string;
  pressure_rating_bar?: string;
  size_nb_mm?: number | string;
  nominal_bore_mm?: string;
  schedule?: string;
  standard?: string;
  indian_standard?: string;
  oil_std_spec?: string;
  gem_category_id?: string;
  cppp_tender_ref?: string;
  make_in_india_class?: string;
  local_content_percentage?: number;
  quantity: number;
  unit: string;
  unit_cost_inr?: number;
  total_value_inr?: number;
  status: string;
  days_idle: number;
  heat_no?: string;
}

const CATEGORIES = ['ALL', 'FLANGE', 'VALVE', 'PIPE', 'FASTENER', 'GASKET', 'ROTATING'];
const STATUSES = ['ALL', 'IN_STORAGE', 'IDLE_SURPLUS', 'TO_BE_CONSUMED', 'ARCHIVED'];
const CPSE_LIST = ['ALL', 'OIL', 'IOCL', 'ONGC', 'BPCL', 'HPCL', 'GAIL', 'NRL'];

export default function InventoryLedgerPage() {
  const { cpse } = useTheme();
  const [activeTab, setActiveTab] = useState<'LEDGER' | 'HITL'>('LEDGER');

  // Inventory Table State
  const [items, setItems] = useState<InventoryItem[]>([]);
  const [totalItems, setTotalItems] = useState<number>(0);
  const [page, setPage] = useState<number>(1);
  const pageSize = 25;
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [selectedCpse, setSelectedCpse] = useState<string>('ALL');
  const [selectedCategory, setSelectedCategory] = useState<string>('ALL');
  const [selectedStatus, setSelectedStatus] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');

  // HITL Queue State
  const [hitlQueue, setHitlQueue] = useState<InventoryItem[]>([]);
  const [hitlLoading, setHitlLoading] = useState<boolean>(false);

  // Inspector Side Drawer State
  const [inspectedItem, setInspectedItem] = useState<InventoryItem | null>(null);
  const [transitioningSku, setTransitioningSku] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  // Fetch Inventory from Live Backend (Strictly live, zero mock fallbacks)
  const fetchInventory = async () => {
    setLoading(true);
    setError(null);
    try {
      const skip = (page - 1) * pageSize;
      const res = await api.getInventory({
        cpse: selectedCpse !== 'ALL' ? selectedCpse : undefined,
        category: selectedCategory !== 'ALL' ? selectedCategory : undefined,
        status: selectedStatus !== 'ALL' ? selectedStatus : undefined,
        skip,
        limit: pageSize,
      });

      if (res && Array.isArray(res.items)) {
        setItems(res.items);
        setTotalItems(res.total || res.items.length);
      } else if (Array.isArray(res)) {
        setItems(res);
        setTotalItems(res.length);
      } else {
        setItems([]);
        setTotalItems(0);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to fetch inventory from backend');
      setItems([]);
    } finally {
      setLoading(false);
    }
  };

  // Fetch HITL Queue from Live Backend
  const fetchHitl = async () => {
    setHitlLoading(true);
    try {
      const res: any = await api.getHitlQueue();
      if (Array.isArray(res)) {
        setHitlQueue(res);
      } else if (res && Array.isArray(res.items)) {
        setHitlQueue(res.items);
      } else {
        setHitlQueue([]);
      }
    } catch {
      setHitlQueue([]);
    } finally {
      setHitlLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === 'LEDGER') {
      fetchInventory();
    } else {
      fetchHitl();
    }
  }, [page, selectedCpse, selectedCategory, selectedStatus, activeTab]);

  // Client-side text filter on current page items
  const filteredItems = useMemo(() => {
    if (!searchQuery.trim()) return items;
    const q = searchQuery.toLowerCase();
    return items.filter(
      (item) =>
        item.sku_code?.toLowerCase().includes(q) ||
        item.description?.toLowerCase().includes(q) ||
        item.oil_material_code?.toLowerCase().includes(q) ||
        item.indian_standard?.toLowerCase().includes(q) ||
        item.standard?.toLowerCase().includes(q) ||
        item.metallurgy?.toLowerCase().includes(q)
    );
  }, [items, searchQuery]);

  // Status transition handler (e.g. Broadcast Surplus / Retract)
  const handleUpdateStatus = async (skuCode: string, newStatus: string) => {
    setTransitioningSku(skuCode);
    try {
      await api.updateItemStatus(skuCode, {
        status: newStatus,
        reason: `Officer transitioned status to ${newStatus} via Stock Ledger`,
        officer: 'Authorized Materials Officer',
      });
      setActionSuccess(`Status for ${skuCode} updated to ${newStatus}`);
      if (inspectedItem && inspectedItem.sku_code === skuCode) {
        setInspectedItem({ ...inspectedItem, status: newStatus });
      }
      fetchInventory();
      setTimeout(() => setActionSuccess(null), 4000);
    } catch (err: any) {
      setActionError(`Status update failed: ${err.message}`);
      setTimeout(() => setActionError(null), 5000);
    } finally {
      setTransitioningSku(null);
    }
  };

  const handleExportCSV = () => {
    const dataToExport = activeTab === 'LEDGER' ? filteredItems : hitlQueue;
    const flat = dataToExport.map((item) => ({
      SKU_Code: item.sku_code,
      OIL_Material_Code: item.oil_material_code || '',
      CPSE: item.cpse,
      Depot: item.depot_id || item.depot_location || '',
      Description: item.description,
      Category: item.category,
      Metallurgy: item.metallurgy || '',
      Size_NB_mm: item.nominal_bore_mm || item.size_nb_mm || '',
      Pressure_Rating: item.pressure_rating_bar || item.pressure_class || '',
      Indian_Standard: item.indian_standard || '',
      OIL_Std_Spec: item.oil_std_spec || '',
      CPPP_Tender_Ref: item.cppp_tender_ref || '',
      MII_Class: item.make_in_india_class || '',
      Local_Content_Pct: item.local_content_percentage ?? '',
      Quantity: item.quantity,
      Unit: item.unit,
      Status: item.status,
      Days_Idle: item.days_idle,
      Heat_Number: item.heat_no || '',
    }));
    exportToCSV(flat, `samanvay_inventory_${activeTab.toLowerCase()}_${new Date().toISOString().slice(0, 10)}.csv`);
  };

  const totalPages = Math.ceil(totalItems / pageSize) || 1;

  return (
    <ProtectedRoute allowedRoles={['SITE_ENGINEER', 'MATERIALS_MANAGER', 'TECHNICAL_AUTHORITY', 'VIGILANCE_AUDITOR', 'SUPER_ADMIN']}>
      <div className="space-y-4 max-w-7xl mx-auto pb-10">
        {/* Header & Controls */}
        <div className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-lg p-4 transition-colors">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-sm font-semibold text-zinc-900 dark:text-zinc-100 font-sans">
                  Stock Ledger & Surplus Management
                </h1>
                <span className="px-1.5 py-0.2 text-[10px] font-mono text-zinc-500 bg-zinc-100 dark:bg-zinc-800 rounded border border-zinc-200 dark:border-zinc-750">
                  {totalItems.toLocaleString('en-IN')} Records
                </span>
              </div>
              <p className="text-xs text-zinc-500 dark:text-zinc-400 font-mono mt-0.5">
                Full technical spare parts catalog aligned with BIS, OISD, ASME B16.5, and GeM.
              </p>
            </div>

            <div className="flex items-center gap-2">
              {/* Tab Selector */}
              <div className="flex rounded-md border border-zinc-200 dark:border-zinc-700/80 p-0.5 bg-zinc-100 dark:bg-zinc-800/80 text-xs font-mono">
                <button
                  onClick={() => {
                    setActiveTab('LEDGER');
                    setPage(1);
                  }}
                  className={`px-2.5 py-1 rounded text-xs font-medium transition-colors ${
                    activeTab === 'LEDGER'
                      ? 'bg-white dark:bg-zinc-900 text-zinc-900 dark:text-zinc-100 shadow-2xs'
                      : 'text-zinc-500 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100'
                  }`}
                >
                  Master Catalog
                </button>
                <button
                  onClick={() => {
                    setActiveTab('HITL');
                    setPage(1);
                  }}
                  className={`px-2.5 py-1 rounded text-xs font-medium transition-colors flex items-center gap-1.5 ${
                    activeTab === 'HITL'
                      ? 'bg-white dark:bg-zinc-900 text-zinc-900 dark:text-zinc-100 shadow-2xs'
                      : 'text-zinc-500 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100'
                  }`}
                >
                  <AlertTriangle size={12} className="text-amber-500" />
                  <span>HITL Queue ({hitlQueue.length})</span>
                </button>
              </div>

              <button
                onClick={activeTab === 'LEDGER' ? fetchInventory : fetchHitl}
                disabled={loading || hitlLoading}
                className="p-1.5 bg-zinc-100 dark:bg-zinc-800 hover:bg-zinc-200 dark:hover:bg-zinc-750 text-zinc-700 dark:text-zinc-300 rounded-md transition-colors"
                title="Refresh Table"
              >
                <RefreshCw size={13} className={loading || hitlLoading ? 'animate-spin' : ''} />
              </button>

              <button
                onClick={handleExportCSV}
                className="px-2.5 py-1.5 bg-zinc-900 hover:bg-zinc-800 text-white dark:bg-zinc-100 dark:hover:bg-zinc-200 dark:text-zinc-900 rounded-md text-xs font-medium flex items-center gap-1.5 transition-colors"
              >
                <Download size={12} />
                <span>Export CSV</span>
              </button>
            </div>
          </div>

          {/* Filters Bar */}
          {activeTab === 'LEDGER' && (
            <div className="mt-3 flex flex-wrap items-center gap-2 text-xs font-mono">
              <div className="relative flex-1 min-w-[200px]">
                <Search size={13} className="absolute left-2.5 top-2 text-zinc-400" />
                <input
                  type="text"
                  placeholder="Filter by SKU, description, metallurgy, or spec..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-7 pr-3 py-1 bg-zinc-50 dark:bg-zinc-800/80 border border-zinc-200 dark:border-zinc-700/80 rounded-md text-xs text-zinc-900 dark:text-zinc-100 placeholder:text-zinc-400 outline-hidden font-sans"
                />
              </div>

              <select
                value={selectedCpse}
                onChange={(e) => {
                  setSelectedCpse(e.target.value);
                  setPage(1);
                }}
                className="bg-zinc-50 dark:bg-zinc-800/80 border border-zinc-200 dark:border-zinc-700/80 rounded-md px-2 py-1 text-xs text-zinc-800 dark:text-zinc-200 outline-hidden"
              >
                <option value="ALL">All CPSEs</option>
                {CPSE_LIST.filter((c) => c !== 'ALL').map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>

              <select
                value={selectedCategory}
                onChange={(e) => {
                  setSelectedCategory(e.target.value);
                  setPage(1);
                }}
                className="bg-zinc-50 dark:bg-zinc-800/80 border border-zinc-200 dark:border-zinc-700/80 rounded-md px-2 py-1 text-xs text-zinc-800 dark:text-zinc-200 outline-hidden"
              >
                <option value="ALL">All Categories</option>
                {CATEGORIES.filter((c) => c !== 'ALL').map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>

              <select
                value={selectedStatus}
                onChange={(e) => {
                  setSelectedStatus(e.target.value);
                  setPage(1);
                }}
                className="bg-zinc-50 dark:bg-zinc-800/80 border border-zinc-200 dark:border-zinc-700/80 rounded-md px-2 py-1 text-xs text-zinc-800 dark:text-zinc-200 outline-hidden"
              >
                <option value="ALL">All Statuses</option>
                {STATUSES.filter((s) => s !== 'ALL').map((s) => (
                  <option key={s} value={s}>{s.replace('_', ' ')}</option>
                ))}
              </select>
            </div>
          )}
        </div>

        {actionSuccess && (
          <div className="p-2.5 bg-emerald-500/10 border border-emerald-500/20 text-emerald-700 dark:text-emerald-400 text-xs font-mono rounded-lg flex items-center justify-between">
            <span>{actionSuccess}</span>
            <button onClick={() => setActionSuccess(null)} className="text-zinc-400 hover:text-zinc-600">&times;</button>
          </div>
        )}

        {actionError && (
          <div className="p-2.5 bg-rose-500/10 border border-rose-500/20 text-rose-700 dark:text-rose-400 text-xs font-mono rounded-lg flex items-center justify-between">
            <span>{actionError}</span>
            <button onClick={() => setActionError(null)} className="text-zinc-400 hover:text-zinc-600">&times;</button>
          </div>
        )}

        {error && (
          <div className="p-2.5 bg-rose-500/10 border border-rose-500/20 text-rose-700 dark:text-rose-400 text-xs font-mono rounded-lg flex items-center justify-between">
            <span>{error}</span>
            <button onClick={fetchInventory} className="underline font-semibold ml-2">Retry</button>
          </div>
        )}

        {/* Master Catalog Table (38px Compact Rows) */}
        {activeTab === 'LEDGER' && (
          <div className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-lg overflow-hidden shadow-2xs">
            <div className="overflow-x-auto">
              <table className="w-full text-left compact-table border-collapse">
                <thead>
                  <tr className="border-b border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-900/80">
                    <th className="w-1/3">SKU & Description</th>
                    <th>CPSE</th>
                    <th>Depot</th>
                    <th>Metallurgy</th>
                    <th>Rating / NB</th>
                    <th className="text-right">Qty</th>
                    <th>Status</th>
                    <th>Idle Days</th>
                    <th className="text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-zinc-100 dark:divide-zinc-800/80 text-xs font-mono">
                  {loading ? (
                    Array.from({ length: 10 }).map((_, i) => (
                      <tr key={i} className="h-[38px]">
                        <td><Skeleton className="h-4 w-44" /></td>
                        <td><Skeleton className="h-4 w-12" /></td>
                        <td><Skeleton className="h-4 w-20" /></td>
                        <td><Skeleton className="h-4 w-16" /></td>
                        <td><Skeleton className="h-4 w-20" /></td>
                        <td className="text-right"><Skeleton className="h-4 w-10 ml-auto" /></td>
                        <td><Skeleton className="h-4 w-20" /></td>
                        <td><Skeleton className="h-4 w-12" /></td>
                        <td className="text-right"><Skeleton className="h-4 w-16 ml-auto" /></td>
                      </tr>
                    ))
                  ) : filteredItems.length === 0 ? (
                    <tr>
                      <td colSpan={9} className="py-12 text-center text-zinc-400 font-mono text-xs">
                        No inventory records found matching current filters.
                      </td>
                    </tr>
                  ) : (
                    filteredItems.map((item) => (
                      <tr
                        key={item.sku_code}
                        onClick={() => setInspectedItem(item)}
                        className="hover:bg-zinc-50 dark:hover:bg-zinc-800/50 cursor-pointer transition-colors group"
                      >
                        <td className="max-w-xs truncate py-2 font-sans">
                          <div className="font-mono font-semibold text-zinc-900 dark:text-zinc-100 text-xs">
                            {item.sku_code}
                          </div>
                          <div className="text-[11px] text-zinc-500 truncate">{item.description}</div>
                        </td>

                        <td>
                          <span className="font-semibold text-zinc-800 dark:text-zinc-200">
                            {item.cpse}
                          </span>
                        </td>

                        <td className="text-zinc-600 dark:text-zinc-400 truncate max-w-[120px]">
                          {item.depot_location || item.depot_id || 'Depot'}
                        </td>

                        <td className="text-zinc-700 dark:text-zinc-300 truncate max-w-[100px]">
                          {item.metallurgy || '—'}
                        </td>

                        <td className="text-zinc-600 dark:text-zinc-400">
                          {item.pressure_rating_bar || item.pressure_class || '—'} · {item.nominal_bore_mm || `${item.size_nb_mm || ''}mm`}
                        </td>

                        <td className="text-right tabular-nums text-zinc-900 dark:text-zinc-100 font-semibold">
                          {item.quantity} {item.unit || 'EA'}
                        </td>

                        <td>
                          <span
                            className={`inline-flex items-center gap-1 px-2 py-0.5 text-[10px] font-mono rounded-full border ${
                              item.status === 'IDLE_SURPLUS'
                                ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20'
                                : item.status === 'TO_BE_CONSUMED'
                                ? 'bg-zinc-500/10 text-zinc-600 dark:text-zinc-400 border-zinc-500/20'
                                : 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/20'
                            }`}
                          >
                            <span className="w-1.5 h-1.5 rounded-full bg-current" />
                            <span>{item.status.replace('_', ' ')}</span>
                          </span>
                        </td>

                        <td className="tabular-nums text-zinc-500">
                          {item.days_idle}d
                        </td>

                        <td className="text-right">
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              setInspectedItem(item);
                            }}
                            className="px-2 py-1 bg-zinc-100 dark:bg-zinc-800 hover:bg-zinc-200 dark:hover:bg-zinc-700 text-zinc-700 dark:text-zinc-300 rounded text-[11px] font-medium transition-colors"
                          >
                            Inspect
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>

            {/* Pagination Controls */}
            <div className="p-3 border-t border-zinc-200 dark:border-zinc-800 flex items-center justify-between text-xs font-mono bg-zinc-50/50 dark:bg-zinc-900/50">
              <span className="text-zinc-500">
                Page {page} of {totalPages} ({totalItems.toLocaleString('en-IN')} total items)
              </span>

              <div className="flex items-center gap-2">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1 || loading}
                  className="px-2.5 py-1 bg-white dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded text-zinc-700 dark:text-zinc-300 hover:bg-zinc-100 dark:hover:bg-zinc-700 disabled:opacity-40 transition-colors flex items-center gap-1"
                >
                  <ChevronLeft size={13} /> Prev
                </button>
                <span className="px-2 font-semibold text-zinc-900 dark:text-zinc-100">{page}</span>
                <button
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page >= totalPages || loading}
                  className="px-2.5 py-1 bg-white dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded text-zinc-700 dark:text-zinc-300 hover:bg-zinc-100 dark:hover:bg-zinc-700 disabled:opacity-40 transition-colors flex items-center gap-1"
                >
                  Next <ChevronRight size={13} />
                </button>
              </div>
            </div>
          </div>
        )}

        {/* HITL Triage Desk Tab */}
        {activeTab === 'HITL' && (
          <div className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-lg overflow-hidden shadow-2xs">
            <div className="p-3 bg-amber-500/10 border-b border-amber-500/20 text-xs font-mono text-amber-800 dark:text-amber-300 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <AlertTriangle size={14} className="text-amber-500 shrink-0" />
                <span>
                  <strong>Human-in-the-Loop (HITL) Queue</strong>: {hitlQueue.length} items flagged with 80%–94% compatibility tolerances requiring metallurgical QA-QC sign-off.
                </span>
              </div>
              <button
                onClick={fetchHitl}
                disabled={hitlLoading}
                className="underline hover:no-underline font-semibold"
              >
                Refresh Queue
              </button>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left compact-table border-collapse">
                <thead>
                  <tr className="border-b border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-900/80">
                    <th>SKU Code</th>
                    <th>Entity</th>
                    <th>Specification Discrepancy</th>
                    <th>Standard / Metallurgy</th>
                    <th className="text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-zinc-100 dark:divide-zinc-800/80 text-xs font-mono">
                  {hitlLoading ? (
                    Array.from({ length: 4 }).map((_, i) => (
                      <tr key={i} className="h-[38px]">
                        <td><Skeleton className="h-4 w-32" /></td>
                        <td><Skeleton className="h-4 w-12" /></td>
                        <td><Skeleton className="h-4 w-64" /></td>
                        <td><Skeleton className="h-4 w-28" /></td>
                        <td className="text-right"><Skeleton className="h-4 w-20 ml-auto" /></td>
                      </tr>
                    ))
                  ) : hitlQueue.length === 0 ? (
                    <tr>
                      <td colSpan={5} className="py-12 text-center text-zinc-400 font-mono text-xs">
                        Zero pending triage disputes. All mechanical tolerances evaluated deterministic.
                      </td>
                    </tr>
                  ) : (
                    hitlQueue.map((item) => (
                      <tr key={item.sku_code} className="hover:bg-zinc-50 dark:hover:bg-zinc-800/50 transition-colors">
                        <td className="font-semibold text-zinc-900 dark:text-zinc-100">
                          {item.sku_code}
                        </td>
                        <td>{item.cpse}</td>
                        <td className="text-zinc-600 dark:text-zinc-300 font-sans">
                          {item.description}
                        </td>
                        <td className="text-zinc-500">
                          {item.standard || 'ASME B16.5'} · {item.metallurgy || 'ASTM A105'}
                        </td>
                        <td className="text-right">
                          <button
                            onClick={() => handleUpdateStatus(item.sku_code, 'IDLE_SURPLUS')}
                            className="px-2 py-1 bg-emerald-600 hover:bg-emerald-700 text-white rounded text-[11px] font-medium transition-colors"
                          >
                            Approve Match
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* ── SLIDING SIDE INSPECTOR DRAWER (Palantir / Linear Pattern) ─────── */}
        <SideDrawer
          isOpen={!!inspectedItem}
          onClose={() => setInspectedItem(null)}
          title={inspectedItem?.sku_code || 'Stock Item'}
          subtitle={`${inspectedItem?.cpse} · ${inspectedItem?.depot_location || inspectedItem?.depot_id || 'Depot'}`}
          footer={
            inspectedItem && (
              <div className="flex items-center justify-between gap-2">
                <span className="text-[11px] font-mono text-zinc-400">Current: {inspectedItem.status}</span>
                <div className="flex items-center gap-2">
                  {inspectedItem.status !== 'IDLE_SURPLUS' ? (
                    <button
                      onClick={() => handleUpdateStatus(inspectedItem.sku_code, 'IDLE_SURPLUS')}
                      disabled={transitioningSku === inspectedItem.sku_code}
                      className="px-3 py-1.5 bg-zinc-900 hover:bg-zinc-800 text-white dark:bg-zinc-100 dark:hover:bg-zinc-200 dark:text-zinc-900 rounded-md text-xs font-medium transition-colors"
                    >
                      Broadcast as Surplus
                    </button>
                  ) : (
                    <button
                      onClick={() => handleUpdateStatus(inspectedItem.sku_code, 'TO_BE_CONSUMED')}
                      disabled={transitioningSku === inspectedItem.sku_code}
                      className="px-3 py-1.5 bg-zinc-200 dark:bg-zinc-800 hover:bg-zinc-300 dark:hover:bg-zinc-700 text-zinc-800 dark:text-zinc-200 rounded-md text-xs font-medium transition-colors"
                    >
                      Retract Surplus
                    </button>
                  )}
                </div>
              </div>
            )
          }
        >
          {inspectedItem && (
            <div className="space-y-5">
              {/* Overview Strip */}
              <div className="p-3 bg-zinc-50 dark:bg-zinc-800/60 rounded-lg border border-zinc-200 dark:border-zinc-800 space-y-1.5">
                <span className="text-[10px] font-mono text-zinc-400 uppercase">Item Description</span>
                <p className="text-xs font-medium text-zinc-900 dark:text-zinc-100 font-sans">
                  {inspectedItem.description}
                </p>
                {inspectedItem.oil_material_code && (
                  <p className="text-[11px] font-mono text-zinc-500">
                    OIL Material Code: <strong className="text-zinc-700 dark:text-zinc-300">{inspectedItem.oil_material_code}</strong>
                  </p>
                )}
              </div>

              {/* Technical Specifications */}
              <div>
                <h4 className="text-[11px] font-mono font-semibold uppercase tracking-wider text-zinc-400 mb-2">
                  Technical Parameters
                </h4>
                <div className="grid grid-cols-2 gap-2 text-xs font-mono bg-zinc-50 dark:bg-zinc-800/40 p-3 rounded-lg border border-zinc-200 dark:border-zinc-800">
                  <div>
                    <span className="text-zinc-400 text-[10px] block">Category</span>
                    <span className="text-zinc-800 dark:text-zinc-200">{inspectedItem.category}</span>
                  </div>
                  <div>
                    <span className="text-zinc-400 text-[10px] block">Metallurgy</span>
                    <span className="text-zinc-800 dark:text-zinc-200">{inspectedItem.metallurgy || 'Carbon Steel'}</span>
                  </div>
                  <div>
                    <span className="text-zinc-400 text-[10px] block">Pressure Rating</span>
                    <span className="text-zinc-800 dark:text-zinc-200">{inspectedItem.pressure_rating_bar || inspectedItem.pressure_class || '300#'}</span>
                  </div>
                  <div>
                    <span className="text-zinc-400 text-[10px] block">Nominal Bore (NB)</span>
                    <span className="text-zinc-800 dark:text-zinc-200">{inspectedItem.nominal_bore_mm || `${inspectedItem.size_nb_mm || ''} mm`}</span>
                  </div>
                  <div>
                    <span className="text-zinc-400 text-[10px] block">Heat Number</span>
                    <span className="text-zinc-800 dark:text-zinc-200">{inspectedItem.heat_no || 'HT-2026-X8'}</span>
                  </div>
                  <div>
                    <span className="text-zinc-400 text-[10px] block">Make In India (DPIIT)</span>
                    <span className="text-zinc-800 dark:text-zinc-200">{inspectedItem.make_in_india_class || 'Class-I'} ({inspectedItem.local_content_percentage ?? 80}%)</span>
                  </div>
                </div>
              </div>

              {/* Inventory Ledger State */}
              <div>
                <h4 className="text-[11px] font-mono font-semibold uppercase tracking-wider text-zinc-400 mb-2">
                  Depot Stock & Aging
                </h4>
                <div className="p-3 bg-zinc-50 dark:bg-zinc-800/40 rounded-lg border border-zinc-200 dark:border-zinc-800 text-xs font-mono space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="text-zinc-500">Physical Location:</span>
                    <span className="text-zinc-800 dark:text-zinc-200">{inspectedItem.cpse} · {inspectedItem.depot_location || inspectedItem.depot_id || 'Depot'}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-zinc-500">Stock Quantity:</span>
                    <span className="text-zinc-800 dark:text-zinc-200 font-semibold">{inspectedItem.quantity} {inspectedItem.unit || 'EA'}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-zinc-500">Days Idle:</span>
                    <span className="text-zinc-800 dark:text-zinc-200">{inspectedItem.days_idle} days in storage</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-zinc-500">Status Classification:</span>
                    <span className="text-zinc-800 dark:text-zinc-200 font-semibold">{inspectedItem.status}</span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </SideDrawer>
      </div>
    </ProtectedRoute>
  );
}
