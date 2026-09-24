"use client";

import React, { useState, useEffect, useMemo } from 'react';
import { Card, KpiCard } from '@/components/ui';
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

  // Modal / Detail State
  const [selectedItem, setSelectedItem] = useState<InventoryItem | null>(null);
  const [transitioningSku, setTransitioningSku] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  // Fetch Inventory from Live Backend
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
        item.heat_no?.toLowerCase().includes(q)
    );
  }, [items, searchQuery]);

  // Status Change handler
  const handleUpdateStatus = async (skuCode: string, newStatus: string) => {
    setTransitioningSku(skuCode);
    try {
      await api.updateItemStatus(skuCode, {
        status: newStatus,
        reason: `Status updated via web console to ${newStatus}`,
        officer: `OFFICER_${cpse}`,
      });
      setActionSuccess(`SKU ${skuCode} transitioned to ${newStatus}`);
      setTimeout(() => setActionSuccess(null), 4000);
      if (activeTab === 'LEDGER') {
        fetchInventory();
      } else {
        fetchHitl();
      }
      if (selectedItem?.sku_code === skuCode) {
        setSelectedItem((prev) => (prev ? { ...prev, status: newStatus } : null));
      }
    } catch (err: any) {
      alert(`Status transition failed: ${err.message}`);
    } finally {
      setTransitioningSku(null);
    }
  };

  // Export to CSV
  const handleExportCSV = () => {
    const dataToExport = activeTab === 'LEDGER' ? filteredItems : hitlQueue;
    if (dataToExport.length === 0) {
      alert('No data available to export.');
      return;
    }
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
      <div className="flex flex-col space-y-4 max-w-[1600px] mx-auto pb-8">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-5 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl shadow-2xs">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-mono font-semibold text-emerald-700 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/60 px-2 py-0.5 rounded border border-emerald-200 dark:border-emerald-800">
              STOCK LEDGER
            </span>
            <span className="text-xs font-mono text-slate-500">
              Live Database: {totalItems.toLocaleString('en-IN')} records
            </span>
          </div>
          <h1 className="text-xl font-bold text-slate-900 dark:text-white tracking-tight">
            Inter-CPSE Inventory & Surplus Ledger
          </h1>
          <p className="text-xs text-slate-600 dark:text-slate-400 mt-0.5">
            Full technical catalog aligned with BIS, OISD, EIL, GeM, and CPPP standards.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <div className="flex rounded-md border border-slate-300 dark:border-slate-700 p-0.5 bg-slate-100 dark:bg-slate-800">
            <button
              onClick={() => {
                setActiveTab('LEDGER');
                setPage(1);
              }}
              className={`px-3 py-1.5 rounded text-xs font-mono font-semibold transition-colors ${
                activeTab === 'LEDGER'
                  ? 'bg-white dark:bg-slate-900 text-slate-900 dark:text-white shadow-2xs'
                  : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
              }`}
            >
              Master Catalog ({totalItems})
            </button>
            <button
              onClick={() => {
                setActiveTab('HITL');
                setPage(1);
              }}
              className={`px-3 py-1.5 rounded text-xs font-mono font-semibold transition-colors flex items-center gap-1.5 ${
                activeTab === 'HITL'
                  ? 'bg-white dark:bg-slate-900 text-slate-900 dark:text-white shadow-2xs'
                  : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
              }`}
            >
              <AlertTriangle size={12} className="text-amber-500" />
              <span>HITL Queue ({hitlQueue.length})</span>
            </button>
          </div>

          <button
            onClick={activeTab === 'LEDGER' ? fetchInventory : fetchHitl}
            disabled={loading || hitlLoading}
            className="p-2 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 border border-slate-300 dark:border-slate-700 rounded transition-colors"
            title="Refresh Data"
          >
            <RefreshCw size={14} className={loading || hitlLoading ? 'animate-spin' : ''} />
          </button>

          <button
            onClick={handleExportCSV}
            className="px-3 py-2 bg-slate-900 dark:bg-slate-800 hover:bg-slate-800 dark:hover:bg-slate-700 text-white rounded text-xs font-mono font-semibold flex items-center gap-1.5 transition-colors"
          >
            <Download size={13} />
            <span>Export CSV</span>
          </button>
        </div>
      </div>

      {actionSuccess && (
        <div className="p-3 bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 text-emerald-800 dark:text-emerald-300 text-xs font-mono rounded-lg flex items-center justify-between">
          <span>{actionSuccess}</span>
          <button onClick={() => setActionSuccess(null)} className="text-slate-500 hover:text-slate-700">&times;</button>
        </div>
      )}

      {error && (
        <div className="p-3 bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900 text-rose-800 dark:text-rose-300 text-xs font-mono rounded-lg flex items-center justify-between">
          <span>{error}</span>
          <button onClick={fetchInventory} className="underline font-semibold">Retry</button>
        </div>
      )}

      {/* Filter & Search Bar */}
      <div className="p-3.5 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl flex flex-wrap items-center justify-between gap-3 text-xs font-mono">
        <div className="flex flex-wrap items-center gap-2 flex-1 min-w-[300px]">
          <div className="relative flex-1 min-w-[200px] max-w-md">
            <Search size={14} className="absolute left-3 top-2.5 text-slate-400" />
            <input
              type="text"
              placeholder="Search SKU, OIL material code, standard, heat no..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-8 pr-3 py-1.5 bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded text-slate-900 dark:text-slate-100 placeholder:text-slate-400 focus:outline-hidden focus:ring-1 focus:ring-emerald-500 text-xs"
            />
          </div>

          <div className="flex items-center gap-1.5">
            <span className="text-slate-500">CPSE:</span>
            <select
              value={selectedCpse}
              onChange={(e) => {
                setSelectedCpse(e.target.value);
                setPage(1);
              }}
              className="bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded px-2 py-1 text-xs text-slate-800 dark:text-slate-200"
            >
              {CPSE_LIST.map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </div>

          <div className="flex items-center gap-1.5">
            <span className="text-slate-500">Category:</span>
            <select
              value={selectedCategory}
              onChange={(e) => {
                setSelectedCategory(e.target.value);
                setPage(1);
              }}
              className="bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded px-2 py-1 text-xs text-slate-800 dark:text-slate-200"
            >
              {CATEGORIES.map((cat) => (
                <option key={cat} value={cat}>{cat}</option>
              ))}
            </select>
          </div>

          <div className="flex items-center gap-1.5">
            <span className="text-slate-500">Status:</span>
            <select
              value={selectedStatus}
              onChange={(e) => {
                setSelectedStatus(e.target.value);
                setPage(1);
              }}
              className="bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded px-2 py-1 text-xs text-slate-800 dark:text-slate-200"
            >
              {STATUSES.map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          </div>
        </div>

        <div className="text-slate-500 text-[11px]">
          Showing {filteredItems.length} records · Page {page} of {totalPages}
        </div>
      </div>

      {/* Main Table */}
      <Card className="p-0 border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono border-collapse">
            <thead>
              <tr className="bg-slate-50 dark:bg-slate-800/60 border-b border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-400">
                <th className="py-2.5 px-3 font-semibold">SKU / MESC CODE</th>
                <th className="py-2.5 px-3 font-semibold">CPSE / DEPOT</th>
                <th className="py-2.5 px-3 font-semibold">DESCRIPTION</th>
                <th className="py-2.5 px-3 font-semibold">STANDARDS & MII</th>
                <th className="py-2.5 px-3 font-semibold text-right">QTY</th>
                <th className="py-2.5 px-3 font-semibold text-center">IDLE</th>
                <th className="py-2.5 px-3 font-semibold text-center">STATUS</th>
                <th className="py-2.5 px-3 font-semibold text-right">ACTIONS</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60">
              {loading && activeTab === 'LEDGER' ? (
                <tr>
                  <td colSpan={8} className="py-16 text-center text-slate-500">
                    <RefreshCw className="animate-spin h-5 w-5 mx-auto mb-2 text-emerald-500" />
                    <span>Loading stock records from PostgreSQL...</span>
                  </td>
                </tr>
              ) : filteredItems.length === 0 ? (
                <tr>
                  <td colSpan={8} className="py-16 text-center text-slate-500">
                    No matching inventory items found.
                  </td>
                </tr>
              ) : (
                filteredItems.map((item) => (
                  <tr
                    key={item.sku_code}
                    className="hover:bg-slate-50/80 dark:hover:bg-slate-800/40 transition-colors"
                  >
                    <td className="py-2.5 px-3">
                      <div className="font-bold text-slate-900 dark:text-slate-100">{item.sku_code}</div>
                      {item.oil_material_code && (
                        <div className="text-[11px] text-emerald-700 dark:text-emerald-400">
                          MESC: {item.oil_material_code}
                        </div>
                      )}
                    </td>

                    <td className="py-2.5 px-3">
                      <span className="font-semibold text-slate-800 dark:text-slate-200">{item.cpse}</span>
                      <div className="text-[11px] text-slate-500 truncate max-w-[140px]">
                        {item.depot_location || item.depot_id || 'Main Yard'}
                      </div>
                    </td>

                    <td className="py-2.5 px-3 max-w-[340px]">
                      <div className="truncate text-slate-800 dark:text-slate-200 font-medium" title={item.description}>
                        {item.description}
                      </div>
                      <div className="text-[11px] text-slate-500 truncate">
                        {item.metallurgy} · {item.nominal_bore_mm || `${item.size_nb_mm || ''} mm`} · {item.pressure_rating_bar || item.pressure_class}
                      </div>
                    </td>

                    <td className="py-2.5 px-3 max-w-[220px]">
                      <div className="text-[11px] text-slate-700 dark:text-slate-300 truncate" title={item.indian_standard || item.standard}>
                        {item.indian_standard || item.standard || 'IS / ASME'}
                      </div>
                      <div className="text-[10px] text-slate-500 flex items-center gap-1.5">
                        {item.make_in_india_class && (
                          <span className="text-emerald-700 dark:text-emerald-400 font-semibold">
                            {item.make_in_india_class} ({item.local_content_percentage}%)
                          </span>
                        )}
                        {item.cppp_tender_ref && (
                          <span className="text-slate-400 truncate" title={item.cppp_tender_ref}>
                            CPPP: {item.cppp_tender_ref}
                          </span>
                        )}
                      </div>
                    </td>

                    <td className="py-2.5 px-3 text-right font-semibold text-slate-900 dark:text-slate-100">
                      {item.quantity} <span className="text-[10px] text-slate-500">{item.unit}</span>
                    </td>

                    <td className="py-2.5 px-3 text-center">
                      <span
                        className={`text-[11px] font-semibold ${
                          item.days_idle >= 90
                            ? 'text-amber-600 dark:text-amber-400 font-bold'
                            : 'text-slate-500'
                        }`}
                      >
                        {item.days_idle}d
                      </span>
                    </td>

                    <td className="py-2.5 px-3 text-center">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          item.status === 'IDLE_SURPLUS'
                            ? 'bg-emerald-100 dark:bg-emerald-950/80 text-emerald-800 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-800'
                            : item.status === 'TO_BE_CONSUMED'
                            ? 'bg-blue-100 dark:bg-blue-950/80 text-blue-800 dark:text-blue-300'
                            : 'bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300'
                        }`}
                      >
                        {item.status}
                      </span>
                    </td>

                    <td className="py-2.5 px-3 text-right">
                      <div className="flex items-center justify-end gap-1.5">
                        <button
                          onClick={() => setSelectedItem(item)}
                          className="px-2 py-1 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 rounded text-[11px] transition-colors"
                          title="View Full Technical Specifications"
                        >
                          Details
                        </button>
                        {item.status !== 'IDLE_SURPLUS' ? (
                          <button
                            onClick={() => handleUpdateStatus(item.sku_code, 'IDLE_SURPLUS')}
                            disabled={transitioningSku === item.sku_code}
                            className="px-2 py-1 bg-emerald-600 hover:bg-emerald-700 text-white rounded text-[11px] font-semibold transition-colors disabled:opacity-50"
                            title="Declare surplus to sister CPSEs"
                          >
                            Broadcast
                          </button>
                        ) : (
                          <button
                            onClick={() => handleUpdateStatus(item.sku_code, 'TO_BE_CONSUMED')}
                            disabled={transitioningSku === item.sku_code}
                            className="px-2 py-1 bg-slate-200 dark:bg-slate-700 hover:bg-slate-300 dark:hover:bg-slate-600 text-slate-800 dark:text-slate-200 rounded text-[11px] transition-colors disabled:opacity-50"
                            title="Withdraw surplus declaration"
                          >
                            Retract
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Bar */}
        <div className="p-3 border-t border-slate-200 dark:border-slate-800 flex items-center justify-between text-xs font-mono bg-slate-50/50 dark:bg-slate-850">
          <span className="text-slate-500">
            Page {page} of {totalPages} ({totalItems.toLocaleString('en-IN')} total items)
          </span>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1 || loading}
              className="px-2.5 py-1 bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 disabled:opacity-40 transition-colors flex items-center gap-1"
            >
              <ChevronLeft size={14} /> Previous
            </button>
            <span className="px-2 font-bold text-slate-900 dark:text-slate-100">{page}</span>
            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page >= totalPages || loading}
              className="px-2.5 py-1 bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 disabled:opacity-40 transition-colors flex items-center gap-1"
            >
              Next <ChevronRight size={14} />
            </button>
          </div>
        </div>
      </Card>

      {/* Item Detail Modal */}
      {selectedItem && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto flex flex-col">
            <div className="p-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
              <div>
                <h3 className="text-base font-bold font-mono text-slate-900 dark:text-white">
                  Technical Specification: {selectedItem.sku_code}
                </h3>
                <p className="text-xs font-mono text-slate-500">
                  {selectedItem.cpse} · {selectedItem.depot_location || selectedItem.depot_id}
                </p>
              </div>
              <button
                onClick={() => setSelectedItem(null)}
                className="p-1 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
              >
                <X size={18} />
              </button>
            </div>

            <div className="p-5 space-y-4 text-xs font-mono flex-1">
              <div>
                <span className="text-slate-400 block mb-0.5">Description</span>
                <p className="text-slate-900 dark:text-slate-100 font-medium bg-slate-50 dark:bg-slate-800 p-2.5 rounded border border-slate-200 dark:border-slate-700">
                  {selectedItem.description}
                </p>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                <div className="p-2.5 bg-slate-50 dark:bg-slate-800 rounded border border-slate-200 dark:border-slate-700">
                  <span className="text-slate-400 block">OIL Material Code</span>
                  <span className="font-bold text-slate-800 dark:text-slate-200">{selectedItem.oil_material_code || '—'}</span>
                </div>
                <div className="p-2.5 bg-slate-50 dark:bg-slate-800 rounded border border-slate-200 dark:border-slate-700">
                  <span className="text-slate-400 block">Category</span>
                  <span className="font-bold text-slate-800 dark:text-slate-200">{selectedItem.category}</span>
                </div>
                <div className="p-2.5 bg-slate-50 dark:bg-slate-800 rounded border border-slate-200 dark:border-slate-700">
                  <span className="text-slate-400 block">Metallurgy</span>
                  <span className="font-bold text-slate-800 dark:text-slate-200">{selectedItem.metallurgy || '—'}</span>
                </div>
                <div className="p-2.5 bg-slate-50 dark:bg-slate-800 rounded border border-slate-200 dark:border-slate-700">
                  <span className="text-slate-400 block">Nominal Bore (NB)</span>
                  <span className="font-bold text-slate-800 dark:text-slate-200">{selectedItem.nominal_bore_mm || `${selectedItem.size_nb_mm || ''} mm`}</span>
                </div>
                <div className="p-2.5 bg-slate-50 dark:bg-slate-800 rounded border border-slate-200 dark:border-slate-700">
                  <span className="text-slate-400 block">Pressure Class / Bar</span>
                  <span className="font-bold text-slate-800 dark:text-slate-200">{selectedItem.pressure_rating_bar || selectedItem.pressure_class || '—'}</span>
                </div>
                <div className="p-2.5 bg-slate-50 dark:bg-slate-800 rounded border border-slate-200 dark:border-slate-700">
                  <span className="text-slate-400 block">Quantity</span>
                  <span className="font-bold text-slate-800 dark:text-slate-200">{selectedItem.quantity} {selectedItem.unit}</span>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div className="p-2.5 bg-slate-50 dark:bg-slate-800 rounded border border-slate-200 dark:border-slate-700">
                  <span className="text-slate-400 block">BIS Indian Standard</span>
                  <span className="font-semibold text-slate-800 dark:text-slate-200">{selectedItem.indian_standard || '—'}</span>
                </div>
                <div className="p-2.5 bg-slate-50 dark:bg-slate-800 rounded border border-slate-200 dark:border-slate-700">
                  <span className="text-slate-400 block">OIL / Industry Spec</span>
                  <span className="font-semibold text-slate-800 dark:text-slate-200">{selectedItem.oil_std_spec || selectedItem.standard || '—'}</span>
                </div>
                <div className="p-2.5 bg-slate-50 dark:bg-slate-800 rounded border border-slate-200 dark:border-slate-700">
                  <span className="text-slate-400 block">Make In India (MII) Class</span>
                  <span className="font-semibold text-emerald-700 dark:text-emerald-400">
                    {selectedItem.make_in_india_class || 'Class-I'} ({selectedItem.local_content_percentage ?? 80}%)
                  </span>
                </div>
                <div className="p-2.5 bg-slate-50 dark:bg-slate-800 rounded border border-slate-200 dark:border-slate-700">
                  <span className="text-slate-400 block">CPPP Tender Ref</span>
                  <span className="font-semibold text-slate-800 dark:text-slate-200">{selectedItem.cppp_tender_ref || '—'}</span>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div className="p-2.5 bg-slate-50 dark:bg-slate-800 rounded border border-slate-200 dark:border-slate-700">
                  <span className="text-slate-400 block">Heat Number</span>
                  <span className="font-semibold text-slate-800 dark:text-slate-200">{selectedItem.heat_no || '—'}</span>
                </div>
                <div className="p-2.5 bg-slate-50 dark:bg-slate-800 rounded border border-slate-200 dark:border-slate-700">
                  <span className="text-slate-400 block">Days Idle</span>
                  <span className="font-semibold text-slate-800 dark:text-slate-200">{selectedItem.days_idle} days</span>
                </div>
                <div className="p-2.5 bg-slate-50 dark:bg-slate-800 rounded border border-slate-200 dark:border-slate-700">
                  <span className="text-slate-400 block">Current Status</span>
                  <span className="font-bold text-emerald-700 dark:text-emerald-400">{selectedItem.status}</span>
                </div>
              </div>
            </div>

            <div className="p-4 border-t border-slate-200 dark:border-slate-800 flex items-center justify-between">
              <div className="flex gap-2">
                {selectedItem.status !== 'IDLE_SURPLUS' ? (
                  <button
                    onClick={() => handleUpdateStatus(selectedItem.sku_code, 'IDLE_SURPLUS')}
                    className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded text-xs font-mono font-semibold"
                  >
                    Broadcast as Surplus
                  </button>
                ) : (
                  <button
                    onClick={() => handleUpdateStatus(selectedItem.sku_code, 'TO_BE_CONSUMED')}
                    className="px-3 py-1.5 bg-slate-700 hover:bg-slate-600 text-white rounded text-xs font-mono font-semibold"
                  >
                    Retract Surplus Status
                  </button>
                )}
              </div>
              <button
                onClick={() => setSelectedItem(null)}
                className="px-4 py-1.5 bg-slate-200 dark:bg-slate-800 hover:bg-slate-300 dark:hover:bg-slate-700 text-slate-800 dark:text-slate-200 rounded text-xs font-mono"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
      </div>
    </ProtectedRoute>
  );
}
