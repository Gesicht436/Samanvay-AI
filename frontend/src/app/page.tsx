"use client";

import React, { useState } from 'react';
import Link from 'next/link';
import { Card, KpiCard, StatusBadge } from '@/components/ui';
import {
  Database,
  ShieldCheck,
  CheckCircle2,
  Clock,
  Leaf,
  Truck,
  AlertTriangle,
  ArrowRight,
  Upload,
  Search,
  Building2,
  Radio,
  FileCheck2,
  ExternalLink,
} from 'lucide-react';
import { CPSE_DEPOTS, CPSEDepot } from '@/lib/constants';

interface ConsignmentItem {
  id: string;
  from: string;
  to: string;
  part: string;
  urgency: 'CRITICAL_EMERGENCY' | 'EXPEDITE' | 'STANDARD';
  status: string;
  eta: string;
  distanceKm: number;
}

const ACTIVE_CONSIGNMENTS: ConsignmentItem[] = [
  {
    id: 'REQ-99201',
    from: 'BPCL Mumbai',
    to: 'ONGC Uran',
    part: '2x CS A105 WN Flanges 4" 300#',
    urgency: 'CRITICAL_EMERGENCY',
    status: 'CISF CLEARANCE GRANTED',
    eta: 'Today 19:30 IST',
    distanceKm: 120,
  },
  {
    id: 'REQ-55102',
    from: 'IOCL Panipat',
    to: 'HPCL Visakh',
    part: '1x Gas Turbine Rotor Forging',
    urgency: 'EXPEDITE',
    status: 'IN TRANSIT (NH-44 CORRIDOR)',
    eta: 'Tomorrow 08:00 IST',
    distanceKm: 1480,
  },
  {
    id: 'REQ-44019',
    from: 'GAIL Pata',
    to: 'IOCL Panipat',
    part: '8x ASTM A182 F316L Globe Valves 2"',
    urgency: 'STANDARD',
    status: 'DISPATCH SCHEDULED',
    eta: '20-FEB 14:00 IST',
    distanceKm: 410,
  },
];

export default function ExecutiveCommandCenter() {
  const [selectedDepot, setSelectedDepot] = useState<CPSEDepot>(CPSE_DEPOTS[0]);
  const totalValueCr = CPSE_DEPOTS.reduce((acc, d) => acc + d.unlockedValueCr, 0);
  const totalItems = CPSE_DEPOTS.reduce((acc, d) => acc + d.itemsCount, 0);

  return (
    <div className="flex flex-col space-y-6 max-w-[1600px] mx-auto pb-10">
      {/* Top Banner & Context */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 bg-slate-900 border border-slate-800 p-6 rounded-2xl text-white relative overflow-hidden shadow-sm">
        {/* Subtle background glow */}
        <div className="absolute -right-10 -top-10 w-96 h-96 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="space-y-1.5 z-10">
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 rounded-full text-xs font-mono font-semibold flex items-center gap-1.5">
              <Radio size={12} className="animate-pulse text-emerald-400" />
              SOVEREIGN MESH OPERATIONAL
            </span>
            <span className="text-xs font-mono text-slate-400">Node ID: MOPNG-NODE-01</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white font-mono">
            Inter-CPSE Strategic Surplus Command Center
          </h1>
          <p className="text-xs font-mono text-slate-300 max-w-2xl">
            Autonomous material interoperability and zero-tolerance cross-CPSE sharing for Indian Public Sector Undertakings.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2.5 z-10">
          <Link
            href="/upload"
            className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-mono font-bold flex items-center gap-2 transition-all shadow-xs"
          >
            <Upload size={14} /> Intake MTC Certificate
          </Link>
          <Link
            href="/discover"
            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 rounded-lg text-xs font-mono font-bold flex items-center gap-2 transition-all shadow-xs"
          >
            <Search size={14} /> Search Surplus Parts
          </Link>
        </div>
      </div>

      {/* 1. Executive KPI Metrics Strip */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        <KpiCard
          title="Dead Capital Unlocked"
          value={`₹${totalValueCr.toFixed(1)} Cr`}
          unit="Book Value"
          delta="+14.2%"
          isPositive={true}
          icon={Database}
        />
        <KpiCard
          title="Breakdowns Averted"
          value="18"
          unit="Incidents < 24h"
          delta="100% SLA"
          isPositive={true}
          icon={ShieldCheck}
        />
        <KpiCard
          title="Safety Verification"
          value="94.8%"
          unit="Tier 1 Compatible"
          delta="21 Modules"
          isPositive={true}
          icon={CheckCircle2}
        />
        <KpiCard
          title="Turnaround Time"
          value="16.4"
          unit="Hours Avg."
          delta="-89% vs Baseline"
          isPositive={true}
          icon={Clock}
        />
        <KpiCard
          title="CO₂ Transport Saved"
          value="32.4"
          unit="Metric Tons"
          delta="Geodesic Routing"
          isPositive={true}
          icon={Leaf}
        />
      </div>

      {/* 2. Main Operational Deck: Logistics Radar + Emergency Requisitions */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Geographic Inter-CPSE Transit Map (7 Cols) */}
        <Card className="lg:col-span-7 flex flex-col p-5 border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900">
          <div className="flex items-center justify-between pb-4 border-b border-slate-100 dark:border-slate-800">
            <div>
              <h2 className="text-sm font-mono font-bold uppercase tracking-wider text-slate-900 dark:text-slate-100 flex items-center gap-2">
                <Truck size={16} className="text-emerald-500" />
                Inter-CPSE Active Logistics Corridors
              </h2>
              <p className="text-xs font-mono text-slate-500 mt-0.5">
                Real-time transit tracking across {CPSE_DEPOTS.length} sovereign PSU depots
              </p>
            </div>
            <span className="text-[11px] font-mono bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 px-2 py-1 rounded">
              {ACTIVE_CONSIGNMENTS.length} Active Corridors
            </span>
          </div>

          {/* Interactive Geographic Radar Diagram */}
          <div className="relative my-4 w-full h-[340px] bg-slate-950 rounded-xl border border-slate-800 overflow-hidden flex items-center justify-center p-4">
            {/* SVG Grid Background */}
            <svg className="absolute inset-0 w-full h-full opacity-20 pointer-events-none" xmlns="http://www.w3.org/2000/svg">
              <defs>
                <pattern id="grid" width="30" height="30" patternUnits="userSpaceOnUse">
                  <path d="M 30 0 L 0 0 0 30" fill="none" stroke="#334155" strokeWidth="0.8" />
                </pattern>
              </defs>
              <rect width="100%" height="100%" fill="url(#grid)" />
            </svg>

            {/* Simulated Indian Subcontinent Geo Radar */}
            <svg viewBox="0 0 100 100" className="w-full h-full max-h-[320px] drop-shadow-md">
              {/* Radar Rings */}
              <circle cx="50" cy="50" r="25" fill="none" stroke="#1e293b" strokeWidth="0.5" strokeDasharray="2 2" />
              <circle cx="50" cy="50" r="42" fill="none" stroke="#1e293b" strokeWidth="0.5" strokeDasharray="2 2" />

              {/* Animated Transit Lines */}
              {/* Panipat (38,25) to Visakh (68,62) */}
              <path
                d="M 38 25 Q 56 42 68 62"
                fill="none"
                stroke="#10b981"
                strokeWidth="1.2"
                strokeDasharray="3 2"
                className="animate-pulse"
              />
              {/* Mumbai (25,58) to Uran (27,60) */}
              <path
                d="M 25 58 L 27 60"
                fill="none"
                stroke="#f59e0b"
                strokeWidth="2"
              />
              {/* GAIL Pata (48,35) to Panipat (38,25) */}
              <path
                d="M 48 35 L 38 25"
                fill="none"
                stroke="#3b82f6"
                strokeWidth="1"
                strokeDasharray="2 2"
              />

              {/* Transit Particles */}
              <circle cx="53" cy="43" r="1.5" fill="#34d399" className="animate-ping" />
              <circle cx="26" cy="59" r="1.5" fill="#fbbf24" className="animate-ping" />

              {/* Depot Nodes */}
              {CPSE_DEPOTS.map((depot) => {
                const isSelected = selectedDepot.id === depot.id;
                return (
                  <g
                    key={depot.id}
                    className="cursor-pointer transition-transform hover:scale-110"
                    onClick={() => setSelectedDepot(depot)}
                  >
                    <circle
                      cx={depot.coords.x}
                      cy={depot.coords.y}
                      r={isSelected ? '3.5' : '2.5'}
                      fill={
                        depot.cpse === 'IOCL'
                          ? '#10b981'
                          : depot.cpse === 'ONGC'
                          ? '#f59e0b'
                          : depot.cpse === 'BPCL'
                          ? '#3b82f6'
                          : depot.cpse === 'HPCL'
                          ? '#ec4899'
                          : '#8b5cf6'
                      }
                      stroke="#ffffff"
                      strokeWidth="0.8"
                    />
                    <text
                      x={depot.coords.x + 3}
                      y={depot.coords.y + 1}
                      fill="#e2e8f0"
                      fontSize="3.2"
                      fontFamily="monospace"
                      fontWeight="bold"
                    >
                      {depot.cpse} ({depot.city})
                    </text>
                  </g>
                );
              })}
            </svg>

            {/* Selected Depot Inspection Floating Card */}
            <div className="absolute bottom-3 left-3 bg-slate-900/90 backdrop-blur-md border border-slate-700/80 p-3 rounded-lg text-xs font-mono max-w-[260px] text-slate-200">
              <div className="flex items-center gap-1.5 text-emerald-400 font-bold mb-1">
                <Building2 size={14} />
                <span>{selectedDepot.name}</span>
              </div>
              <div className="text-[11px] text-slate-400 space-y-0.5">
                <div className="flex justify-between">
                  <span>Inventory Catalog:</span>
                  <span className="font-bold text-white">{selectedDepot.itemsCount} Items</span>
                </div>
                <div className="flex justify-between">
                  <span>Unlocked Capital:</span>
                  <span className="font-bold text-emerald-400">₹{selectedDepot.unlockedValueCr} Cr</span>
                </div>
                <div className="flex justify-between">
                  <span>Location:</span>
                  <span className="text-slate-300">{selectedDepot.city}, {selectedDepot.state}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Quick Depot Selector Pill Bar */}
          <div className="flex flex-wrap gap-2 pt-2">
            {CPSE_DEPOTS.map((d) => (
              <button
                key={d.id}
                onClick={() => setSelectedDepot(d)}
                className={`px-2.5 py-1 rounded text-xs font-mono transition-all border ${
                  selectedDepot.id === d.id
                    ? 'bg-slate-900 dark:bg-slate-100 text-white dark:text-slate-900 border-slate-900 dark:border-slate-100 font-bold'
                    : 'bg-slate-50 dark:bg-slate-800 text-slate-600 dark:text-slate-400 border-slate-200 dark:border-slate-700 hover:border-slate-400'
                }`}
              >
                {d.cpse} · {d.city}
              </button>
            ))}
          </div>
        </Card>

        {/* Right Column: Emergency Breakdown Radar & Critical Requisitions (5 Cols) */}
        <Card className="lg:col-span-5 flex flex-col p-5 border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900">
          <div className="flex items-center justify-between pb-4 border-b border-slate-100 dark:border-slate-800">
            <div>
              <h2 className="text-sm font-mono font-bold uppercase tracking-wider text-slate-900 dark:text-slate-100 flex items-center gap-2">
                <AlertTriangle size={16} className="text-amber-500" />
                Emergency Breakdown Radar
              </h2>
              <p className="text-xs font-mono text-slate-500 mt-0.5">
                Automated compatibility matching for critical requisitions
              </p>
            </div>
            <Link
              href="/requests"
              className="text-xs font-mono text-emerald-600 dark:text-emerald-400 hover:underline flex items-center gap-1 font-semibold"
            >
              View Hub <ArrowRight size={12} />
            </Link>
          </div>

          <div className="flex-1 overflow-y-auto space-y-3 py-3">
            {ACTIVE_CONSIGNMENTS.map((consign) => (
              <div
                key={consign.id}
                className={`p-3.5 rounded-xl border transition-all ${
                  consign.urgency === 'CRITICAL_EMERGENCY'
                    ? 'border-amber-400/80 bg-amber-50/40 dark:bg-amber-950/20'
                    : 'border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/40'
                }`}
              >
                <div className="flex items-center justify-between mb-1.5">
                  <div className="flex items-center gap-2">
                    <span className="font-mono font-bold text-xs text-slate-900 dark:text-slate-100">
                      {consign.id}
                    </span>
                    <span
                      className={`px-2 py-0.5 text-[10px] font-mono font-bold rounded-full ${
                        consign.urgency === 'CRITICAL_EMERGENCY'
                          ? 'bg-rose-100 text-rose-800 dark:bg-rose-950/70 dark:text-rose-300'
                          : 'bg-blue-100 text-blue-800 dark:bg-blue-950/70 dark:text-blue-300'
                      }`}
                    >
                      {consign.urgency.replace('_', ' ')}
                    </span>
                  </div>
                  <span className="text-[11px] font-mono text-slate-500">{consign.distanceKm} km</span>
                </div>

                <p className="text-xs font-bold text-slate-800 dark:text-slate-200 mb-1">
                  {consign.part}
                </p>

                <div className="flex items-center justify-between text-xs font-mono text-slate-500 mt-2 pt-2 border-t border-slate-200 dark:border-slate-800">
                  <span>
                    {consign.from} &rarr; {consign.to}
                  </span>
                  <span className="font-semibold text-emerald-600 dark:text-emerald-400">
                    ETA: {consign.eta}
                  </span>
                </div>

                <div className="mt-3 flex gap-2">
                  <Link
                    href={`/requests/${consign.id}`}
                    className="flex-1 py-1.5 bg-slate-900 hover:bg-slate-800 dark:bg-emerald-600 dark:hover:bg-emerald-700 text-white rounded text-xs font-mono font-semibold text-center transition-colors"
                  >
                    Track & Gate Pass
                  </Link>
                </div>
              </div>
            ))}
          </div>

          {/* HITL Triage Alert Callout */}
          <div className="mt-2 p-3 bg-slate-100 dark:bg-slate-800/80 rounded-xl border border-slate-200 dark:border-slate-700 flex items-center justify-between text-xs font-mono">
            <div className="flex items-center gap-2 text-slate-700 dark:text-slate-300">
              <FileCheck2 size={16} className="text-amber-500" />
              <span>1 Out-of-Spec MTC in HITL Triage Queue</span>
            </div>
            <Link
              href="/inventory"
              className="font-bold text-emerald-600 dark:text-emerald-400 hover:underline"
            >
              Review Queue &rarr;
            </Link>
          </div>
        </Card>
      </div>

      {/* 3. Bottom Row: Plant Inventory Breakdown & Audit Trail Preview */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Plant Inventory Breakdown (6 Cols) */}
        <Card className="lg:col-span-6 p-5 border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800 mb-4">
            <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-800 dark:text-slate-200">
              Cross-CPSE Surplus Stock Distribution
            </h3>
            <span className="text-xs font-mono text-slate-500">{totalItems} Cataloged Items</span>
          </div>

          <div className="space-y-3">
            {CPSE_DEPOTS.map((d) => {
              const pct = ((d.itemsCount / totalItems) * 100).toFixed(1);
              return (
                <div key={d.id} className="space-y-1 text-xs font-mono">
                  <div className="flex justify-between text-slate-700 dark:text-slate-300">
                    <span className="font-semibold">{d.name}</span>
                    <span className="text-slate-500">
                      {d.itemsCount} items (₹{d.unlockedValueCr} Cr) · {pct}%
                    </span>
                  </div>
                  <div className="w-full bg-slate-100 dark:bg-slate-800 h-2 rounded-full overflow-hidden">
                    <div
                      style={{ width: `${pct}%` }}
                      className={`h-full rounded-full ${
                        d.cpse === 'IOCL'
                          ? 'bg-emerald-500'
                          : d.cpse === 'BPCL'
                          ? 'bg-blue-500'
                          : d.cpse === 'HPCL'
                          ? 'bg-pink-500'
                          : d.cpse === 'ONGC'
                          ? 'bg-amber-500'
                          : 'bg-purple-500'
                      }`}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </Card>

        {/* Sovereign Audit Trail Preview (6 Cols) */}
        <Card className="lg:col-span-6 p-5 border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800 mb-4">
              <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-800 dark:text-slate-200 flex items-center gap-1.5">
                <ShieldCheck size={16} className="text-emerald-500" />
                Sovereign Cryptographic Audit Stream
              </h3>
              <Link
                href="/audit"
                className="text-xs font-mono text-emerald-600 dark:text-emerald-400 hover:underline flex items-center gap-1"
              >
                Full Ledger <ExternalLink size={12} />
              </Link>
            </div>

            <div className="space-y-2.5 font-mono text-xs">
              <div className="p-2.5 rounded-lg bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-800 flex items-center justify-between">
                <div className="space-y-0.5">
                  <div className="flex items-center gap-2">
                    <span className="px-1.5 py-0.5 bg-emerald-100 dark:bg-emerald-950/80 text-emerald-800 dark:text-emerald-300 text-[10px] font-bold rounded">
                      LEDGER_COMMIT
                    </span>
                    <span className="font-bold text-slate-800 dark:text-slate-200">MTC-2026-5516</span>
                  </div>
                  <p className="text-[11px] text-slate-500">Actor: system_ocr · IOCL Panipat</p>
                </div>
                <span className="text-[10px] text-slate-400 truncate max-w-[140px]" title="SHA-256 seal">
                  sha256:e3b0c44298fc...
                </span>
              </div>

              <div className="p-2.5 rounded-lg bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-800 flex items-center justify-between">
                <div className="space-y-0.5">
                  <div className="flex items-center gap-2">
                    <span className="px-1.5 py-0.5 bg-blue-100 dark:bg-blue-950/80 text-blue-800 dark:text-blue-300 text-[10px] font-bold rounded">
                      CISF_GATE_PASS
                    </span>
                    <span className="font-bold text-slate-800 dark:text-slate-200">REQ-55102</span>
                  </div>
                  <p className="text-[11px] text-slate-500">Actor: cisf_in_charge · Visakh Gate #4</p>
                </div>
                <span className="text-[10px] text-slate-400 truncate max-w-[140px]" title="SHA-256 seal">
                  sha256:8a91a92120e2...
                </span>
              </div>
            </div>
          </div>

          <div className="pt-4 mt-2 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-xs font-mono text-slate-500">
            <span>Merkle Tree Root: <span className="text-emerald-500 font-bold">VALID</span></span>
            <span>Block Height: #1,842</span>
          </div>
        </Card>
      </div>
    </div>
  );
}
