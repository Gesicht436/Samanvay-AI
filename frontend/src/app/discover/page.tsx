"use client";

import React, { useState, useEffect, useMemo } from 'react';
import { Card, StatusBadge, Modal } from '@/components/ui';
import {
  Search,
  Filter,
  ShoppingCart,
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
  Sparkles,
} from 'lucide-react';
import { CPSE_DEPOTS } from '@/lib/constants';

interface SurplusItem {
  id: string;
  sku_code: string;
  title: string;
  item_type: string;
  tier: 1 | 2;
  score: number;
  cpse: 'IOCL' | 'ONGC' | 'BPCL' | 'HPCL' | 'GAIL';
  depot_name: string;
  distance_km: number;
  transit_hours: number;
  metallurgy: string;
  pressure_class: string;
  schedule: string;
  facing: string;
  quantity: number;
  unit: string;
  days_idle: number;
  substitution_note?: string;
  scorecard: {
    rule_name: string;
    standard: string;
    candidate_spec: string;
    target_spec: string;
    status: 'PASS' | 'SAFE_UPGRADE' | 'WARNING';
    score: number;
    explanation: string;
  }[];
}

const SURPLUS_CATALOG: SurplusItem[] = [
  {
    id: 'sp-01',
    sku_code: 'IOCL-PNP-VLV-401',
    title: 'Gate Valve 6" Class 150# RF API 600',
    item_type: 'GATE_VALVE',
    tier: 1,
    score: 98.8,
    cpse: 'IOCL',
    depot_name: 'IOCL Panipat Refinery',
    distance_km: 320,
    transit_hours: 8.5,
    metallurgy: 'ASTM A216 WCB',
    pressure_class: '150#',
    schedule: 'STD',
    facing: 'RF (Raised Face)',
    quantity: 4,
    unit: 'EA',
    days_idle: 184,
    scorecard: [
      {
        rule_name: 'Dimension & Nominal Bore',
        standard: 'ASME B16.10',
        candidate_spec: 'DN 150 (6 IN)',
        target_spec: 'DN 150 (6 IN)',
        status: 'PASS',
        score: 1.0,
        explanation: 'Exact face-to-face and nominal bore match. Zero dimensional variance.',
      },
      {
        rule_name: 'Pressure Class Rating',
        standard: 'ASME B16.34',
        candidate_spec: 'Class 150# (20 bar @ 100°C)',
        target_spec: 'Class 150#',
        status: 'PASS',
        score: 1.0,
        explanation: 'Pressure boundary rating strictly identical to requisition.',
      },
      {
        rule_name: 'Metallurgy Compatibility',
        standard: 'ASTM A216',
        candidate_spec: 'Cast Carbon Steel WCB',
        target_spec: 'Cast Carbon Steel WCB',
        status: 'PASS',
        score: 1.0,
        explanation: 'Direct alloy equivalence under ASTM metallurgical DAG.',
      },
      {
        rule_name: 'Facing & Gasket Seating',
        standard: 'ASME B16.5',
        candidate_spec: 'RF 125-250 AARH',
        target_spec: 'RF (Raised Face)',
        status: 'PASS',
        score: 1.0,
        explanation: 'Standard spiral serration matching spiral wound and graphite sheet gaskets.',
      },
      {
        rule_name: 'Valve Trim Metallurgy',
        standard: 'API 600',
        candidate_spec: 'Trim 8 (13Cr / Hardfaced Stellite 6)',
        target_spec: 'Trim 1 (13Cr)',
        status: 'SAFE_UPGRADE',
        score: 0.98,
        explanation: 'Trim 8 provides superior erosion and galling resistance over standard Trim 1.',
      },
    ],
  },
  {
    id: 'sp-02',
    sku_code: 'BPCL-MUM-VLV-902',
    title: 'Gate Valve 6" Class 300# RF API 600',
    item_type: 'GATE_VALVE',
    tier: 2,
    score: 88.5,
    cpse: 'BPCL',
    depot_name: 'BPCL Mumbai Refinery',
    distance_km: 950,
    transit_hours: 24.0,
    metallurgy: 'ASTM A216 WCB',
    pressure_class: '300#',
    schedule: 'SCH 40',
    facing: 'RF (Raised Face)',
    quantity: 2,
    unit: 'EA',
    days_idle: 260,
    substitution_note: 'Pressure rating exceeds requirement (300# vs 150#). Safe heavy-duty substitution.',
    scorecard: [
      {
        rule_name: 'Dimension & Nominal Bore',
        standard: 'ASME B16.10',
        candidate_spec: 'DN 150 (6 IN)',
        target_spec: 'DN 150 (6 IN)',
        status: 'PASS',
        score: 1.0,
        explanation: 'Identical pipe bore diameter (150 mm).',
      },
      {
        rule_name: 'Pressure Class Rating',
        standard: 'ASME B16.34',
        candidate_spec: 'Class 300# (50 bar)',
        target_spec: 'Class 150# (20 bar)',
        status: 'SAFE_UPGRADE',
        score: 0.92,
        explanation: 'Candidate rating safely exceeds required working pressure. Up-rating allowed under ASME B31.3.',
      },
      {
        rule_name: 'Metallurgy Compatibility',
        standard: 'ASTM A216',
        candidate_spec: 'Cast Carbon Steel WCB',
        target_spec: 'Cast Carbon Steel WCB',
        status: 'PASS',
        score: 1.0,
        explanation: 'Identical body metallurgy.',
      },
      {
        rule_name: 'Weight & Flange Thickness',
        standard: 'ASME B16.5',
        candidate_spec: 'Flange thickness 36.5 mm (300#)',
        target_spec: 'Flange thickness 25.4 mm (150#)',
        status: 'WARNING',
        score: 0.85,
        explanation: 'Higher class flange requires longer mating bolts (5/8" x 3-1/2"). Check pipe rack dead load.',
      },
    ],
  },
  {
    id: 'sp-03',
    sku_code: 'ONGC-URN-FLG-551',
    title: 'Weld Neck Flange 4" Class 300# RF SCH 40',
    item_type: 'FLANGE',
    tier: 1,
    score: 99.4,
    cpse: 'ONGC',
    depot_name: 'ONGC Uran Gas Terminal',
    distance_km: 120,
    transit_hours: 3.5,
    metallurgy: 'ASTM A105',
    pressure_class: '300#',
    schedule: 'SCH 40',
    facing: 'RF (Raised Face)',
    quantity: 16,
    unit: 'EA',
    days_idle: 95,
    scorecard: [
      {
        rule_name: 'Flange Dimensions',
        standard: 'ASME B16.5',
        candidate_spec: '4" Class 300 RF',
        target_spec: '4" Class 300 RF',
        status: 'PASS',
        score: 1.0,
        explanation: 'Bolt circle diameter, bolt hole count (8 holes), and OD match exactly.',
      },
      {
        rule_name: 'Bore & Schedule Alignment',
        standard: 'ASME B36.10M',
        candidate_spec: 'SCH 40 (Wall 6.02 mm)',
        target_spec: 'SCH 40 (Wall 6.02 mm)',
        status: 'PASS',
        score: 1.0,
        explanation: 'Internal pipe bore matches without turbulence or flow restriction.',
      },
      {
        rule_name: 'Metallurgy & Heat Treatment',
        standard: 'ASTM A105',
        candidate_spec: 'Forged Carbon Steel A105',
        target_spec: 'ASTM A105',
        status: 'PASS',
        score: 1.0,
        explanation: 'EN 10204 3.1 Certified. CE = 0.41% (Standard weldable).',
      },
    ],
  },
  {
    id: 'sp-04',
    sku_code: 'HPCL-VSK-VLV-112',
    title: 'Gate Valve Body 6" Class 600# RTJ ASTM A350 LF2',
    item_type: 'GATE_VALVE',
    tier: 1,
    score: 97.2,
    cpse: 'HPCL',
    depot_name: 'HPCL Visakh Refinery',
    distance_km: 1480,
    transit_hours: 36.0,
    metallurgy: 'ASTM A350 LF2',
    pressure_class: '600#',
    schedule: 'SCH 80',
    facing: 'RTJ (Ring Type Joint)',
    quantity: 3,
    unit: 'EA',
    days_idle: 310,
    scorecard: [
      {
        rule_name: 'Cryogenic Toughness',
        standard: 'ASTM A350',
        candidate_spec: 'LF2 Class 1 (Charpy 38J @ -46°C)',
        target_spec: 'LF2 Class 1',
        status: 'PASS',
        score: 1.0,
        explanation: 'Exceeds minimum sub-zero impact toughness requirements for cryogenic service.',
      },
      {
        rule_name: 'Groove Sealing Compatibility',
        standard: 'ASME B16.5',
        candidate_spec: 'RTJ Ring Groove R45',
        target_spec: 'RTJ Groove R45',
        status: 'PASS',
        score: 1.0,
        explanation: 'Groove geometry and surface roughness strictly conform to ASME B16.20.',
      },
      {
        rule_name: 'Sour Duty Hardness Ceiling',
        standard: 'NACE MR0175 / ISO 15156',
        candidate_spec: '170 HBW (Max 187 HBW)',
        target_spec: '<= 22 HRC (187 HBW)',
        status: 'PASS',
        score: 1.0,
        explanation: 'Complies with wet H2S sulfide stress cracking hardness limits.',
      },
    ],
  },
  {
    id: 'sp-05',
    sku_code: 'GAIL-PAT-FLG-880',
    title: 'Blind Flange 2" Class 150# RF ASTM A182 F316L',
    item_type: 'FLANGE',
    tier: 1,
    score: 99.1,
    cpse: 'GAIL',
    depot_name: 'GAIL Pata Petrochemical',
    distance_km: 410,
    transit_hours: 10.0,
    metallurgy: 'ASTM A182 F316L',
    pressure_class: '150#',
    schedule: 'BLIND',
    facing: 'RF (Raised Face)',
    quantity: 8,
    unit: 'EA',
    days_idle: 125,
    scorecard: [
      {
        rule_name: 'Corrosion Resistance (PREN)',
        standard: 'ASTM A182',
        candidate_spec: 'PREN 25.02 (Cr 17.2, Mo 2.15, N 0.045)',
        target_spec: 'F316L Stainless Steel',
        status: 'PASS',
        score: 1.0,
        explanation: 'Extra low carbon prevents sensitization during welding. Marine duty qualified.',
      },
    ],
  },
];

export default function DiscoverPage() {
  const [search, setSearch] = useState('');
  const [selectedCpse, setSelectedCpse] = useState<string>('ALL');
  const [selectedTier, setSelectedTier] = useState<string>('ALL');
  const [selectedClass, setSelectedClass] = useState<string>('ALL');
  const [inspectingItem, setInspectingItem] = useState<SurplusItem | null>(null);
  const [requisitionItem, setRequisitionItem] = useState<SurplusItem | null>(null);
  const [reqQuantity, setReqQuantity] = useState<number>(1);
  const [reqJustification, setReqJustification] = useState<string>('Emergency Breakdown Replacement');
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  // Handle Ctrl+K shortcut
  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === 'k' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        document.getElementById('global-search')?.focus();
      }
    };
    document.addEventListener('keydown', down);
    return () => document.removeEventListener('keydown', down);
  }, []);

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 3500);
  };

  const filteredItems = useMemo(() => {
    return SURPLUS_CATALOG.filter((item) => {
      if (selectedCpse !== 'ALL' && item.cpse !== selectedCpse) return false;
      if (selectedTier !== 'ALL' && String(item.tier) !== selectedTier) return false;
      if (selectedClass !== 'ALL' && item.pressure_class !== selectedClass) return false;

      if (search.trim()) {
        const q = search.toLowerCase();
        return (
          item.title.toLowerCase().includes(q) ||
          item.sku_code.toLowerCase().includes(q) ||
          item.metallurgy.toLowerCase().includes(q) ||
          item.depot_name.toLowerCase().includes(q)
        );
      }
      return true;
    });
  }, [search, selectedCpse, selectedTier, selectedClass]);

  const handleSendRequisition = () => {
    if (!requisitionItem) return;
    showToast(`Requisition sent to ${requisitionItem.cpse} for ${reqQuantity}x ${requisitionItem.title}`);
    setRequisitionItem(null);
  };

  return (
    <div className="flex flex-col h-full space-y-4 max-w-[1600px] mx-auto">
      {/* Toast Notification */}
      {toastMessage && (
        <div className="fixed bottom-6 right-6 z-50 bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-900 px-4 py-2.5 rounded-lg shadow-xl text-xs font-mono font-semibold flex items-center gap-2 border border-slate-700 animate-in fade-in slide-in-from-bottom-2">
          <CheckCircle2 size={16} className="text-emerald-400" />
          <span>{toastMessage}</span>
        </div>
      )}

      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-white dark:bg-slate-900 p-5 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-xs shrink-0">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono font-bold text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/60 px-2.5 py-0.5 rounded-full border border-emerald-200 dark:border-emerald-800 flex items-center gap-1.5">
              <Sparkles size={12} /> Pre-Purchase Compatibility Radar
            </span>
            <span className="text-xs font-mono text-slate-500">21 Safety Rules Active</span>
          </div>
          <h1 className="text-2xl font-bold font-mono text-slate-900 dark:text-slate-100 tracking-tight mt-1">
            Cross-CPSE Surplus Material Discovery
          </h1>
          <p className="text-xs font-mono text-slate-500 mt-0.5">
            Real-time multi-PSU surplus lookup with mathematical zero-tolerance verification & attribute-level privacy
          </p>
        </div>

        <div className="flex items-center gap-2 bg-slate-50 dark:bg-slate-800/80 px-3 py-1.5 rounded-xl border border-slate-200 dark:border-slate-700 text-xs font-mono text-slate-600 dark:text-slate-300">
          <Lock size={14} className="text-amber-500" />
          <span>Commercial Pricing Masked (SIH Slide 4)</span>
        </div>
      </div>

      {/* Global Search Bar */}
      <div className="relative shrink-0">
        <Search className="absolute left-3.5 top-3 text-slate-400" size={18} />
        <input
          id="global-search"
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search parts by description, ASME class, metallurgy, or SKU (Press Ctrl+K)..."
          className="w-full pl-11 pr-4 py-2.5 border border-slate-200 dark:border-slate-700 rounded-xl bg-white dark:bg-slate-900 text-sm font-mono text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:ring-2 focus:ring-emerald-500 focus:outline-none shadow-xs"
        />
      </div>

      {/* Content Layout: Faceted Filter Sidebar + Results Deck */}
      <div className="flex flex-col lg:flex-row gap-5 flex-1 min-h-0 overflow-hidden">
        {/* Sidebar Filters */}
        <div className="w-full lg:w-72 bg-white dark:bg-slate-900 p-5 border border-slate-200 dark:border-slate-800 rounded-2xl shrink-0 overflow-y-auto space-y-6 shadow-xs">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800 font-mono text-xs font-bold uppercase tracking-wider text-slate-900 dark:text-slate-100">
            <span className="flex items-center gap-1.5">
              <Filter size={14} className="text-emerald-500" /> Parametric Filters
            </span>
            <button
              onClick={() => {
                setSelectedCpse('ALL');
                setSelectedTier('ALL');
                setSelectedClass('ALL');
                setSearch('');
              }}
              className="text-[10px] text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 lowercase font-normal"
            >
              reset
            </button>
          </div>

          {/* Filter: CPSE Node */}
          <div className="space-y-2">
            <h4 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-500">
              Holding CPSE Node
            </h4>
            <div className="space-y-1 text-xs font-mono">
              {['ALL', 'IOCL', 'ONGC', 'BPCL', 'HPCL', 'GAIL'].map((c) => (
                <label
                  key={c}
                  className={`flex items-center justify-between px-2.5 py-1.5 rounded-lg cursor-pointer transition-colors ${
                    selectedCpse === c
                      ? 'bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-900 font-bold'
                      : 'text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800'
                  }`}
                >
                  <span>{c === 'ALL' ? 'All Enterprise Nodes' : c}</span>
                  <input
                    type="radio"
                    name="cpse"
                    checked={selectedCpse === c}
                    onChange={() => setSelectedCpse(c)}
                    className="hidden"
                  />
                </label>
              ))}
            </div>
          </div>

          {/* Filter: Compatibility Tier */}
          <div className="space-y-2">
            <h4 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-500">
              Dynamic Tier
            </h4>
            <div className="space-y-1 text-xs font-mono">
              {[
                { id: 'ALL', label: 'All Match Levels' },
                { id: '1', label: 'Tier 1 · Direct Drop-in (≥95%)' },
                { id: '2', label: 'Tier 2 · Safe Upgrade (80-94%)' },
              ].map((t) => (
                <label
                  key={t.id}
                  className={`flex items-center justify-between px-2.5 py-1.5 rounded-lg cursor-pointer transition-colors ${
                    selectedTier === t.id
                      ? 'bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-900 font-bold'
                      : 'text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800'
                  }`}
                >
                  <span>{t.label}</span>
                  <input
                    type="radio"
                    name="tier"
                    checked={selectedTier === t.id}
                    onChange={() => setSelectedTier(t.id)}
                    className="hidden"
                  />
                </label>
              ))}
            </div>
          </div>

          {/* Filter: Pressure Class */}
          <div className="space-y-2">
            <h4 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-500">
              ASME Pressure Rating
            </h4>
            <div className="grid grid-cols-2 gap-1.5 text-xs font-mono">
              {['ALL', '150#', '300#', '600#'].map((rating) => (
                <button
                  key={rating}
                  onClick={() => setSelectedClass(rating)}
                  className={`px-2 py-1.5 rounded-lg border text-center transition-colors ${
                    selectedClass === rating
                      ? 'bg-emerald-600 text-white border-emerald-600 font-bold'
                      : 'bg-slate-50 dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300'
                  }`}
                >
                  {rating}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Results List */}
        <div className="flex-1 overflow-y-auto space-y-4 pr-1">
          {filteredItems.length === 0 ? (
            <Card className="p-12 text-center text-slate-500 font-mono text-sm border-dashed">
              <Search size={32} className="mx-auto text-slate-400 mb-2" />
              <p className="font-bold text-slate-800 dark:text-slate-200">No surplus matches found</p>
              <p className="text-xs text-slate-400 mt-1">
                Try widening your pressure class or changing the holding CPSE node.
              </p>
            </Card>
          ) : (
            filteredItems.map((item) => (
              <Card
                key={item.id}
                className="p-5 border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 hover:border-emerald-500/70 transition-all duration-150 space-y-4 shadow-xs"
              >
                <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-2">
                  <div>
                    <div className="flex items-center gap-2.5 flex-wrap">
                      <h3 className="font-bold font-mono text-base text-slate-900 dark:text-slate-100">
                        {item.title}
                      </h3>
                      <button
                        onClick={() => setInspectingItem(item)}
                        className="cursor-pointer"
                        title="Click to view 21-rule engineering scorecard"
                      >
                        <StatusBadge tier={item.tier} />
                      </button>
                    </div>

                    <p className="text-xs font-mono text-slate-500 mt-1">
                      SKU: <span className="text-slate-700 dark:text-slate-300 font-semibold">{item.sku_code}</span> · Material:{' '}
                      <span className="text-slate-700 dark:text-slate-300 font-semibold">{item.metallurgy}</span> · Rating:{' '}
                      <span className="text-slate-700 dark:text-slate-300 font-semibold">{item.pressure_class}</span> · Facing:{' '}
                      <span className="text-slate-700 dark:text-slate-300 font-semibold">{item.facing}</span>
                    </p>
                  </div>

                  <div className="text-right shrink-0">
                    <span className="text-sm font-bold font-mono text-slate-900 dark:text-slate-100">
                      {item.quantity} {item.unit} Surplus
                    </span>
                    <span className="block text-[10px] font-mono text-slate-400">
                      Dormant: {item.days_idle} days
                    </span>
                  </div>
                </div>

                {/* Substitution Alert if Tier 2 */}
                {item.substitution_note && (
                  <div className="p-2.5 bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-900/60 rounded-lg text-xs font-mono text-amber-800 dark:text-amber-300 flex items-start gap-2">
                    <AlertTriangle size={14} className="text-amber-600 mt-0.5 shrink-0" />
                    <span>{item.substitution_note}</span>
                  </div>
                )}

                {/* Logistics & Privacy Footer Strip */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-3 border-t border-slate-100 dark:border-slate-800 text-xs font-mono">
                  <div className="flex items-center gap-4 flex-wrap text-slate-500">
                    <span className="flex items-center gap-1.5 text-slate-700 dark:text-slate-300 font-medium">
                      <Building2 size={14} className="text-emerald-500" /> {item.depot_name}
                    </span>
                    <span className="flex items-center gap-1.5">
                      <Truck size={14} className="text-slate-400" /> {item.distance_km} km (~{item.transit_hours} hrs via NH)
                    </span>
                    <span
                      className="px-2 py-0.5 bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 rounded border border-slate-200 dark:border-slate-700 text-[10px] font-bold flex items-center gap-1 cursor-help"
                      title="Commercial prices remain strictly hidden across competing PSUs per SIH guidelines"
                    >
                      <Lock size={10} className="text-amber-500" /> PRICE MASKED
                    </span>
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => setInspectingItem(item)}
                      className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-800 dark:text-slate-200 rounded-lg text-xs font-mono font-semibold transition-colors flex items-center gap-1"
                    >
                      <Layers size={13} /> Inspect Safety Rules
                    </button>

                    <button
                      onClick={() => setRequisitionItem(item)}
                      className="px-3.5 py-1.5 bg-slate-900 hover:bg-slate-800 dark:bg-emerald-600 dark:hover:bg-emerald-700 text-white rounded-lg text-xs font-mono font-bold transition-all shadow-xs flex items-center gap-1.5"
                    >
                      <ShoppingCart size={13} /> Compose Requisition
                    </button>
                  </div>
                </div>
              </Card>
            ))
          )}
        </div>
      </div>

      {/* 21-Rule Tolerance & Safety Scorecard Modal */}
      {inspectingItem && (
        <Modal isOpen={Boolean(inspectingItem)} onClose={() => setInspectingItem(null)}>
          <div className="space-y-4">
            <div className="flex items-start justify-between border-b border-slate-200 dark:border-slate-800 pb-3">
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-base font-bold font-mono text-slate-900 dark:text-slate-100">
                    {inspectingItem.title}
                  </h3>
                  <StatusBadge tier={inspectingItem.tier} />
                </div>
                <p className="text-xs font-mono text-slate-500 mt-1">
                  SKU: {inspectingItem.sku_code} · Depot: {inspectingItem.depot_name}
                </p>
              </div>
            </div>

            <div className="p-3 bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800/60 rounded-xl text-xs font-mono text-emerald-800 dark:text-emerald-300 flex items-center justify-between">
              <span className="flex items-center gap-1.5 font-bold">
                <ShieldCheck size={16} /> Continuous Compatibility Rating:
              </span>
              <span className="text-sm font-bold">{inspectingItem.score}%</span>
            </div>

            {/* Scorecard Table */}
            <div className="space-y-2">
              <h4 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-500">
                21 Codified Engineering Safety Modules Evaluation
              </h4>
              <div className="border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden">
                <table className="w-full text-xs font-mono">
                  <thead className="bg-slate-50 dark:bg-slate-800/80 text-slate-500 border-b border-slate-200 dark:border-slate-800 text-[10px] uppercase">
                    <tr>
                      <th className="p-2.5 text-left">Module / Standard</th>
                      <th className="p-2.5 text-left">Specification Comparison</th>
                      <th className="p-2.5 text-right">Result</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                    {inspectingItem.scorecard.map((row, idx) => (
                      <tr key={idx} className="hover:bg-slate-50 dark:hover:bg-slate-800/40">
                        <td className="p-2.5 font-bold text-slate-800 dark:text-slate-200">
                          {row.rule_name}
                          <span className="block text-[10px] text-slate-400 font-normal">
                            {row.standard}
                          </span>
                        </td>
                        <td className="p-2.5 text-slate-600 dark:text-slate-300">
                          <div>
                            <span className="text-slate-400 text-[10px]">Surplus: </span>
                            <span className="font-semibold">{row.candidate_spec}</span>
                          </div>
                          <p className="text-[10px] text-slate-400 mt-0.5">{row.explanation}</p>
                        </td>
                        <td className="p-2.5 text-right font-bold">
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] ${
                              row.status === 'PASS'
                                ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/80 dark:text-emerald-300'
                                : row.status === 'SAFE_UPGRADE'
                                ? 'bg-blue-100 text-blue-800 dark:bg-blue-950/80 dark:text-blue-300'
                                : 'bg-amber-100 text-amber-800 dark:bg-amber-950/80 dark:text-amber-300'
                            }`}
                          >
                            {row.status}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            <div className="pt-2 text-right">
              <button
                onClick={() => {
                  const itm = inspectingItem;
                  setInspectingItem(null);
                  setRequisitionItem(itm);
                }}
                className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-mono font-bold transition-all shadow-xs"
              >
                Proceed to Requisition
              </button>
            </div>
          </div>
        </Modal>
      )}

      {/* Compose Requisition Modal */}
      {requisitionItem && (
        <Modal isOpen={Boolean(requisitionItem)} onClose={() => setRequisitionItem(null)}>
          <div className="space-y-4">
            <div className="border-b border-slate-200 dark:border-slate-800 pb-3">
              <h3 className="text-base font-bold font-mono text-slate-900 dark:text-slate-100">
                Compose Inter-CPSE Requisition
              </h3>
              <p className="text-xs font-mono text-slate-500 mt-0.5">
                Target Node: {requisitionItem.cpse} ({requisitionItem.depot_name})
              </p>
            </div>

            <div className="p-3 bg-slate-50 dark:bg-slate-800 rounded-lg text-xs font-mono space-y-1">
              <p className="font-bold text-slate-800 dark:text-slate-200">{requisitionItem.title}</p>
              <p className="text-slate-500">
                Available Stock: {requisitionItem.quantity} {requisitionItem.unit} · Metallurgy:{' '}
                {requisitionItem.metallurgy}
              </p>
            </div>

            <div className="space-y-3 font-mono text-xs">
              <div>
                <label className="block text-slate-500 font-bold mb-1">Required Quantity</label>
                <input
                  type="number"
                  min="1"
                  max={requisitionItem.quantity}
                  value={reqQuantity}
                  onChange={(e) => setReqQuantity(Math.max(1, parseInt(e.target.value) || 1))}
                  className="w-full p-2 bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-lg text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                />
              </div>

              <div>
                <label className="block text-slate-500 font-bold mb-1">Operational Justification</label>
                <select
                  value={reqJustification}
                  onChange={(e) => setReqJustification(e.target.value)}
                  className="w-full p-2 bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-lg text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                >
                  <option value="Emergency Breakdown Replacement">Emergency Breakdown Replacement (&lt;24h SLA)</option>
                  <option value="Scheduled Plant Turnaround Maintenance">Scheduled Plant Turnaround Maintenance</option>
                  <option value="Buffer Safety Stock Depletion">Buffer Safety Stock Depletion</option>
                </select>
              </div>
            </div>

            <div className="pt-3 border-t border-slate-200 dark:border-slate-800 flex justify-end gap-2.5">
              <button
                onClick={() => setRequisitionItem(null)}
                className="px-4 py-2 border border-slate-300 dark:border-slate-700 text-slate-600 dark:text-slate-400 rounded-lg text-xs font-mono font-semibold hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleSendRequisition}
                className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-mono font-bold transition-all shadow-xs flex items-center gap-1.5"
              >
                <Check size={14} /> Submit Inter-CPSE Requisition
              </button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}
