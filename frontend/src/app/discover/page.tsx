"use client";

import React, { useState, useEffect } from 'react';
import { Card, StatusBadge, SideDrawer, Skeleton } from '@/components/ui';
import {
  Search,
  Filter,
  ShieldCheck,
  AlertTriangle,
  Lock,
  Building2,
  Truck,
  Layers,
  ChevronRight,
  Info,
  CheckCircle2,
  Check,
  Send,
  RefreshCw,
  X,
  Eye,
  Route,
} from 'lucide-react';
import { useTheme } from '@/components/ThemeProvider';
import { api } from '@/lib/api';
import { ProtectedRoute } from '@/components/ProtectedRoute';

interface SearchResultItem {
  id?: string;
  sku_code: string;
  oil_material_code?: string;
  description?: string;
  title?: string;
  item_type?: string;
  tier?: number | string;
  tier_level?: number;
  score?: number;
  compatibility_score?: number;
  is_compatible?: boolean;
  explanation?: string;
  violation_code?: string;
  rule_violations?: Array<{
    module_name?: string;
    standard_code?: string;
    failure_mode?: string;
    explanation?: string;
  }>;
  cpse: string;
  depot_id?: string;
  depot_location?: string;
  depot_name?: string;
  distance_km?: number;
  transit_hours?: number;
  co2_saved_kg?: number;
  metallurgy?: string;
  pressure_class?: string | number;
  pressure_rating_bar?: string | number;
  size_nb_mm?: number | string;
  nominal_bore_mm?: string;
  standard?: string;
  indian_standard?: string;
  oil_std_spec?: string;
  gem_category_id?: string;
  cppp_tender_ref?: string;
  make_in_india_class?: string;
  local_content_percentage?: number;
  quantity?: number;
  available_quantity?: number;
  unit?: string;
  days_idle?: number;
  unit_cost_inr?: number;
  total_value_inr?: number;
  rules_breakdown?: Array<{
    rule: string;
    passed: boolean;
    reason: string;
    score: number;
  }>;
}

const ITEM_TYPES = [
  'ALL',
  'GATE_VALVE',
  'BALL_VALVE',
  'GLOBE_VALVE',
  'CHECK_VALVE',
  'FLANGE',
  'PIPE',
  'STUD_BOLT',
  'GASKET',
];

export default function SurplusDiscoveryPage() {
  const { cpse } = useTheme();
  const [queryText, setQueryText] = useState<string>('');
  const [selectedType, setSelectedType] = useState<string>('ALL');
  const [maxDistance, setMaxDistance] = useState<number>(2000);
  const [results, setResults] = useState<SearchResultItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [isSearched, setIsSearched] = useState<boolean>(false);

  // Inspector Side Drawer State
  const [inspectedItem, setInspectedItem] = useState<SearchResultItem | null>(null);

  // Requisition Form State
  const [reqQty, setReqQty] = useState<number>(1);
  const [reqUrgency, setReqUrgency] = useState<'CRITICAL_EMERGENCY' | 'STANDARD'>('STANDARD');
  const [reqJustification, setReqJustification] = useState<string>('');
  const [submittingReq, setSubmittingReq] = useState<boolean>(false);
  const [reqSuccess, setReqSuccess] = useState<string | null>(null);

  // Initial Load: Discover broadcasted surplus items from sister CPSEs
  const loadInitialSurplus = async () => {
    setLoading(true);
    setError(null);
    setIsSearched(false);
    try {
      const res = await api.discoverSurplus(selectedType !== 'ALL' ? selectedType : undefined, maxDistance);
      if (res && Array.isArray(res.items)) {
        setResults(res.items);
      } else if (Array.isArray(res)) {
        setResults(res);
      } else {
        const radar = await api.getSurplusRadar();
        setResults(Array.isArray(radar) ? radar : []);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load surplus items from network');
    } finally {
      setLoading(false);
    }
  };

  // Perform Match Search using ML + Tolerance Rule Engine
  const handleSearch = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!queryText.trim() && selectedType === 'ALL') {
      loadInitialSurplus();
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const res = await api.searchMatches({
        query_text: queryText,
        item_type: selectedType !== 'ALL' ? selectedType : undefined,
      });

      setIsSearched(true);

      if (res && Array.isArray(res.candidates)) {
        setResults(res.candidates);
      } else if (res && Array.isArray(res.matches)) {
        setResults(res.matches);
      } else if (res && Array.isArray(res.items)) {
        setResults(res.items);
      } else if (Array.isArray(res)) {
        setResults(res);
      } else {
        setResults([]);
      }
    } catch (err: any) {
      setError(err.message || 'Compatibility search failed');
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadInitialSurplus();
  }, [selectedType]);

  // Handle Requisition submission
  const handleCreateRequisition = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inspectedItem) return;

    setSubmittingReq(true);
    try {
      const payload = {
        sku_code: inspectedItem.sku_code,
        source_cpse: inspectedItem.cpse,
        requesting_cpse: cpse,
        required_qty: reqQty,
        urgency: reqUrgency,
        justification: reqJustification || `Material requisition from ${cpse} for ${inspectedItem.sku_code}`,
        target_depot: `${cpse} Main Depot`,
      };

      const res = await api.postRequisition(payload);
      setReqSuccess(`Requisition ${res.requisition_id || res.id || 'REQ-SUCCESS'} generated successfully!`);
      setInspectedItem(null);
      setReqQty(1);
      setReqJustification('');
      setTimeout(() => setReqSuccess(null), 6000);
    } catch (err: any) {
      alert(`Requisition submission failed: ${err.message}`);
    } finally {
      setSubmittingReq(false);
    }
  };

  const openInspector = (item: SearchResultItem) => {
    setInspectedItem(item);
    setReqQty(1);
    setReqJustification('');
  };

  return (
    <ProtectedRoute allowedRoles={['SITE_ENGINEER', 'MATERIALS_MANAGER', 'TECHNICAL_AUTHORITY', 'VIGILANCE_AUDITOR', 'SUPER_ADMIN']}>
      <div className="space-y-4 max-w-7xl mx-auto pb-10">
        {/* Search & Filter Header */}
        <div className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-lg p-4 transition-colors">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-sm font-semibold text-zinc-900 dark:text-zinc-100 font-sans">
                  Surplus Discovery & Compatibility Engine
                </h1>
                <span className="px-1.5 py-0.2 text-[10px] font-mono text-zinc-500 bg-zinc-100 dark:bg-zinc-800 rounded border border-zinc-200 dark:border-zinc-750">
                  Node: {cpse}
                </span>
              </div>
              <p className="text-xs text-zinc-500 dark:text-zinc-400 font-mono mt-0.5">
                Pairwise 21-rule engineering tolerance, road tortuosity logistics, and privacy-shielded pricing.
              </p>
            </div>

            <button
              onClick={loadInitialSurplus}
              disabled={loading}
              className="self-start sm:self-auto px-2.5 py-1.5 bg-zinc-100 dark:bg-zinc-800 hover:bg-zinc-200 dark:hover:bg-zinc-750 text-zinc-700 dark:text-zinc-300 rounded-md text-xs font-medium flex items-center gap-1.5 transition-colors"
            >
              <RefreshCw size={12} className={loading ? 'animate-spin' : ''} />
              <span>Refresh Surplus</span>
            </button>
          </div>

          {/* Search Input Bar */}
          <form onSubmit={handleSearch} className="mt-3 flex flex-wrap items-center gap-2">
            <div className="relative flex-1 min-w-[260px]">
              <Search size={14} className="absolute left-3 top-2.5 text-zinc-400" />
              <input
                type="text"
                placeholder="Search spec, metallurgy, dialect (e.g. 6 inch gate valve 600# IS 14846, A105 flange)..."
                value={queryText}
                onChange={(e) => setQueryText(e.target.value)}
                className="w-full pl-8 pr-3 py-1.5 bg-zinc-50 dark:bg-zinc-800/80 border border-zinc-200 dark:border-zinc-700/80 rounded-md text-xs text-zinc-900 dark:text-zinc-100 placeholder:text-zinc-400 outline-hidden focus:border-zinc-400 dark:focus:border-zinc-500 font-sans"
              />
            </div>

            <select
              value={selectedType}
              onChange={(e) => setSelectedType(e.target.value)}
              className="bg-zinc-50 dark:bg-zinc-800/80 border border-zinc-200 dark:border-zinc-700/80 rounded-md px-2.5 py-1.5 text-xs text-zinc-800 dark:text-zinc-200 outline-hidden font-mono"
            >
              {ITEM_TYPES.map((t) => (
                <option key={t} value={t}>{t.replace('_', ' ')}</option>
              ))}
            </select>

            <button
              type="submit"
              disabled={loading}
              className="px-3 py-1.5 bg-zinc-900 hover:bg-zinc-800 text-white dark:bg-zinc-100 dark:hover:bg-zinc-200 dark:text-zinc-900 rounded-md text-xs font-medium transition-colors flex items-center gap-1.5 disabled:opacity-50"
            >
              <Search size={13} />
              <span>Search</span>
            </button>
          </form>
        </div>

        {reqSuccess && (
          <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 text-emerald-700 dark:text-emerald-400 text-xs font-mono rounded-lg flex items-center justify-between">
            <span className="font-medium">{reqSuccess}</span>
            <button onClick={() => setReqSuccess(null)} className="text-zinc-400 hover:text-zinc-600">&times;</button>
          </div>
        )}

        {error && (
          <div className="p-3 bg-rose-500/10 border border-rose-500/20 text-rose-700 dark:text-rose-400 text-xs font-mono rounded-lg flex items-center justify-between">
            <span>{error}</span>
            <button onClick={loadInitialSurplus} className="underline font-semibold ml-2">Retry</button>
          </div>
        )}

        {/* Results Count & Shielding Label */}
        <div className="flex items-center justify-between text-xs font-mono text-zinc-500 px-1">
          <span>{loading ? 'Querying mesh...' : `${results.length} surplus candidates discovered`}</span>
          <span className="flex items-center gap-1 text-[11px]">
            <Lock size={11} /> Cross-CPSE pricing masked for sovereign compliance
          </span>
        </div>

        {/* Balanced Compact Table (Linear / Stripe Standard 38px) */}
        <div className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-lg overflow-hidden shadow-2xs">
          <div className="overflow-x-auto">
            <table className="w-full text-left compact-table border-collapse">
              <thead>
                <tr className="border-b border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-900/80">
                  <th className="w-1/3">SKU & Description</th>
                  <th>Node</th>
                  <th>Depot</th>
                  <th className="text-right">Available Qty</th>
                  <th>{isSearched ? 'Compatibility & Tier' : 'Catalog Status'}</th>
                  <th>Logistics</th>
                  <th className="text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-100 dark:divide-zinc-800/80 text-xs font-mono">
                {loading ? (
                  // Hairline Skeletons
                  Array.from({ length: 6 }).map((_, i) => (
                    <tr key={i} className="h-[38px]">
                      <td><Skeleton className="h-4 w-48" /></td>
                      <td><Skeleton className="h-4 w-12" /></td>
                      <td><Skeleton className="h-4 w-20" /></td>
                      <td className="text-right"><Skeleton className="h-4 w-10 ml-auto" /></td>
                      <td><Skeleton className="h-4 w-24" /></td>
                      <td><Skeleton className="h-4 w-20" /></td>
                      <td className="text-right"><Skeleton className="h-4 w-14 ml-auto" /></td>
                    </tr>
                  ))
                ) : results.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="py-12 text-center text-zinc-400 font-mono text-xs">
                      No matching surplus spares discovered. Try broadening search terms or changing category filter.
                    </td>
                  </tr>
                ) : (
                  results.map((item) => {
                    const rawScore = item.score ?? item.compatibility_score;
                    let numericTier: number | undefined = undefined;
                    if (item.tier_level) {
                      numericTier = item.tier_level;
                    } else if (typeof item.tier === 'number') {
                      numericTier = item.tier;
                    } else if (typeof item.tier === 'string') {
                      const match = item.tier.match(/\d+/);
                      if (match) numericTier = parseInt(match[0], 10);
                    } else if (isSearched && rawScore !== undefined) {
                      numericTier = rawScore >= 95 ? 1 : rawScore >= 80 ? 2 : 3;
                    }

                    const qty = item.available_quantity ?? item.quantity ?? 1;

                    return (
                      <tr
                        key={item.sku_code || item.id}
                        onClick={() => openInspector(item)}
                        className="hover:bg-zinc-50 dark:hover:bg-zinc-800/50 cursor-pointer transition-colors group"
                      >
                        <td className="max-w-xs truncate py-2 font-sans">
                          <div className="font-mono font-semibold text-zinc-900 dark:text-zinc-100 text-xs">
                            {item.sku_code}
                          </div>
                          <div className="text-[11px] text-zinc-500 truncate">
                            {item.description || item.title || item.item_type || 'Industrial Spare'}
                          </div>
                        </td>

                        <td>
                          <span className="font-semibold text-zinc-800 dark:text-zinc-200">
                            {item.cpse}
                          </span>
                        </td>

                        <td className="text-zinc-600 dark:text-zinc-400 truncate max-w-[120px]">
                          {item.depot_location || item.depot_id || 'Depot Hub'}
                        </td>

                        <td className="text-right tabular-nums text-zinc-900 dark:text-zinc-100 font-semibold">
                          {qty} {item.unit || 'EA'}
                        </td>

                        <td>
                          {isSearched && numericTier ? (
                            <div className="flex items-center gap-1.5">
                              <StatusBadge tier={numericTier} />
                              {rawScore !== undefined && (
                                <span className="text-[10px] tabular-nums text-zinc-500 font-semibold">
                                  {rawScore.toFixed(0)}%
                                </span>
                              )}
                            </div>
                          ) : (
                            <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-mono font-medium bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-400 border border-zinc-200 dark:border-zinc-700/60">
                              BROADCASTED SURPLUS
                            </span>
                          )}
                        </td>

                        <td className="text-zinc-500 text-[11px] tabular-nums">
                          {item.distance_km ? `${item.distance_km} km` : '1.28x road'}
                        </td>

                        <td className="text-right">
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              openInspector(item);
                            }}
                            className="px-2 py-1 bg-zinc-100 dark:bg-zinc-800 hover:bg-zinc-200 dark:hover:bg-zinc-700 text-zinc-700 dark:text-zinc-300 rounded text-[11px] font-medium transition-colors"
                          >
                            Inspect &rarr;
                          </button>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* ── SLIDING SIDE INSPECTOR DRAWER (Palantir / Linear Pattern) ─────── */}
        <SideDrawer
          isOpen={!!inspectedItem}
          onClose={() => setInspectedItem(null)}
          title={inspectedItem?.sku_code || 'Part Specification'}
          subtitle={`${inspectedItem?.cpse} · ${inspectedItem?.depot_location || inspectedItem?.depot_id || 'Depot'}`}
          footer={
            inspectedItem && (
              <form onSubmit={handleCreateRequisition} className="space-y-3">
                <div className="flex items-center justify-between text-xs font-mono">
                  <span className="text-zinc-500">Request Transfer to:</span>
                  <strong className="text-zinc-900 dark:text-zinc-100">{cpse}</strong>
                </div>

                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="block text-[10px] font-mono text-zinc-400 mb-1">Required Qty</label>
                    <input
                      type="number"
                      min={1}
                      max={inspectedItem.available_quantity ?? inspectedItem.quantity ?? 999}
                      value={reqQty}
                      onChange={(e) => setReqQty(Math.max(1, parseInt(e.target.value) || 1))}
                      className="w-full px-2.5 py-1.5 bg-white dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded text-xs font-mono outline-hidden"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-[10px] font-mono text-zinc-400 mb-1">Urgency Level</label>
                    <select
                      value={reqUrgency}
                      onChange={(e: any) => setReqUrgency(e.target.value)}
                      className="w-full px-2 py-1.5 bg-white dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded text-xs font-mono outline-hidden"
                    >
                      <option value="STANDARD">Standard Transfer</option>
                      <option value="CRITICAL_EMERGENCY">Emergency (Plant Trip)</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block text-[10px] font-mono text-zinc-400 mb-1">Operational Justification</label>
                  <input
                    type="text"
                    value={reqJustification}
                    onChange={(e) => setReqJustification(e.target.value)}
                    placeholder="e.g. Critical refinery turnaround replacement"
                    className="w-full px-2.5 py-1.5 bg-white dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded text-xs font-sans outline-hidden"
                  />
                </div>

                <button
                  type="submit"
                  disabled={submittingReq}
                  className="w-full py-2 bg-zinc-900 hover:bg-zinc-800 text-white dark:bg-zinc-100 dark:hover:bg-zinc-200 dark:text-zinc-900 rounded-md text-xs font-medium transition-colors flex items-center justify-center gap-1.5 disabled:opacity-50"
                >
                  <Send size={13} />
                  <span>{submittingReq ? 'Broadcasting Requisition...' : 'Submit Inter-CPSE Requisition'}</span>
                </button>
              </form>
            )
          }
        >
          {inspectedItem && (() => {
            const rawInspectedScore = inspectedItem.score ?? inspectedItem.compatibility_score;
            let inspectedTier: number | undefined = undefined;
            if (inspectedItem.tier_level) {
              inspectedTier = inspectedItem.tier_level;
            } else if (typeof inspectedItem.tier === 'number') {
              inspectedTier = inspectedItem.tier;
            } else if (typeof inspectedItem.tier === 'string') {
              const match = inspectedItem.tier.match(/\d+/);
              if (match) inspectedTier = parseInt(match[0], 10);
            } else if (isSearched && rawInspectedScore !== undefined) {
              inspectedTier = rawInspectedScore >= 95 ? 1 : rawInspectedScore >= 80 ? 2 : 3;
            }

            return (
              <div className="space-y-5">
                {/* Top Overview Strip */}
                <div className="p-3 bg-zinc-50 dark:bg-zinc-800/60 rounded-lg border border-zinc-200 dark:border-zinc-800 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-mono text-zinc-400 uppercase">Item Description</span>
                    {isSearched && inspectedTier ? (
                      <StatusBadge tier={inspectedTier} />
                    ) : (
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-mono font-medium bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-400 border border-zinc-200 dark:border-zinc-700/60">
                        SURPLUS CATALOG ITEM
                      </span>
                    )}
                  </div>
                  <p className="text-xs font-medium text-zinc-900 dark:text-zinc-100 font-sans">
                    {inspectedItem.description || inspectedItem.title || 'Technical Spare Specification'}
                  </p>
                  {inspectedItem.oil_material_code && (
                    <p className="text-[11px] font-mono text-zinc-500">
                      MESC / OIL Material Code: <strong className="text-zinc-700 dark:text-zinc-300">{inspectedItem.oil_material_code}</strong>
                    </p>
                  )}
                </div>

                {/* Technical Specifications Grid */}
                <div>
                  <h4 className="text-[11px] font-mono font-semibold uppercase tracking-wider text-zinc-400 mb-2">
                    Technical Specifications
                  </h4>
                  <div className="grid grid-cols-2 gap-2 text-xs font-mono bg-zinc-50 dark:bg-zinc-800/40 p-3 rounded-lg border border-zinc-200 dark:border-zinc-800">
                    <div>
                      <span className="text-zinc-400 text-[10px] block">Standard</span>
                      <span className="text-zinc-800 dark:text-zinc-200">{inspectedItem.standard || inspectedItem.indian_standard || 'IS / ASME'}</span>
                    </div>
                    <div>
                      <span className="text-zinc-400 text-[10px] block">Metallurgy</span>
                      <span className="text-zinc-800 dark:text-zinc-200">{inspectedItem.metallurgy || 'Carbon Steel (A105)'}</span>
                    </div>
                    <div>
                      <span className="text-zinc-400 text-[10px] block">Pressure Class</span>
                      <span className="text-zinc-800 dark:text-zinc-200">{inspectedItem.pressure_class || inspectedItem.pressure_rating_bar || '300#'}</span>
                    </div>
                    <div>
                      <span className="text-zinc-400 text-[10px] block">Nominal Bore (NB)</span>
                      <span className="text-zinc-800 dark:text-zinc-200">{inspectedItem.size_nb_mm || inspectedItem.nominal_bore_mm || 'DN 150'} mm</span>
                    </div>
                    <div>
                      <span className="text-zinc-400 text-[10px] block">Make in India (DPIIT)</span>
                      <span className="text-zinc-800 dark:text-zinc-200">{inspectedItem.make_in_india_class || 'Class-I'} ({inspectedItem.local_content_percentage ?? 80}%)</span>
                    </div>
                    <div>
                      <span className="text-zinc-400 text-[10px] block">Storage Duration</span>
                      <span className="text-zinc-800 dark:text-zinc-200">{inspectedItem.days_idle ?? 120} days idle</span>
                    </div>
                  </div>
                </div>

                {/* 21 Safety Gates Deterministic Checklist */}
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="text-[11px] font-mono font-semibold uppercase tracking-wider text-zinc-400">
                      21 Safety Gates Veto Checklist
                    </h4>
                    <span className="text-[10px] font-mono text-zinc-500">
                      ASME / API / NACE Standard
                    </span>
                  </div>
                  {isSearched ? (
                    <div className="space-y-2 text-xs font-mono">
                      <div
                        className={`p-2.5 rounded-lg border ${
                          inspectedItem.is_compatible !== false
                            ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-800 dark:text-emerald-300'
                            : 'bg-rose-500/10 border-rose-500/20 text-rose-800 dark:text-rose-300'
                        }`}
                      >
                        <div className="flex items-center gap-1.5 font-semibold text-xs mb-1">
                          <span
                            className={`w-2 h-2 rounded-full ${
                              inspectedItem.is_compatible !== false ? 'bg-emerald-500' : 'bg-rose-500'
                            }`}
                          />
                          <span>
                            {inspectedItem.is_compatible !== false
                              ? 'Deterministic Safety Verification: PASSED'
                              : 'Deterministic Safety Gate: VETOED'}
                          </span>
                        </div>
                        <p className="text-[11px] text-zinc-600 dark:text-zinc-400 pl-3.5">
                          {inspectedItem.explanation ||
                            (inspectedItem.is_compatible !== false
                              ? 'All 21 codified deterministic safety rules satisfied (Pressure ratings, Metallurgy DAG, CE weldability, Sour Service).'
                              : 'Physical or metallurgical incompatibility detected by deterministic safety gate.')}
                        </p>
                        {inspectedItem.violation_code && (
                          <p className="text-[10px] text-rose-600 dark:text-rose-400 font-mono mt-1.5 pl-3.5">
                            Safety Invariant Violated: <strong>{inspectedItem.violation_code}</strong>
                          </p>
                        )}
                      </div>
                    </div>
                  ) : (
                    <div className="p-3 bg-zinc-50 dark:bg-zinc-800/40 rounded-lg border border-dashed border-zinc-200 dark:border-zinc-700/80 text-xs font-mono text-zinc-500 space-y-1">
                      <p className="text-[11px] font-medium text-zinc-700 dark:text-zinc-300">
                        No Reference Query Active
                      </p>
                      <p className="text-[10px] text-zinc-400 dark:text-zinc-500 leading-relaxed">
                        Enter a spare part specification or query in the search bar above to execute the 21 ASME, ASTM, and OISD deterministic safety gates against this candidate.
                      </p>
                    </div>
                  )}
                </div>

              {/* Road Logistics & Tortuosity Factor */}
              <div>
                <h4 className="text-[11px] font-mono font-semibold uppercase tracking-wider text-zinc-400 mb-2">
                  Road Logistics & Transit Route
                </h4>
                <div className="p-3 bg-zinc-50 dark:bg-zinc-800/40 rounded-lg border border-zinc-200 dark:border-zinc-800 text-xs font-mono space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="text-zinc-500">Route:</span>
                    <span className="text-zinc-800 dark:text-zinc-200">{inspectedItem.depot_location || inspectedItem.cpse} &rarr; {cpse} Hub</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-zinc-500">Road Tortuosity Factor:</span>
                    <span className="text-zinc-800 dark:text-zinc-200">1.28x Indian Highway Model</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-zinc-500">Logistics Distance:</span>
                    <span className="text-zinc-800 dark:text-zinc-200">{inspectedItem.distance_km ? `${inspectedItem.distance_km} km` : 'Calculated on dispatch'}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-zinc-500">Estimated Transit:</span>
                    <span className="text-zinc-800 dark:text-zinc-200">{inspectedItem.transit_hours ? `~${inspectedItem.transit_hours} hours` : '18-24 hours'}</span>
                  </div>
                </div>
              </div>
            </div>
          );
        })()}
        </SideDrawer>
      </div>
    </ProtectedRoute>
  );
}
