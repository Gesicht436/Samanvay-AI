"use client";

import React, { useState, useMemo } from 'react';
import { Card, KpiCard, StatusBadge } from '@/components/ui';
import {
  Package,
  Radio,
  AlertTriangle,
  Archive,
  Search,
  Filter,
  Download,
  CheckCircle2,
  XCircle,
  ArrowRight,
  Database,
  Building2,
  Check,
} from 'lucide-react';
import { exportToCSV } from '@/lib/exportUtils';
import { useTheme } from '@/components/ThemeProvider';
import { CPSE_DEPOTS } from '@/lib/constants';

interface InventoryItem {
  id: string;
  sku_code: string;
  description: string;
  category: 'FLANGE' | 'VALVE' | 'PIPE' | 'FASTENER' | 'GASKET' | 'ROTATING';
  metallurgy: string;
  pressure_class: string;
  size: string;
  quantity: number;
  unit: string;
  status: 'IN_STORAGE' | 'IDLE_SURPLUS' | 'TO_BE_CONSUMED' | 'ARCHIVED';
  days_idle: number;
  heat_no: string;
}

const INITIAL_INVENTORY: InventoryItem[] = [
  {
    id: 'inv-001',
    sku_code: 'PRT-8892',
    description: 'Weld Neck Flange 4" Class 300 RF SCH 40',
    category: 'FLANGE',
    metallurgy: 'ASTM A105',
    pressure_class: '300#',
    size: '100 mm (4")',
    quantity: 12,
    unit: 'EA',
    status: 'IDLE_SURPLUS',
    days_idle: 142,
    heat_no: 'HT-2025-20300',
  },
  {
    id: 'inv-002',
    sku_code: 'PRT-8893',
    description: 'Globe Valve 2" Class 150 RF Bolted Bonnet',
    category: 'VALVE',
    metallurgy: 'ASTM A182 F316',
    pressure_class: '150#',
    size: '50 mm (2")',
    quantity: 4,
    unit: 'EA',
    status: 'IN_STORAGE',
    days_idle: 38,
    heat_no: 'HT-SS-9912',
  },
  {
    id: 'inv-003',
    sku_code: 'PRT-9014',
    description: 'Gate Valve 6" Class 600 RTJ Full Bore API 600',
    category: 'VALVE',
    metallurgy: 'ASTM A350 LF2',
    pressure_class: '600#',
    size: '150 mm (6")',
    quantity: 6,
    unit: 'EA',
    status: 'IDLE_SURPLUS',
    days_idle: 210,
    heat_no: 'HT-LF2-9014',
  },
  {
    id: 'inv-004',
    sku_code: 'PRT-7721',
    description: 'Seamless Pipe 6" SCH 80 BE API 5L PSL 2',
    category: 'PIPE',
    metallurgy: 'API 5L Gr. B',
    pressure_class: 'SCH 80',
    size: '150 mm (6")',
    quantity: 48,
    unit: 'MTR',
    status: 'TO_BE_CONSUMED',
    days_idle: 15,
    heat_no: 'HT-P-55102',
  },
  {
    id: 'inv-005',
    sku_code: 'PRT-6610',
    description: 'Stud Bolts 1-1/8" x 7" Heavy Hex with 2H Nuts',
    category: 'FASTENER',
    metallurgy: 'ASTM A193 B7 / A194 2H',
    pressure_class: 'High Temp',
    size: '1-1/8" x 7"',
    quantity: 120,
    unit: 'SET',
    status: 'IDLE_SURPLUS',
    days_idle: 180,
    heat_no: 'HT-B7-8821',
  },
  {
    id: 'inv-006',
    sku_code: 'PRT-5512',
    description: 'Spiral Wound Gasket 4" 300# 316L/Graphite with Inner Ring',
    category: 'GASKET',
    metallurgy: 'SS316L / Flexible Graphite',
    pressure_class: '300#',
    size: '100 mm (4")',
    quantity: 35,
    unit: 'EA',
    status: 'IN_STORAGE',
    days_idle: 45,
    heat_no: 'HT-SWG-4401',
  },
  {
    id: 'inv-007',
    sku_code: 'PRT-4401',
    description: 'Centrifugal Pump Impeller Cast SS316 API 610 OH2',
    category: 'ROTATING',
    metallurgy: 'ASTM A743 CF8M',
    pressure_class: 'API 610 S-6',
    size: '250 mm dia',
    quantity: 2,
    unit: 'EA',
    status: 'ARCHIVED',
    days_idle: 340,
    heat_no: 'HT-ROT-1092',
  },
];

interface HITLCase {
  id: string;
  sourceSku: string;
  physicalPart: {
    description: string;
    metallurgy: string;
    rating: string;
    schedule: string;
    facing: string;
  };
  extractedMTC: {
    filename: string;
    certificate_no: string;
    description: string;
    metallurgy: string;
    rating: string;
    schedule: string;
    facing: string;
    confidence: number;
    varianceReason: string;
  };
}

const HITL_CASES: HITLCase[] = [
  {
    id: 'hitl-01',
    sourceSku: 'PRT-8892',
    physicalPart: {
      description: 'Weld Neck Flange 4" 300# RF SCH 40',
      metallurgy: 'ASTM A105',
      rating: 'Class 300#',
      schedule: 'SCH 40',
      facing: 'RF (Raised Face)',
    },
    extractedMTC: {
      filename: 'MTC_L&T_Hazira_Scan_Smudged.pdf',
      certificate_no: 'MTC/2026/5516',
      description: 'WELD NECK FLG 4IN 300LBS RF SCH40 NORM',
      metallurgy: 'ASTM A105N (Normalized)',
      rating: 'Class 300#',
      schedule: 'SCH 40',
      facing: 'RF (Raised Face)',
      confidence: 88.6,
      varianceReason: 'Grade A105N is a superior heat-treated equivalent of A105. Zero tolerance dimensions match.',
    },
  },
  {
    id: 'hitl-02',
    sourceSku: 'PRT-9014',
    physicalPart: {
      description: 'Gate Valve 6" 600# RTJ API 600',
      metallurgy: 'ASTM A216 WCB',
      rating: 'Class 600#',
      schedule: 'SCH 80',
      facing: 'RTJ (Ring Type Joint)',
    },
    extractedMTC: {
      filename: 'BHEL_GateValve_OCR_Scan.pdf',
      certificate_no: 'BHEL/QA/2026/8941',
      description: 'GATE VALVE 6" 600# RTJ BODY A350 LF2',
      metallurgy: 'ASTM A350 LF2 (Cryogenic)',
      rating: 'Class 600#',
      schedule: 'SCH 80',
      facing: 'RTJ',
      confidence: 91.2,
      varianceReason: 'A350 LF2 exceeds A216 WCB impact toughness. Safe low-temp upgrade for general hydrocarbon duty.',
    },
  },
];

export default function InventoryPage() {
  const { cpse } = useTheme();
  const currentDepot = CPSE_DEPOTS.find((d) => d.id === cpse) || CPSE_DEPOTS[0];

  const [activeTab, setActiveTab] = useState<'ALL' | 'SURPLUS' | 'HITL' | 'ARCHIVED'>('ALL');
  const [inventory, setInventory] = useState<InventoryItem[]>(INITIAL_INVENTORY);
  const [hitlList, setHitlList] = useState<HITLCase[]>(HITL_CASES);
  const [searchQuery, setSearchQuery] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('ALL');
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 3500);
  };

  const handleToggleSurplus = (id: string) => {
    setInventory((prev) =>
      prev.map((item) => {
        if (item.id === id) {
          const newStatus = item.status === 'IDLE_SURPLUS' ? 'IN_STORAGE' : 'IDLE_SURPLUS';
          showToast(`Updated ${item.sku_code} status to ${newStatus}`);
          return { ...item, status: newStatus };
        }
        return item;
      })
    );
  };

  const handleApproveHITL = (hitlId: string) => {
    const item = hitlList.find((h) => h.id === hitlId);
    if (!item) return;

    setHitlList((prev) => prev.filter((h) => h.id !== hitlId));
    showToast(`Approved & Merged ${item.sourceSku} into Plant Ledger.`);
  };

  const handleRejectHITL = (hitlId: string) => {
    setHitlList((prev) => prev.filter((h) => h.id !== hitlId));
    showToast(`Rejected candidate match for ${hitlId}. Logged in Audit Trail.`);
  };

  const filteredItems = useMemo(() => {
    return inventory.filter((item) => {
      // Tab filter
      if (activeTab === 'SURPLUS' && item.status !== 'IDLE_SURPLUS') return false;
      if (activeTab === 'ARCHIVED' && item.status !== 'ARCHIVED') return false;

      // Category filter
      if (categoryFilter !== 'ALL' && item.category !== categoryFilter) return false;

      // Search query
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        return (
          item.sku_code.toLowerCase().includes(q) ||
          item.description.toLowerCase().includes(q) ||
          item.metallurgy.toLowerCase().includes(q) ||
          item.heat_no.toLowerCase().includes(q)
        );
      }
      return true;
    });
  }, [inventory, activeTab, categoryFilter, searchQuery]);

  const handleExport = () => {
    exportToCSV(`plant_ledger_${currentDepot.city.toLowerCase()}.csv`, filteredItems);
    showToast('Exported inventory catalog (RFC 4180 CSV).');
  };

  return (
    <div className="flex flex-col h-full space-y-5 max-w-[1600px] mx-auto">
      {/* Toast Notification */}
      {toastMessage && (
        <div className="fixed bottom-6 right-6 z-50 bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-900 px-4 py-2.5 rounded-lg shadow-xl text-xs font-mono font-semibold flex items-center gap-2 border border-slate-700 animate-in fade-in slide-in-from-bottom-2">
          <CheckCircle2 size={16} className="text-emerald-400" />
          <span>{toastMessage}</span>
        </div>
      )}

      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-white dark:bg-slate-900 p-5 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-xs">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono font-bold text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/60 px-2.5 py-0.5 rounded-full border border-emerald-200 dark:border-emerald-800 flex items-center gap-1.5">
              <Building2 size={12} /> {currentDepot.name}
            </span>
            <span className="text-xs font-mono text-slate-500">Node ID: {currentDepot.id}</span>
          </div>
          <h1 className="text-2xl font-bold font-mono text-slate-900 dark:text-slate-100 tracking-tight mt-1">
            Plant Stock Ledger & Surplus Control
          </h1>
          <p className="text-xs font-mono text-slate-500 mt-0.5">
            Real-time material status, broadcasted surplus controls, and human-in-the-loop verification
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            onClick={handleExport}
            className="px-3.5 py-2 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-800 dark:text-slate-200 rounded-lg text-xs font-mono font-semibold flex items-center gap-2 transition-colors border border-slate-200 dark:border-slate-700"
          >
            <Download size={14} /> Export CSV / SAP MM
          </button>
        </div>
      </div>

      {/* Metric Strip */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard
          title="Total Cataloged Stock"
          value="1,420"
          unit="Line Items"
          delta="+24 this month"
          isPositive={true}
          icon={Package}
        />
        <KpiCard
          title="Broadcasted Surplus"
          value={inventory.filter((i) => i.status === 'IDLE_SURPLUS').length}
          unit="Active on Radar"
          delta="Broadcasting to 5 PSUs"
          isPositive={true}
          icon={Radio}
        />
        <KpiCard
          title="HITL Triage Queue"
          value={hitlList.length}
          unit="Pending Sign-off"
          delta={hitlList.length > 0 ? "Requires review" : "Queue clear"}
          isPositive={hitlList.length === 0}
          icon={AlertTriangle}
        />
        <KpiCard
          title="Idle Capital Unlocked"
          value={`₹${currentDepot.unlockedValueCr} Cr`}
          unit="Book Value"
          delta="+8.4% recovered"
          isPositive={true}
          icon={Database}
        />
      </div>

      {/* Navigation Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 px-4 py-2 rounded-xl shadow-xs">
        <button
          onClick={() => setActiveTab('ALL')}
          className={`px-3 py-1.5 rounded-lg text-xs font-mono font-bold transition-all ${
            activeTab === 'ALL'
              ? 'bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-900'
              : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800'
          }`}
        >
          All Inventory Stock ({inventory.length})
        </button>

        <button
          onClick={() => setActiveTab('SURPLUS')}
          className={`px-3 py-1.5 rounded-lg text-xs font-mono font-bold transition-all flex items-center gap-1.5 ${
            activeTab === 'SURPLUS'
              ? 'bg-emerald-600 text-white'
              : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800'
          }`}
        >
          <Radio size={12} className={activeTab === 'SURPLUS' ? 'animate-pulse' : ''} />
          Broadcasted Surplus ({inventory.filter((i) => i.status === 'IDLE_SURPLUS').length})
        </button>

        <button
          onClick={() => setActiveTab('HITL')}
          className={`px-3 py-1.5 rounded-lg text-xs font-mono font-bold transition-all flex items-center gap-1.5 ${
            activeTab === 'HITL'
              ? 'bg-amber-500 text-white'
              : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800'
          }`}
        >
          <AlertTriangle size={12} />
          HITL Triage Queue
          {hitlList.length > 0 && (
            <span className="px-1.5 py-0.2 rounded-full bg-rose-500 text-white text-[10px]">
              {hitlList.length}
            </span>
          )}
        </button>

        <button
          onClick={() => setActiveTab('ARCHIVED')}
          className={`px-3 py-1.5 rounded-lg text-xs font-mono font-bold transition-all ${
            activeTab === 'ARCHIVED'
              ? 'bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-900'
              : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800'
          }`}
        >
          Consumed / Archived
        </button>
      </div>

      {/* Main Tab Views */}
      {activeTab === 'HITL' ? (
        /* HITL Diff Triage View */
        <div className="space-y-4">
          <div className="p-4 bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-900/60 rounded-xl text-xs font-mono text-amber-900 dark:text-amber-200 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <AlertTriangle size={18} className="text-amber-600" />
              <span>
                <strong>Human-in-the-Loop Verification Queue:</strong> Borderline algorithmic predictions (80%–94%)
                and superior metallurgical upgrades requiring materials engineer sign-off.
              </span>
            </div>
            <span className="font-bold">{hitlList.length} Pending Review</span>
          </div>

          {hitlList.length === 0 ? (
            <Card className="p-12 text-center text-slate-500 font-mono text-sm">
              <CheckCircle2 size={32} className="mx-auto text-emerald-500 mb-2" />
              <p className="font-bold text-slate-800 dark:text-slate-200">HITL Triage Queue is Clear</p>
              <p className="text-xs text-slate-400 mt-1">All algorithmic predictions and MTC certifications have been validated.</p>
            </Card>
          ) : (
            hitlList.map((caseItem) => (
              <Card
                key={caseItem.id}
                className="p-5 border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 space-y-4"
              >
                <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
                  <div className="flex items-center gap-2.5">
                    <span className="font-mono font-bold text-sm text-slate-900 dark:text-slate-100">
                      Triage Item: {caseItem.sourceSku}
                    </span>
                    <span className="px-2 py-0.5 bg-amber-100 dark:bg-amber-950/60 text-amber-800 dark:text-amber-300 text-[10px] font-mono font-bold rounded">
                      Confidence: {caseItem.extractedMTC.confidence}%
                    </span>
                  </div>
                  <span className="text-xs font-mono text-slate-400">
                    Source Document: {caseItem.extractedMTC.filename}
                  </span>
                </div>

                {/* Diff Visualizer Columns */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Left: Plant Catalog Master */}
                  <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/50 space-y-2">
                    <div className="flex items-center justify-between text-xs font-mono text-slate-500 font-bold">
                      <span>PLANT MATERIAL MASTER (PHYSICAL PART)</span>
                      <span className="text-[10px] bg-slate-200 dark:bg-slate-700 px-1.5 py-0.5 rounded">ORIGINAL</span>
                    </div>
                    <p className="text-sm font-bold font-mono text-slate-900 dark:text-slate-100">
                      {caseItem.physicalPart.description}
                    </p>
                    <div className="grid grid-cols-2 gap-2 text-xs font-mono pt-2 border-t border-slate-200 dark:border-slate-700">
                      <div>
                        <span className="text-slate-400 block text-[10px]">GRADE:</span>
                        <span className="font-semibold">{caseItem.physicalPart.metallurgy}</span>
                      </div>
                      <div>
                        <span className="text-slate-400 block text-[10px]">PRESSURE CLASS:</span>
                        <span className="font-semibold">{caseItem.physicalPart.rating}</span>
                      </div>
                      <div>
                        <span className="text-slate-400 block text-[10px]">FACING:</span>
                        <span className="font-semibold">{caseItem.physicalPart.facing}</span>
                      </div>
                      <div>
                        <span className="text-slate-400 block text-[10px]">SCHEDULE:</span>
                        <span className="font-semibold">{caseItem.physicalPart.schedule}</span>
                      </div>
                    </div>
                  </div>

                  {/* Right: Extracted MTC Certificate Candidate */}
                  <div className="p-4 rounded-xl border border-emerald-300 dark:border-emerald-800 bg-emerald-50/40 dark:bg-emerald-950/20 space-y-2">
                    <div className="flex items-center justify-between text-xs font-mono text-emerald-800 dark:text-emerald-300 font-bold">
                      <span>EXTRACTED MTC INTELLIGENCE (CANDIDATE)</span>
                      <span className="text-[10px] bg-emerald-200 dark:bg-emerald-900 px-1.5 py-0.5 rounded font-mono">
                        EN 10204 3.1
                      </span>
                    </div>
                    <p className="text-sm font-bold font-mono text-slate-900 dark:text-slate-100">
                      {caseItem.extractedMTC.description}
                    </p>
                    <div className="grid grid-cols-2 gap-2 text-xs font-mono pt-2 border-t border-emerald-200 dark:border-emerald-800">
                      <div>
                        <span className="text-slate-400 block text-[10px]">GRADE:</span>
                        <span className="font-semibold text-emerald-700 dark:text-emerald-300">
                          {caseItem.extractedMTC.metallurgy}
                        </span>
                      </div>
                      <div>
                        <span className="text-slate-400 block text-[10px]">PRESSURE CLASS:</span>
                        <span className="font-semibold">{caseItem.extractedMTC.rating}</span>
                      </div>
                      <div>
                        <span className="text-slate-400 block text-[10px]">FACING:</span>
                        <span className="font-semibold">{caseItem.extractedMTC.facing}</span>
                      </div>
                      <div>
                        <span className="text-slate-400 block text-[10px]">SCHEDULE:</span>
                        <span className="font-semibold">{caseItem.extractedMTC.schedule}</span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Algorithmic Variance Justification */}
                <div className="p-3 bg-slate-50 dark:bg-slate-800 rounded-lg text-xs font-mono text-slate-600 dark:text-slate-300 flex items-start gap-2">
                  <CheckCircle2 size={16} className="text-emerald-500 mt-0.5 shrink-0" />
                  <div>
                    <span className="font-bold">Automated Safety Rule Evaluation: </span>
                    <span>{caseItem.extractedMTC.varianceReason}</span>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex justify-end gap-3 pt-2">
                  <button
                    onClick={() => handleRejectHITL(caseItem.id)}
                    className="px-4 py-2 border border-rose-300 dark:border-rose-800 text-rose-600 dark:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/40 rounded-lg text-xs font-mono font-bold transition-colors flex items-center gap-1.5"
                  >
                    <XCircle size={14} /> Reject Prediction
                  </button>

                  <button
                    onClick={() => handleApproveHITL(caseItem.id)}
                    className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-mono font-bold transition-all shadow-xs flex items-center gap-1.5"
                  >
                    <Check size={14} /> Approve & Merge into Ledger
                  </button>
                </div>
              </Card>
            ))
          )}
        </div>
      ) : (
        /* Standard Catalog Table View */
        <div className="space-y-4">
          {/* Table Filters & Search */}
          <div className="flex flex-col sm:flex-row gap-3 items-center justify-between bg-white dark:bg-slate-900 p-3 rounded-xl border border-slate-200 dark:border-slate-800">
            <div className="relative w-full sm:w-80">
              <Search className="absolute left-3 top-2.5 text-slate-400" size={16} />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Filter by SKU, description, metallurgy..."
                className="w-full pl-9 pr-3 py-1.5 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-xs font-mono text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-1 focus:ring-emerald-500"
              />
            </div>

            <div className="flex items-center gap-2 w-full sm:w-auto">
              <span className="text-xs font-mono text-slate-400 flex items-center gap-1">
                <Filter size={12} /> Category:
              </span>
              <select
                value={categoryFilter}
                onChange={(e) => setCategoryFilter(e.target.value)}
                className="bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg px-2.5 py-1.5 text-xs font-mono text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-1 focus:ring-emerald-500"
              >
                <option value="ALL">All Categories</option>
                <option value="FLANGE">Flanges</option>
                <option value="VALVE">Valves</option>
                <option value="PIPE">Piping</option>
                <option value="FASTENER">Fasteners</option>
                <option value="GASKET">Gaskets</option>
                <option value="ROTATING">Rotating</option>
              </select>
            </div>
          </div>

          {/* High-Density Ledger Table */}
          <Card className="p-0 overflow-hidden border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm">
            <div className="overflow-x-auto">
              <table className="w-full text-left compact-table border-collapse">
                <thead className="bg-slate-50 dark:bg-slate-800/80 text-slate-500 dark:text-slate-400 border-b border-slate-200 dark:border-slate-800 font-mono text-[11px] uppercase tracking-wider">
                  <tr>
                    <th className="p-3">SKU Code</th>
                    <th className="p-3">Material Description</th>
                    <th className="p-3">Metallurgy & Grade</th>
                    <th className="p-3">Rating & Size</th>
                    <th className="p-3 text-right">Stock Qty</th>
                    <th className="p-3">Status</th>
                    <th className="p-3 text-right">Surplus Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800/80 text-xs font-mono">
                  {filteredItems.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="p-8 text-center text-slate-400">
                        No inventory items matching filter criteria.
                      </td>
                    </tr>
                  ) : (
                    filteredItems.map((item) => (
                      <tr
                        key={item.id}
                        className="hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors"
                      >
                        <td className="p-3 font-bold text-slate-900 dark:text-slate-100">
                          {item.sku_code}
                          <span className="block text-[10px] text-slate-400 font-normal">
                            Heat: {item.heat_no}
                          </span>
                        </td>
                        <td className="p-3 text-slate-800 dark:text-slate-200 font-sans font-medium max-w-xs">
                          {item.description}
                          <span className="block font-mono text-[10px] text-slate-400">
                            Idle duration: {item.days_idle} days
                          </span>
                        </td>
                        <td className="p-3 text-slate-700 dark:text-slate-300 font-semibold">
                          {item.metallurgy}
                        </td>
                        <td className="p-3 text-slate-600 dark:text-slate-400">
                          {item.pressure_class} · {item.size}
                        </td>
                        <td className="p-3 text-right font-bold text-slate-900 dark:text-slate-100">
                          {item.quantity} {item.unit}
                        </td>
                        <td className="p-3">
                          <span
                            className={`px-2 py-0.5 text-[10px] font-mono font-bold rounded-full border ${
                              item.status === 'IDLE_SURPLUS'
                                ? 'bg-emerald-50 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-300 border-emerald-200 dark:border-emerald-800'
                                : item.status === 'IN_STORAGE'
                                ? 'bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border-slate-300 dark:border-slate-700'
                                : item.status === 'TO_BE_CONSUMED'
                                ? 'bg-blue-50 dark:bg-blue-950/60 text-blue-700 dark:text-blue-300 border-blue-200 dark:border-blue-800'
                                : 'bg-gray-100 text-gray-700 border-gray-300'
                            }`}
                          >
                            {item.status.replace('_', ' ')}
                          </span>
                        </td>
                        <td className="p-3 text-right">
                          <button
                            onClick={() => handleToggleSurplus(item.id)}
                            className={`px-2.5 py-1 rounded text-[11px] font-mono font-bold transition-colors ${
                              item.status === 'IDLE_SURPLUS'
                                ? 'bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300'
                                : 'bg-emerald-600 hover:bg-emerald-500 text-white'
                            }`}
                          >
                            {item.status === 'IDLE_SURPLUS' ? 'Un-broadcast' : 'Broadcast'}
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
}
