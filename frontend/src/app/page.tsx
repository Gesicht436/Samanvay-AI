"use client";

import React from 'react';
import Link from 'next/link';
import { useAuth } from '@/context/AuthContext';
import {
  Shield,
  Search,
  Cpu,
  Layers,
  Building2,
  Lock,
  ArrowRight,
  CheckCircle2,
  AlertTriangle,
  QrCode,
  FileCheck2,
  UserCheck,
  UserPlus,
  KeyRound,
  FileSpreadsheet,
  Globe2,
} from 'lucide-react';

const CPSE_PARTNERS = [
  { name: 'Oil India Limited', code: 'OIL', hub: 'Duliajan & Field HQs' },
  { name: 'Indian Oil Corporation', code: 'IOCL', hub: 'Panipat & Guwahati' },
  { name: 'Oil & Natural Gas Corp', code: 'ONGC', hub: 'Ankleshwar & Nazira' },
  { name: 'Bharat Petroleum', code: 'BPCL', hub: 'Mumbai & Kochi' },
  { name: 'Hindustan Petroleum', code: 'HPCL', hub: 'Visakh & Mumbai' },
  { name: 'GAIL (India) Limited', code: 'GAIL', hub: 'Pata & HVJ Pipeline' },
  { name: 'Numaligarh Refinery', code: 'NRL', hub: 'Numaligarh (Assam)' },
];

const PILLARS = [
  {
    icon: Cpu,
    title: 'Dual-Path MTC Vision & Chemistry',
    desc: 'Automated extraction of Mill Test Certificates using PyTorch GPU OCR. Validates ladle chemistry assays, IIW carbon equivalent weldability (CE ≤ 0.43%), and PREN pitting indices.',
    tag: 'CUDA Accelerated',
  },
  {
    icon: Layers,
    title: '21 Codified Mechanical Safety Gates',
    desc: 'Zero-tolerance deterministic hard vetoes across ASME B16.5, B16.34, API 6D, API 526, and NACE MR0175 sour service. Never recommends an unsafe spare for critical hydrocarbon duty.',
    tag: 'Zero-Tolerance Veto',
  },
  {
    icon: Globe2,
    title: 'GIS Haversine Logistics Topology',
    desc: 'Real-time road transit matrix across 19 CPSE field depots and refineries incorporating a 1.28× road tortuosity factor to identify the fastest mutual-aid delivery route.',
    tag: '19 Hub Network',
  },
  {
    icon: Shield,
    title: 'Commercial Privacy & SHA-256 Ledger',
    desc: 'Commercial price masking prevents anti-competitive pricing leakage between PSUs. All inter-CPSE loan requisitions and status changes are cryptographically sealed into an immutable Merkle chain.',
    tag: 'Merkle Audit Trail',
  },
];

const PERSONAS = [
  {
    role: 'Site Engineer',
    user: 'engineer_oil',
    cpse: 'OIL',
    desc: 'Discovers interchangeable spares in sister refineries, checks 21 safety veto gates, and submits emergency loan requisitions to prevent plant trips.',
  },
  {
    role: 'Materials Manager',
    user: 'stores_oil',
    cpse: 'OIL',
    desc: 'Monitors warehouse idle stock countdowns (>180 days), broadcasts surplus spares into the sovereign mesh, and authorizes inter-CPSE loans.',
  },
  {
    role: 'Technical Authority',
    user: 'tech_authority',
    cpse: 'OIL',
    desc: 'QA-QC Chief Metallurgist arbitrating 80%–94% tolerance triage disputes, validating ASTM A105 vs IS 2062 equivalence, and reviewing ladle assays.',
  },
  {
    role: 'CISF Security Officer',
    user: 'cisf_officer',
    cpse: 'OIL',
    desc: 'Scans offline air-gapped SVG QR bit-matrices at refinery security gates, verifying truck registration, driver credentials, and stamping gate passes.',
  },
  {
    role: 'Vigilance Auditor',
    user: 'auditor',
    cpse: 'MoPNG',
    desc: 'Validates cryptographic SHA-256 continuity from Genesis block to latest transaction, ensures statutory compliance, and exports CAG audit logs.',
  },
  {
    role: 'Super Administrator',
    user: 'admin',
    cpse: 'MoPNG',
    desc: 'Maintains national inter-CPSE mesh parameters, oversees connected depots, and manages sovereign access policies.',
  },
];

export default function LandingPage() {
  const { user, isAuthenticated } = useAuth();

  return (
    <div className="space-y-16 pb-16">
      {/* Hero Section */}
      <section className="relative overflow-hidden pt-12 pb-16 border-b border-slate-200 dark:border-slate-800 bg-gradient-to-b from-white via-slate-50/50 to-slate-100/40 dark:from-slate-900 dark:via-slate-900/80 dark:to-slate-950">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 text-center space-y-6">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-100 dark:bg-emerald-950/60 border border-emerald-300 dark:border-emerald-700 text-xs font-mono font-semibold text-emerald-800 dark:text-emerald-300">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            <span>SIH26099 · MINISTRY OF PETROLEUM & NATURAL GAS</span>
          </div>

          <h1 className="text-3xl sm:text-5xl font-extrabold tracking-tight text-slate-900 dark:text-white max-w-4xl mx-auto leading-tight sm:leading-tight">
            Sovereign Inter-CPSE Spare Parts & Material Sharing Mesh
          </h1>

          <p className="text-sm sm:text-base text-slate-600 dark:text-slate-300 max-w-3xl mx-auto leading-relaxed">
            Eliminating <strong className="text-slate-900 dark:text-white">₹12,000+ Crore</strong> in idle PSU maintenance spare inventory and preventing <strong className="text-slate-900 dark:text-white">₹5–20 Crore/day</strong> refinery trip losses through an automated, sovereign, cross-CPSE mutual aid spare mesh.
          </p>

          {/* User Status or CTA Buttons */}
          <div className="pt-4 flex flex-wrap items-center justify-center gap-4">
            {isAuthenticated && user ? (
              <div className="p-4 bg-white dark:bg-slate-800 border border-emerald-500 dark:border-emerald-600 rounded-xl shadow-xs flex flex-col sm:flex-row items-center gap-4">
                <div className="text-left">
                  <div className="flex items-center gap-2">
                    <UserCheck className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
                    <p className="font-bold text-xs text-slate-900 dark:text-white">
                      Logged in as {user.full_name}
                    </p>
                    <span className="px-1.5 py-0.5 text-[10px] font-mono bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300 rounded">
                      {user.cpse} · {user.role.replace('_', ' ')}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-500 font-mono mt-0.5">
                    Assigned Depot: {user.depot_id}
                  </p>
                </div>
                <Link
                  href="/dashboard"
                  className="py-2.5 px-5 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-xs rounded-lg transition-all shadow-xs flex items-center gap-2 shrink-0"
                >
                  <span>Enter My Authorized Workspace</span>
                  <ArrowRight size={14} />
                </Link>
              </div>
            ) : (
              <>
                <Link
                  href="/login"
                  className="py-3 px-6 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-xs rounded-lg transition-all shadow-xs flex items-center gap-2"
                >
                  <KeyRound size={15} />
                  <span>Sign In to Sovereign Node</span>
                  <ArrowRight size={14} />
                </Link>

                <Link
                  href="/signup"
                  className="py-3 px-6 bg-white dark:bg-slate-800 hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-800 dark:text-slate-100 font-semibold text-xs rounded-lg border border-slate-300 dark:border-slate-700 transition-all flex items-center gap-2"
                >
                  <UserPlus size={15} />
                  <span>Register CPSE Officer</span>
                </Link>
              </>
            )}
          </div>
        </div>
      </section>

      {/* Live Impact Counters */}
      <section className="max-w-6xl mx-auto px-4 sm:px-6">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="p-5 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl text-center shadow-xs">
            <p className="text-2xl sm:text-3xl font-extrabold text-emerald-600 dark:text-emerald-400 font-mono">
              ₹12,000+ Cr
            </p>
            <p className="text-xs font-semibold text-slate-800 dark:text-slate-200 mt-1">
              Idle Spares Addressable
            </p>
            <p className="text-[11px] text-slate-500 mt-0.5">Across Indian Oil & Gas PSUs</p>
          </div>

          <div className="p-5 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl text-center shadow-xs">
            <p className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white font-mono">
              19 Hubs
            </p>
            <p className="text-xs font-semibold text-slate-800 dark:text-slate-200 mt-1">
              Connected Depots & Refineries
            </p>
            <p className="text-[11px] text-slate-500 mt-0.5">1.28× Road Tortuosity Haversine</p>
          </div>

          <div className="p-5 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl text-center shadow-xs">
            <p className="text-2xl sm:text-3xl font-extrabold text-emerald-600 dark:text-emerald-400 font-mono">
              21 Gates
            </p>
            <p className="text-xs font-semibold text-slate-800 dark:text-slate-200 mt-1">
              Deterministic Safety Vetoes
            </p>
            <p className="text-[11px] text-slate-500 mt-0.5">ASME · ASTM · API · NACE</p>
          </div>

          <div className="p-5 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl text-center shadow-xs">
            <p className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white font-mono">
              SHA-256
            </p>
            <p className="text-xs font-semibold text-slate-800 dark:text-slate-200 mt-1">
              Sovereign Merkle Ledger
            </p>
            <p className="text-[11px] text-slate-500 mt-0.5">Tamper-Evident CAG Audit Trail</p>
          </div>
        </div>
      </section>

      {/* Core Architectural Pillars */}
      <section id="safety-gates" className="max-w-6xl mx-auto px-4 sm:px-6 space-y-6">
        <div className="text-center space-y-2">
          <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            Core Engineering & Safety Pillars
          </h2>
          <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-400 max-w-2xl mx-auto">
            Combining deterministic physics, GPU machine learning, and sovereign cryptographic ledgers.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {PILLARS.map((p) => {
            const Icon = p.icon;
            return (
              <div
                key={p.title}
                className="p-6 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl shadow-xs space-y-3"
              >
                <div className="flex items-center justify-between">
                  <div className="w-10 h-10 rounded-lg bg-slate-100 dark:bg-slate-800 flex items-center justify-center text-emerald-600 dark:text-emerald-400">
                    <Icon size={20} />
                  </div>
                  <span className="px-2 py-0.5 text-[10px] font-mono font-semibold bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 rounded">
                    {p.tag}
                  </span>
                </div>
                <h3 className="font-bold text-sm text-slate-900 dark:text-white">
                  {p.title}
                </h3>
                <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                  {p.desc}
                </p>
              </div>
            );
          })}
        </div>
      </section>

      {/* Role-Based Sovereign Access Personas */}
      <section id="mission" className="max-w-6xl mx-auto px-4 sm:px-6 space-y-6">
        <div className="text-center space-y-2">
          <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            Segregated Sovereign Operational Roles
          </h2>
          <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-400 max-w-2xl mx-auto">
            Dynamic workspaces configured with strict segregation of duties for plant reliability, materials management, and statutory audit.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {PERSONAS.map((p) => (
            <div
              key={p.role}
              className="p-5 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl shadow-xs flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="font-bold text-xs text-slate-900 dark:text-white">
                    {p.role}
                  </span>
                  <span className="text-[10px] font-mono font-semibold px-1.5 py-0.5 bg-slate-100 dark:bg-slate-800 rounded text-slate-600 dark:text-slate-300">
                    {p.cpse}
                  </span>
                </div>
                <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                  {p.desc}
                </p>
              </div>

              <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-xs">
                <span className="text-[11px] font-mono text-slate-400">@{p.user}</span>
                <Link
                  href="/login"
                  className="text-emerald-600 dark:text-emerald-400 font-semibold text-[11px] hover:underline flex items-center gap-1"
                >
                  Test Role &rarr;
                </Link>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Connected CPSEs */}
      <section id="cpse-mesh" className="max-w-6xl mx-auto px-4 sm:px-6 space-y-6">
        <div className="text-center space-y-2">
          <h2 className="text-xl font-bold tracking-tight text-slate-900 dark:text-white">
            Inter-CPSE Mutual Aid Mesh
          </h2>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Federated spare parts discovery across Indian Public Sector Undertakings.
          </p>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-7 gap-2.5">
          {CPSE_PARTNERS.map((cpse) => (
            <div
              key={cpse.code}
              className="p-3.5 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg text-center"
            >
              <p className="font-bold text-xs text-slate-900 dark:text-white font-mono">
                {cpse.code}
              </p>
              <p className="text-[10px] text-slate-500 truncate mt-0.5">{cpse.name}</p>
            </div>
          ))}
        </div>
      </section>

      {/* National Standards & Make in India Banner */}
      <section id="governance" className="max-w-6xl mx-auto px-4 sm:px-6">
        <div className="p-6 bg-slate-100 dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 text-center space-y-2 text-xs text-slate-600 dark:text-slate-400">
          <p className="font-bold text-slate-900 dark:text-white text-sm">
            National Standards Compliance & Sovereign Governance
          </p>
          <p className="max-w-3xl mx-auto leading-relaxed">
            All technical specifications prioritize Indian procurement standards: Bureau of Indian Standards (<strong>IS 2062</strong>, <strong>IS 14846</strong>, <strong>IS 1239</strong>), Oil Industry Safety Directorate (<strong>OISD-RP-126</strong>, <strong>OISD-STD-118</strong>), Engineers India Limited (<strong>EIL 6-44</strong>), and Make in India (DPIIT Class-I $\ge 50\%$).
          </p>
        </div>
      </section>
    </div>
  );
}
