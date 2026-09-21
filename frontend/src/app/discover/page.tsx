"use client";

import React, { useState, useEffect } from 'react';
import { Card, StatusBadge } from '@/components/ui';
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
} from 'lucide-react';
import { useTheme } from '@/components/ThemeProvider';
import { api } from '@/lib/api';

interface SearchResultItem {
  id?: string;
  sku_code: string;
  oil_material_code?: string;
  description?: string;
  title?: string;
  item_type?: string;
  tier?: number;
  score?: number;
  compatibility_score?: number;
  cpse: string;
  depot_id?: string;
  depot_location?: string;
  depot_name?: string;
  distance_km?: number;
  transit_hours?: number;
  co2_saved_kg?: number;
  metallurgy?: string;
  pressure_class?: string;
  pressure_rating_bar?: string;
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

  // Requisition Modal State
  const [selectedForReq, setSelectedForReq] = useState<SearchResultItem | null>(null);
  const [reqQty, setReqQty] = useState<number>(1);
  const [reqUrgency, setReqUrgency] = useState<'CRITICAL_EMERGENCY' | 'STANDARD'>('STANDARD');
  const [reqJustification, setReqJustification] = useState<string>('');
  const [submittingReq, setSubmittingReq] = useState<boolean>(false);
  const [reqSuccess, setReqSuccess] = useState<string | null>(null);

  // Initial Load: Discover broadcasted surplus items from sister CPSEs
  const loadInitialSurplus = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.discoverSurplus(selectedType !== 'ALL' ? selectedType : undefined, maxDistance);
      if (res && Array.isArray(res.items)) {
        setResults(res.items);
      } else if (Array.isArray(res)) {
        setResults(res);
      } else {
        // Fallback to surplus radar
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

      if (res && Array.isArray(res.matches)) {
        setResults(res.matches);
      } else if (res && Array.isArray(res.items)) {
        setResults(res.items);
      } else if (Array.isArray(res)) {
        setResults(res);
      } else {
        setResults([]);
      }
    } catch (err: any) {
      setError(err.message || 'Search failed');
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
    if (!selectedForReq) return;

    setSubmittingReq(true);
    try {
      const payload = {
        sku_code: selectedForReq.sku_code,
        source_cpse: selectedForReq.cpse,
        requesting_cpse: cpse,
        required_qty: reqQty,
        urgency: reqUrgency,
        justification: reqJustification || `Material requisition from ${cpse} for ${selectedForReq.sku_code}`,
        target_depot: `${cpse} Main Depot`,
      };

      const res = await api.postRequisition(payload);
      setReqSuccess(`Requisition ${res.requisition_id || res.id} generated successfully!`);
      setSelectedForReq(null);
      setReqQty(1);
      setReqJustification('');
      setTimeout(() => setReqSuccess(null), 6000);
    } catch (err: any) {
      alert(`Requisition submission failed: ${err.message}`);
    } finally {
      setSubmittingReq(false);
    }
  };

  return (
    <div className="flex flex-col space-y-4 max-w-[1600px] mx-auto pb-8">
      {/* Top Banner */}
      <div className="p-5 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl shadow-2xs">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs font-mono font-semibold text-emerald-700 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/60 px-2 py-0.5 rounded border border-emerald-200 dark:border-emerald-800">
                PRE-PURCHASE RADAR
              </span>
              <span className="text-xs font-mono text-slate-500">
                Active Node: {cpse} · Cross-CPSE Sharing
              </span>
            </div>
            <h1 className="text-xl font-bold text-slate-900 dark:text-white tracking-tight">
              Cross-CPSE Surplus Discovery & Compatibility Radar
            </h1>
            <p className="text-xs text-slate-600 dark:text-slate-400 mt-0.5">
              Query sister CPSE surplus with automated 21-rule engineering tolerance, logistics transit estimates, and privacy-shielded commercial pricing.
            </p>
          </div>

          <button
            onClick={loadInitialSurplus}
            disabled={loading}
            className="self-start sm:self-auto px-3 py-1.5 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 border border-slate-300 dark:border-slate-700 rounded text-xs font-mono font-semibold flex items-center gap-1.5 transition-colors"
          >
            <RefreshCw size={13} className={loading ? 'animate-spin' : ''} />
            <span>Refresh Radar</span>
          </button>
        </div>

        {/* Search Input & Filter Strip */}
        <form onSubmit={handleSearch} className="mt-4 flex flex-wrap items-center gap-2 text-xs font-mono">
          <div className="relative flex-1 min-w-[280px]">
            <Search size={14} className="absolute left-3 top-2.5 text-slate-400" />
            <input
              type="text"
              placeholder="Search dialect or spec (e.g. 6 inch gate valve 600# IS 14846, A105 flange)..."
              value={queryText}
              onChange={(e) => setQueryText(e.target.value)}
              className="w-full pl-8 pr-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded text-slate-900 dark:text-slate-100 placeholder:text-slate-400 focus:outline-hidden focus:ring-1 focus:ring-emerald-500 text-xs"
            />
          </div>

          <select
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value)}
            className="bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded px-2.5 py-2 text-xs text-slate-800 dark:text-slate-200"
          >
            {ITEM_TYPES.map((t) => (
              <option key={t} value={t}>{t.replace('_', ' ')}</option>
            ))}
          </select>

          <button
            type="submit"
            disabled={loading}
            className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded font-semibold transition-colors flex items-center gap-1.5 disabled:opacity-50"
          >
            <Search size={13} />
            <span>Find Matches</span>
          </button>
        </form>
      </div>

      {reqSuccess && (
        <div className="p-3 bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 text-emerald-800 dark:text-emerald-300 text-xs font-mono rounded-lg flex items-center justify-between">
          <span className="font-semibold">{reqSuccess}</span>
          <button onClick={() => setReqSuccess(null)} className="text-slate-500 hover:text-slate-700">&times;</button>
        </div>
      )}

      {error && (
        <div className="p-3 bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900 text-rose-800 dark:text-rose-300 text-xs font-mono rounded-lg flex items-center justify-between">
          <span>{error}</span>
          <button onClick={loadInitialSurplus} className="underline font-semibold">Retry</button>
        </div>
      )}

      {/* Results Header */}
      <div className="flex items-center justify-between text-xs font-mono text-slate-500 px-1">
        <span>Discovered {results.length} surplus candidates</span>
        <span>Commercial pricing masked for cross-CPSE privacy</span>
      </div>

      {/* Results Grid / List */}
      {loading ? (
        <div className="py-20 text-center text-xs font-mono text-slate-500 bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800">
          <RefreshCw className="animate-spin h-6 w-6 mx-auto mb-2 text-emerald-500" />
          <span>Executing continuous compatibility ranking & logistics estimation...</span>
        </div>
      ) : results.length === 0 ? (
        <div className="py-16 text-center text-xs font-mono text-slate-500 bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800">
          <p>No surplus matches found matching the specified search criteria.</p>
          <button
            onClick={() => {
              setQueryText('');
              setSelectedType('ALL');
            }}
            className="mt-3 px-3 py-1.5 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 rounded"
          >
            Clear Filters & View All Available Surplus
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {results.map((item) => {
            const score = item.score ?? item.compatibility_score ?? 95.0;
            const tier = item.tier || (score >= 90 ? 1 : score >= 75 ? 2 : 3);
            const isSameCpse = item.cpse === cpse;

            return (
              <Card
                key={item.sku_code || item.id}
                className="p-4 border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-sm font-mono text-slate-900 dark:text-white">
                          {item.sku_code}
                        </span>
                        <StatusBadge tier={tier} />
                      </div>
                      {item.oil_material_code && (
                        <span className="text-[11px] font-mono text-emerald-700 dark:text-emerald-400">
                          MESC: {item.oil_material_code}
                        </span>
                      )}
                    </div>

                    <div className="text-right">
                      <span className="text-xs font-mono font-bold text-emerald-600 dark:text-emerald-400">
                        {score.toFixed(1)}% Match
                      </span>
                      <div className="text-[10px] font-mono text-slate-400">
                        {item.days_idle ?? 90}d idle
                      </div>
                    </div>
                  </div>

                  <p className="text-xs text-slate-800 dark:text-slate-200 font-medium mb-2.5">
                    {item.description || item.title || `${item.item_type || 'Part'} - ${item.metallurgy || ''}`}
                  </p>

                  <div className="grid grid-cols-2 gap-2 text-xs font-mono bg-slate-50 dark:bg-slate-800/60 p-2.5 rounded border border-slate-200 dark:border-slate-800 mb-3">
                    <div>
                      <span className="text-slate-400 block text-[10px]">Location</span>
                      <span className="font-semibold text-slate-800 dark:text-slate-200">
                        {item.cpse} · {item.depot_location || item.depot_id || 'Hub'}
                      </span>
                    </div>

                    <div>
                      <span className="text-slate-400 block text-[10px]">Available Quantity</span>
                      <span className="font-semibold text-slate-800 dark:text-slate-200">
                        {item.available_quantity ?? item.quantity ?? 1} {item.unit || 'EA'}
                      </span>
                    </div>

                    <div>
                      <span className="text-slate-400 block text-[10px]">Standard / Spec</span>
                      <span className="text-slate-700 dark:text-slate-300 truncate block" title={item.indian_standard || item.standard}>
                        {item.indian_standard || item.standard || 'IS / ASME'}
                      </span>
                    </div>

                    <div>
                      <span className="text-slate-400 block text-[10px]">Logistics Distance</span>
                      <span className="text-slate-700 dark:text-slate-300">
                        {item.distance_km ? `${item.distance_km} km (~${item.transit_hours || ''}h)` : 'Calculated on order'}
                      </span>
                    </div>
                  </div>

                  {/* Make In India & Commercial Privacy */}
                  <div className="flex items-center justify-between text-[11px] font-mono text-slate-500 mb-3">
                    <span className="flex items-center gap-1">
                      {item.make_in_india_class ? (
                        <span className="text-emerald-700 dark:text-emerald-400 font-semibold">
                          MII {item.make_in_india_class} ({item.local_content_percentage ?? 80}%)
                        </span>
                      ) : (
                        <span>MII Class-I</span>
                      )}
                    </span>

                    {isSameCpse && item.total_value_inr ? (
                      <span className="font-semibold text-slate-700 dark:text-slate-300">
                        Internal Value: ₹{(item.total_value_inr / 1e5).toFixed(2)} Lakh
                      </span>
                    ) : (
                      <span className="flex items-center gap-1 text-slate-400" title="Commercial price masked for cross-CPSE fair transfer">
                        <Lock size={11} /> Price Shielded (Inter-CPSE)
                      </span>
                    )}
                  </div>
                </div>

                <div className="pt-3 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between gap-2">
                  <div className="text-[11px] font-mono text-slate-500 truncate">
                    {item.cppp_tender_ref ? `CPPP: ${item.cppp_tender_ref}` : 'Ready for transfer'}
                  </div>

                  <button
                    onClick={() => {
                      setSelectedForReq(item);
                      setReqQty(1);
                      setReqJustification('');
                    }}
                    className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded text-xs font-mono font-semibold flex items-center gap-1.5 transition-colors"
                  >
                    <Send size={12} />
                    <span>Initiate Transfer</span>
                  </button>
                </div>
              </Card>
            );
          })}
        </div>
      )}

      {/* Requisition Creation Modal */}
      {selectedForReq && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-xl w-full max-w-lg overflow-hidden flex flex-col">
            <div className="p-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold font-mono text-slate-900 dark:text-white">
                  Initiate Inter-CPSE Requisition
                </h3>
                <p className="text-xs font-mono text-slate-500">
                  Target Part: {selectedForReq.sku_code} ({selectedForReq.cpse})
                </p>
              </div>
              <button
                onClick={() => setSelectedForReq(null)}
                className="p-1 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
              >
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleCreateRequisition} className="p-5 space-y-4 text-xs font-mono">
              <div>
                <label className="block text-slate-500 mb-1">Requesting CPSE</label>
                <input
                  type="text"
                  value={cpse}
                  disabled
                  className="w-full p-2 bg-slate-100 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded text-slate-700 dark:text-slate-300 font-semibold cursor-not-allowed"
                />
              </div>

              <div>
                <label className="block text-slate-500 mb-1">Source CPSE (Fulfilling Node)</label>
                <input
                  type="text"
                  value={`${selectedForReq.cpse} (${selectedForReq.depot_location || selectedForReq.depot_id || 'Main Yard'})`}
                  disabled
                  className="w-full p-2 bg-slate-100 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded text-slate-700 dark:text-slate-300 cursor-not-allowed"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-500 mb-1">Requisition Quantity</label>
                  <input
                    type="number"
                    min={1}
                    max={selectedForReq.available_quantity ?? selectedForReq.quantity ?? 100}
                    value={reqQty}
                    onChange={(e) => setReqQty(Number(e.target.value))}
                    className="w-full p-2 bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded text-slate-900 dark:text-slate-100 font-semibold"
                    required
                  />
                </div>

                <div>
                  <label className="block text-slate-500 mb-1">Urgency Level</label>
                  <select
                    value={reqUrgency}
                    onChange={(e: any) => setReqUrgency(e.target.value)}
                    className="w-full p-2 bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded text-slate-900 dark:text-slate-100 font-semibold"
                  >
                    <option value="STANDARD">Standard Planned</option>
                    <option value="CRITICAL_EMERGENCY">Emergency Breakdown</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-slate-500 mb-1">Technical Justification & Plant Requirement</label>
                <textarea
                  rows={3}
                  value={reqJustification}
                  onChange={(e) => setReqJustification(e.target.value)}
                  placeholder="State reason for transfer (e.g. Critical shutdown replacement, zero lead-time required)..."
                  className="w-full p-2 bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded text-slate-900 dark:text-slate-100 placeholder:text-slate-400"
                  required
                />
              </div>

              <div className="p-3 bg-slate-50 dark:bg-slate-800 rounded border border-slate-200 dark:border-slate-700 text-[11px] text-slate-500 space-y-1">
                <p>Transfer will be logged on the sovereign SHA-256 blockchain ledger.</p>
                <p>Fulfilling CPSE officer must authorize dispatch clearance and CISF gate pass.</p>
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setSelectedForReq(null)}
                  className="px-3 py-1.5 bg-slate-200 dark:bg-slate-800 hover:bg-slate-300 dark:hover:bg-slate-700 text-slate-800 dark:text-slate-200 rounded"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submittingReq}
                  className="px-4 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded font-semibold flex items-center gap-1.5 disabled:opacity-50"
                >
                  {submittingReq ? <RefreshCw size={13} className="animate-spin" /> : <Send size={13} />}
                  <span>Submit Requisition</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
