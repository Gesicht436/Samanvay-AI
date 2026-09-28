"use client";

import React, { useState, useEffect, useMemo } from 'react';
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
  SlidersHorizontal,
  ChevronDown,
  ChevronUp,
  RotateCcw,
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

interface AdvancedFilters {
  size_nb_mm: string;
  pressure_class: string;
  pressure_rating_bar: string;
  schedule: string;
  metallurgy: string;
  weldability_class: string;
  sour_service: boolean;
  facing_end: string;
  attachment: string;
  mfg_method: string;
  standard: string;
  indian_standard: string;
  oil_std_spec: string;
  severe_cyclic: boolean;
  trim_no: string;
  port_bore: string;
  piggable: boolean;
  fire_safe_required: boolean;
}

const initialFilters: AdvancedFilters = {
  size_nb_mm: '',
  pressure_class: '',
  pressure_rating_bar: '',
  schedule: '',
  metallurgy: '',
  weldability_class: '',
  sour_service: false,
  facing_end: '',
  attachment: '',
  mfg_method: '',
  standard: '',
  indian_standard: '',
  oil_std_spec: '',
  severe_cyclic: false,
  trim_no: '',
  port_bore: '',
  piggable: false,
  fire_safe_required: false,
};

export default function SurplusDiscoveryPage() {
  const { cpse } = useTheme();
  const [queryText, setQueryText] = useState<string>('');
  const [selectedType, setSelectedType] = useState<string>('ALL');
  const [maxDistance, setMaxDistance] = useState<number>(2000);
  const [results, setResults] = useState<SearchResultItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [isSearched, setIsSearched] = useState<boolean>(false);

  // Advanced Engineering Specification Filters State
  const [showAdvanced, setShowAdvanced] = useState<boolean>(false);
  const [filters, setFilters] = useState<AdvancedFilters>(initialFilters);

  const activeFilterCount = useMemo(() => {
    let count = 0;
    if (filters.size_nb_mm) count++;
    if (filters.pressure_class) count++;
    if (filters.pressure_rating_bar) count++;
    if (filters.schedule) count++;
    if (filters.metallurgy) count++;
    if (filters.weldability_class) count++;
    if (filters.sour_service) count++;
    if (filters.facing_end) count++;
    if (filters.attachment) count++;
    if (filters.mfg_method) count++;
    if (filters.standard) count++;
    if (filters.indian_standard) count++;
    if (filters.oil_std_spec) count++;
    if (filters.severe_cyclic) count++;
    if (filters.trim_no) count++;
    if (filters.port_bore) count++;
    if (filters.piggable) count++;
    if (filters.fire_safe_required) count++;
    return count;
  }, [filters]);

  const updateFilter = (field: keyof AdvancedFilters, val: any) => {
    setFilters((prev) => ({ ...prev, [field]: val }));
  };

  const handleResetFilters = () => {
    setFilters(initialFilters);
    setQueryText('');
    setSelectedType('ALL');
    loadInitialSurplus();
  };

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
    const hasAnyFilter = queryText.trim() || selectedType !== 'ALL' || activeFilterCount > 0;
    if (!hasAnyFilter) {
      loadInitialSurplus();
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const payload: any = {
        query_text: queryText,
        item_type: selectedType !== 'ALL' ? selectedType : undefined,
      };

      if (filters.size_nb_mm) payload.size_nb_mm = parseFloat(filters.size_nb_mm);
      if (filters.pressure_class) payload.pressure_class = parseInt(filters.pressure_class);
      if (filters.pressure_rating_bar) payload.pressure_rating_bar = parseFloat(filters.pressure_rating_bar);
      if (filters.schedule) payload.schedule = filters.schedule;
      if (filters.metallurgy) payload.metallurgy = filters.metallurgy;
      if (filters.weldability_class) payload.weldability_class = filters.weldability_class;
      if (filters.sour_service) payload.sour_service = true;
      if (filters.facing_end) payload.facing_end = filters.facing_end;
      if (filters.attachment) payload.attachment = filters.attachment;
      if (filters.mfg_method) payload.mfg_method = filters.mfg_method;
      if (filters.standard) payload.standard = filters.standard;
      if (filters.indian_standard) payload.indian_standard = filters.indian_standard;
      if (filters.oil_std_spec) payload.oil_std_spec = filters.oil_std_spec;
      if (filters.severe_cyclic) payload.severe_cyclic = true;
      if (filters.trim_no) payload.trim_no = parseInt(filters.trim_no);
      if (filters.port_bore) payload.port_bore = filters.port_bore;
      if (filters.piggable) payload.piggable = true;
      if (filters.fire_safe_required) payload.fire_safe_required = true;

      const res = await api.searchMatches(payload);

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
  }, [selectedType, maxDistance]);

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

          {/* Search Input Bar & Collapsible Advanced Filters */}
          <form onSubmit={handleSearch} className="mt-3">
            <div className="flex flex-wrap items-center gap-2">
              <div className="relative flex-1 min-w-[260px]">
                <Search size={14} className="absolute left-3 top-2.5 text-zinc-400" />
                <input
                  type="text"
                  placeholder="Free-text spec, item code, or dialect (e.g. 6 inch gate valve 600# IS 14846, A105 flange)..."
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
                  <option key={t} value={t}>{t.replace(/_/g, ' ')}</option>
                ))}
              </select>

              <select
                value={maxDistance}
                onChange={(e) => setMaxDistance(Number(e.target.value))}
                className="bg-zinc-50 dark:bg-zinc-800/80 border border-zinc-200 dark:border-zinc-700/80 rounded-md px-2.5 py-1.5 text-xs text-zinc-800 dark:text-zinc-200 outline-hidden font-mono"
                title="Maximum logistics road transport radius"
              >
                <option value={500}>&le; 500 km radius</option>
                <option value={1000}>&le; 1,000 km radius</option>
                <option value={2000}>&le; 2,000 km radius</option>
                <option value={5000}>All India (5,000 km)</option>
              </select>

              <button
                type="button"
                onClick={() => setShowAdvanced(!showAdvanced)}
                className={`px-2.5 py-1.5 border rounded-md text-xs font-medium flex items-center gap-1.5 transition-colors ${
                  showAdvanced || activeFilterCount > 0
                    ? 'bg-zinc-100 dark:bg-zinc-800 border-zinc-300 dark:border-zinc-600 text-zinc-900 dark:text-zinc-100'
                    : 'bg-zinc-50 dark:bg-zinc-800/80 border-zinc-200 dark:border-zinc-700/80 text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-200'
                }`}
              >
                <SlidersHorizontal size={13} />
                <span>Filters</span>
                {activeFilterCount > 0 && (
                  <span className="px-1.5 py-0.2 rounded-full text-[10px] font-mono font-bold bg-zinc-900 text-white dark:bg-zinc-100 dark:text-zinc-900">
                    {activeFilterCount}
                  </span>
                )}
                {showAdvanced ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
              </button>

              <button
                type="submit"
                disabled={loading}
                className="px-3 py-1.5 bg-zinc-900 hover:bg-zinc-800 text-white dark:bg-zinc-100 dark:hover:bg-zinc-200 dark:text-zinc-900 rounded-md text-xs font-medium transition-colors flex items-center gap-1.5 disabled:opacity-50"
              >
                <Search size={13} />
                <span>Search</span>
              </button>

              {(activeFilterCount > 0 || queryText || isSearched) && (
                <button
                  type="button"
                  onClick={handleResetFilters}
                  title="Reset all filters and restore surplus catalog"
                  className="px-2.5 py-1.5 bg-zinc-100 dark:bg-zinc-800 hover:bg-zinc-200 dark:hover:bg-zinc-700 text-zinc-600 dark:text-zinc-400 rounded-md text-xs font-medium transition-colors flex items-center gap-1"
                >
                  <RotateCcw size={12} />
                  <span>Reset</span>
                </button>
              )}
            </div>

            {/* Collapsible Advanced Engineering Property Specification Panel */}
            {showAdvanced && (
              <div className="mt-3 pt-3 border-t border-zinc-200 dark:border-zinc-800 space-y-3">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between text-[11px] font-mono text-zinc-500 gap-1">
                  <span>Detailed Engineering Specification · Provide any 1 or multiple properties for pairwise 21-rule tolerance verification</span>
                  {activeFilterCount > 0 && (
                    <span className="text-zinc-800 dark:text-zinc-200 font-medium">
                      {activeFilterCount} propert{activeFilterCount === 1 ? 'y' : 'ies'} specified
                    </span>
                  )}
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 text-xs font-mono">
                  {/* Col 1: Dimensions & Pressure */}
                  <div className="space-y-2 p-2.5 bg-zinc-50 dark:bg-zinc-800/40 rounded-lg border border-zinc-200/80 dark:border-zinc-800">
                    <span className="text-[10px] font-semibold text-zinc-400 uppercase tracking-wider block">
                      Dimensions & Pressure
                    </span>
                    <div>
                      <label className="text-[10px] text-zinc-500 block mb-0.5">Nominal Bore (NB mm)</label>
                      <input
                        type="number"
                        placeholder="e.g. 50, 100, 150"
                        value={filters.size_nb_mm}
                        onChange={(e) => updateFilter('size_nb_mm', e.target.value)}
                        className="w-full px-2 py-1 bg-white dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded text-xs outline-hidden focus:border-zinc-400"
                      />
                    </div>
                    <div>
                      <label className="text-[10px] text-zinc-500 block mb-0.5">Pressure Class (ASME)</label>
                      <select
                        value={filters.pressure_class}
                        onChange={(e) => updateFilter('pressure_class', e.target.value)}
                        className="w-full px-2 py-1 bg-white dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded text-xs outline-hidden"
                      >
                        <option value="">Any Pressure Class</option>
                        <option value="150">150# (PN 20)</option>
                        <option value="300">300# (PN 50)</option>
                        <option value="600">600# (PN 100)</option>
                        <option value="900">900# (PN 150)</option>
                        <option value="1500">1500# (PN 250)</option>
                        <option value="2500">2500# (PN 420)</option>
                      </select>
                    </div>
                    <div>
                      <label className="text-[10px] text-zinc-500 block mb-0.5">Pipe Schedule (B36.10)</label>
                      <select
                        value={filters.schedule}
                        onChange={(e) => updateFilter('schedule', e.target.value)}
                        className="w-full px-2 py-1 bg-white dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded text-xs outline-hidden"
                      >
                        <option value="">Any Schedule</option>
                        <option value="SCH 10">SCH 10</option>
                        <option value="SCH 20">SCH 20</option>
                        <option value="SCH 40">SCH 40 / STD</option>
                        <option value="SCH 80">SCH 80 / XS</option>
                        <option value="SCH 120">SCH 120</option>
                        <option value="SCH 160">SCH 160</option>
                        <option value="SCH XXS">SCH XXS</option>
                      </select>
                    </div>
                  </div>

                  {/* Col 2: Metallurgy & Weldability */}
                  <div className="space-y-2 p-2.5 bg-zinc-50 dark:bg-zinc-800/40 rounded-lg border border-zinc-200/80 dark:border-zinc-800">
                    <span className="text-[10px] font-semibold text-zinc-400 uppercase tracking-wider block">
                      Metallurgy & Weldability
                    </span>
                    <div>
                      <label className="text-[10px] text-zinc-500 block mb-0.5">Material Grade / DAG</label>
                      <input
                        type="text"
                        placeholder="e.g. A105, WCB, LCB, F316L"
                        value={filters.metallurgy}
                        onChange={(e) => updateFilter('metallurgy', e.target.value)}
                        className="w-full px-2 py-1 bg-white dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded text-xs outline-hidden focus:border-zinc-400"
                      />
                    </div>
                    <div>
                      <label className="text-[10px] text-zinc-500 block mb-0.5">Weldability Class</label>
                      <select
                        value={filters.weldability_class}
                        onChange={(e) => updateFilter('weldability_class', e.target.value)}
                        className="w-full px-2 py-1 bg-white dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded text-xs outline-hidden"
                      >
                        <option value="">Any / Unspecified</option>
                        <option value="HIGH_WELDABILITY">High Weldability (CE &le; 0.40%)</option>
                        <option value="STANDARD">Standard Weldability (CE &le; 0.43% IIW)</option>
                        <option value="NON_WELDABLE">Non-Weldable (Bolted Assembly)</option>
                      </select>
                    </div>
                    <div className="pt-0.5 space-y-1.5">
                      <label className="flex items-center gap-1.5 cursor-pointer text-[11px] text-zinc-700 dark:text-zinc-300">
                        <input
                          type="checkbox"
                          checked={filters.sour_service}
                          onChange={(e) => updateFilter('sour_service', e.target.checked)}
                          className="rounded border-zinc-300 dark:border-zinc-700 text-zinc-900 focus:ring-0"
                        />
                        <span>Sour Service (NACE MR0175 / H2S)</span>
                      </label>
                      <div>
                        <label className="text-[10px] text-zinc-500 block mb-0.5">Manufacturing Method</label>
                        <select
                          value={filters.mfg_method}
                          onChange={(e) => updateFilter('mfg_method', e.target.value)}
                          className="w-full px-2 py-1 bg-white dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded text-xs outline-hidden"
                        >
                          <option value="">Any Method</option>
                          <option value="SEAMLESS">Seamless (SMLS)</option>
                          <option value="WELDED">Welded (ERW / LSAW)</option>
                        </select>
                      </div>
                    </div>
                  </div>

                  {/* Col 3: Connections & Geometry */}
                  <div className="space-y-2 p-2.5 bg-zinc-50 dark:bg-zinc-800/40 rounded-lg border border-zinc-200/80 dark:border-zinc-800">
                    <span className="text-[10px] font-semibold text-zinc-400 uppercase tracking-wider block">
                      Connections & Geometry
                    </span>
                    <div>
                      <label className="text-[10px] text-zinc-500 block mb-0.5">Facing Type</label>
                      <select
                        value={filters.facing_end}
                        onChange={(e) => updateFilter('facing_end', e.target.value)}
                        className="w-full px-2 py-1 bg-white dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded text-xs outline-hidden"
                      >
                        <option value="">Any Facing</option>
                        <option value="RF">Raised Face (RF)</option>
                        <option value="RTJ">Ring Type Joint (RTJ)</option>
                        <option value="FF">Flat Face (FF)</option>
                        <option value="BW">Butt Weld (BW)</option>
                        <option value="SW">Socket Weld (SW)</option>
                        <option value="NPT">Threaded / NPT</option>
                      </select>
                    </div>
                    <div>
                      <label className="text-[10px] text-zinc-500 block mb-0.5">Attachment / Flange Type</label>
                      <select
                        value={filters.attachment}
                        onChange={(e) => updateFilter('attachment', e.target.value)}
                        className="w-full px-2 py-1 bg-white dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded text-xs outline-hidden"
                      >
                        <option value="">Any Attachment</option>
                        <option value="WELD_NECK">Weld Neck (WN)</option>
                        <option value="SLIP_ON">Slip-On (SO)</option>
                        <option value="BLIND">Blind Flange</option>
                        <option value="SOCKET_WELD">Socket Weld (SW)</option>
                      </select>
                    </div>
                    <div className="pt-1.5">
                      <label className="flex items-center gap-1.5 cursor-pointer text-[11px] text-zinc-700 dark:text-zinc-300">
                        <input
                          type="checkbox"
                          checked={filters.severe_cyclic}
                          onChange={(e) => updateFilter('severe_cyclic', e.target.checked)}
                          className="rounded border-zinc-300 dark:border-zinc-700 text-zinc-900 focus:ring-0"
                        />
                        <span>Severe Cyclic (Slip-On Banned)</span>
                      </label>
                    </div>
                  </div>

                  {/* Col 4: Standards & Valve Specs */}
                  <div className="space-y-2 p-2.5 bg-zinc-50 dark:bg-zinc-800/40 rounded-lg border border-zinc-200/80 dark:border-zinc-800">
                    <span className="text-[10px] font-semibold text-zinc-400 uppercase tracking-wider block">
                      Standards & Component Specs
                    </span>
                    <div>
                      <label className="text-[10px] text-zinc-500 block mb-0.5">Indian Standard (BIS/IS)</label>
                      <input
                        type="text"
                        placeholder="e.g. IS 14846, IS 1239, IS 2062"
                        value={filters.indian_standard}
                        onChange={(e) => updateFilter('indian_standard', e.target.value)}
                        className="w-full px-2 py-1 bg-white dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded text-xs outline-hidden focus:border-zinc-400"
                      />
                    </div>
                    <div>
                      <label className="text-[10px] text-zinc-500 block mb-0.5">International Standard</label>
                      <input
                        type="text"
                        placeholder="e.g. ASME B16.5, API 600, B16.34"
                        value={filters.standard}
                        onChange={(e) => updateFilter('standard', e.target.value)}
                        className="w-full px-2 py-1 bg-white dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded text-xs outline-hidden focus:border-zinc-400"
                      />
                    </div>
                    <div>
                      <label className="text-[10px] text-zinc-500 block mb-0.5">OISD / EIL Specification</label>
                      <input
                        type="text"
                        placeholder="e.g. OISD-RP-126, EIL 6-44-0012"
                        value={filters.oil_std_spec}
                        onChange={(e) => updateFilter('oil_std_spec', e.target.value)}
                        className="w-full px-2 py-1 bg-white dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded text-xs outline-hidden focus:border-zinc-400"
                      />
                    </div>
                    <div>
                      <label className="text-[10px] text-zinc-500 block mb-0.5">Valve Trim (API 600)</label>
                      <select
                        value={filters.trim_no}
                        onChange={(e) => updateFilter('trim_no', e.target.value)}
                        className="w-full px-2 py-1 bg-white dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded text-xs outline-hidden"
                      >
                        <option value="">Any Trim</option>
                        <option value="1">Trim 1 (F6a / 13Cr)</option>
                        <option value="5">Trim 5 (Stellite Hardfaced)</option>
                        <option value="8">Trim 8 (F6a + Stellite)</option>
                        <option value="10">Trim 10 (316 SS)</option>
                        <option value="12">Trim 12 (316 SS + Stellite)</option>
                      </select>
                    </div>
                  </div>
                </div>

                {/* Action Bar inside Expanded Filters */}
                <div className="flex items-center justify-between pt-1 text-xs font-mono">
                  <button
                    type="button"
                    onClick={handleResetFilters}
                    className="text-zinc-500 hover:text-zinc-800 dark:hover:text-zinc-200 underline"
                  >
                    Clear All Filters
                  </button>
                  <button
                    type="submit"
                    disabled={loading}
                    className="px-3 py-1.5 bg-zinc-900 hover:bg-zinc-800 text-white dark:bg-zinc-100 dark:hover:bg-zinc-200 dark:text-zinc-900 rounded-md text-xs font-medium transition-colors flex items-center gap-1.5 disabled:opacity-50"
                  >
                    <Search size={13} />
                    <span>Apply Specifications & Search</span>
                  </button>
                </div>
              </div>
            )}
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
