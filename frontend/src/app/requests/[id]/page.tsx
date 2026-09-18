"use client";

import React, { use, useState } from 'react';
import Link from 'next/link';
import { Card, StatusBadge } from '@/components/ui';
import { QRCodeSVG } from '@/components/QRCodeSVG';
import {
  Printer,
  Truck,
  ArrowLeft,
  CheckCircle2,
  Clock,
  ShieldCheck,
  AlertTriangle,
  FileText,
  MapPin,
  Building2,
  KeyRound,
  Radio,
  ExternalLink,
  ChevronRight,
  Sparkles,
} from 'lucide-react';

export default function ConsignmentDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);

  // Stepper state
  const [activeStep, setActiveStep] = useState<number>(4); // 4 = Dispatched / In-Transit
  const [gpsPingCount, setGpsPingCount] = useState<number>(42);
  const [telemetryMessage, setTelemetryMessage] = useState<string | null>(null);

  const isEmergency = id.includes('99201') || id.includes('55102');

  const sha256Seal = '9e8a71b287cf45a19084bb92427ae41e4649b934ca495991b7852b855902bca8';
  const qrDataPayload = JSON.stringify({
    pass: `GP-NR-${id}`,
    req_id: id,
    origin: 'IOCL-PNP-REF',
    destination: 'HPCL-VSK-VRMP',
    sha256: sha256Seal.slice(0, 16),
    cisf_post: 'PANIPAT-GATE-04',
    security_clearance: 'VERIFIED_MUTUAL_AID',
  });

  const handleSimulatePing = () => {
    setGpsPingCount(prev => prev + 1);
    setTelemetryMessage(`GPS telemetry heartbeat acknowledged via IRNSS / NavIC satellite beacon. Speed: 52 km/h • Battery: 98%.`);
    setTimeout(() => setTelemetryMessage(null), 4000);
  };

  const handleAdvanceStep = () => {
    if (activeStep < 5) {
      setActiveStep(prev => prev + 1);
      setTelemetryMessage(`Milestone advanced to: Stage ${activeStep + 1} (Destination Receipt & Ledger Reconciliation).`);
      setTimeout(() => setTelemetryMessage(null), 5000);
    }
  };

  const steps = [
    {
      id: 1,
      title: 'Requisition Approved',
      actor: 'GM Materials (IOCL Panipat)',
      timestamp: '2026-03-16 11:30 IST',
      detail: 'Inter-CPSE mutual aid requisition validated and authorized under MoPNG directive.',
      completed: activeStep >= 1,
      current: activeStep === 1,
    },
    {
      id: 2,
      title: 'MTC & Metallurgy Cleared',
      actor: 'Samanvay Automated Rule Engine',
      timestamp: '2026-03-16 11:32 IST',
      detail: 'ASTM A105 / API 600 ladle analysis validated. Carbon Equivalent CE = 0.41 (Limit <= 0.43). Zero tolerance variance.',
      completed: activeStep >= 2,
      current: activeStep === 2,
    },
    {
      id: 3,
      title: 'CISF Gate Pass Issued',
      actor: 'CISF Unit (Inspector R. K. Singh)',
      timestamp: '2026-03-17 13:45 IST',
      detail: 'Non-Returnable Gate Pass MoPNG/CISF/GP-NR/2026/0412 generated with SHA-256 seal.',
      completed: activeStep >= 3,
      current: activeStep === 3,
    },
    {
      id: 4,
      title: 'Dispatched & In-Transit',
      actor: 'CONCOR Logistics Driver B. Singh',
      timestamp: '2026-03-17 14:00 IST',
      detail: 'Out-Gate biometric clearance passed. Vehicle HR-06-EA-8841 en-route via NH-44 / NH-16 corridor.',
      completed: activeStep >= 4,
      current: activeStep === 4,
    },
    {
      id: 5,
      title: 'Receipt & Stock Reconciliation',
      actor: 'Materials Receiving (HPCL Visakh)',
      timestamp: 'Expected Tomorrow, 06:30 IST',
      detail: 'Destination In-Gate scan, physical seal verification, and automated Stock Ledger debit/credit.',
      completed: activeStep >= 5,
      current: activeStep === 5,
    },
  ];

  return (
    <div className="max-w-6xl mx-auto space-y-6 pb-12">
      {/* Top Breadcrumb & Control Header (Hidden when printing) */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 no-print border-b border-slate-200 dark:border-slate-800 pb-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <Link
              href="/requests"
              className="text-xs font-mono text-slate-500 hover:text-slate-800 dark:hover:text-slate-200 flex items-center gap-1"
            >
              <ArrowLeft size={14} /> Back to Requisitions
            </Link>
            <span className="text-slate-300 dark:text-slate-700">/</span>
            <span className="text-xs font-mono font-bold text-slate-700 dark:text-slate-300">
              {id}
            </span>
          </div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold font-mono tracking-tight text-slate-900 dark:text-white">
              Consignment {id}
            </h1>
            <span className="px-2.5 py-0.5 text-xs font-mono font-bold bg-blue-100 dark:bg-blue-950 text-blue-800 dark:text-blue-300 border border-blue-200 dark:border-blue-900 rounded">
              {activeStep === 5 ? 'DELIVERED & RECONCILED' : 'IN TRANSIT (68%)'}
            </span>
            {isEmergency && (
              <span className="px-2 py-0.5 text-xs font-mono font-bold bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300 border border-rose-200 dark:border-rose-900 rounded flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-rose-600 animate-ping"></span>
                EMERGENCY BREAKDOWN SLA
              </span>
            )}
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => window.print()}
            className="px-4 py-2 bg-slate-900 hover:bg-slate-800 dark:bg-white dark:hover:bg-slate-100 text-white dark:text-slate-950 rounded text-xs font-mono font-bold flex items-center gap-2 shadow-sm transition-colors cursor-pointer"
          >
            <Printer size={15} /> Print CISF Gate Pass
          </button>
        </div>
      </div>

      {/* Telemetry Alert (Hidden on print) */}
      {telemetryMessage && (
        <div className="p-3.5 bg-blue-50 dark:bg-blue-950/50 border border-blue-200 dark:border-blue-800 text-blue-900 dark:text-blue-200 rounded-lg flex items-center justify-between text-xs font-mono no-print">
          <div className="flex items-center gap-2">
            <Radio size={16} className="text-blue-600 animate-pulse" />
            <span>{telemetryMessage}</span>
          </div>
        </div>
      )}

      {/* 5-Stage Milestone Stepper (Hidden on print) */}
      <Card className="p-5 no-print space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-500">
            Chain of Custody & Consignment Milestones
          </h2>
          <span className="text-xs font-mono text-slate-500">
            Stage {activeStep} of 5 Active
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-5 gap-3 relative">
          {steps.map((step, idx) => {
            const isDone = step.completed;
            const isCurrent = step.current;

            return (
              <div
                key={step.id}
                className={`p-3 rounded border transition-all ${
                  isCurrent
                    ? 'border-blue-500 bg-blue-50/40 dark:bg-blue-950/30'
                    : isDone
                    ? 'border-emerald-500/50 bg-emerald-50/20 dark:bg-emerald-950/10'
                    : 'border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/30 opacity-70'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <span
                    className={`w-6 h-6 rounded-full text-xs font-mono font-bold flex items-center justify-center ${
                      isDone
                        ? 'bg-emerald-600 text-white'
                        : isCurrent
                        ? 'bg-blue-600 text-white animate-pulse'
                        : 'bg-slate-200 dark:bg-slate-800 text-slate-600 dark:text-slate-400'
                    }`}
                  >
                    {isDone ? '✓' : step.id}
                  </span>
                  <span className="text-[10px] font-mono text-slate-400">
                    {isDone ? 'CLEARED' : isCurrent ? 'CURRENT' : 'PENDING'}
                  </span>
                </div>
                <h3 className="font-mono text-xs font-bold text-slate-900 dark:text-white leading-tight mb-1">
                  {step.title}
                </h3>
                <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-snug">
                  {step.timestamp}
                </p>
                <p className="text-[10px] text-slate-600 dark:text-slate-400 mt-2 font-mono line-clamp-2">
                  {step.actor}
                </p>
              </div>
            );
          })}
        </div>

        {activeStep < 5 && (
          <div className="flex items-center justify-between pt-2 border-t border-slate-200 dark:border-slate-800">
            <div className="text-xs font-mono text-slate-500">
              Corridor telemetry updated via satellite transponder ping #{gpsPingCount}
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={handleSimulatePing}
                className="px-3 py-1.5 border border-slate-300 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800 rounded text-xs font-mono text-slate-700 dark:text-slate-300 flex items-center gap-1.5 transition-colors"
              >
                <Radio size={13} /> Ping GPS Telemetry
              </button>
              <button
                onClick={handleAdvanceStep}
                className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded text-xs font-mono font-bold flex items-center gap-1.5 transition-colors"
              >
                <span>Simulate In-Gate Receipt</span>
                <ChevronRight size={14} />
              </button>
            </div>
          </div>
        )}
      </Card>

      {/* Grid: Logistics Details (Left) + Printable Gate Pass (Right or Full on Print) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Live Logistics & Waypoint Telemetry (Hidden on print) */}
        <div className="space-y-4 no-print lg:col-span-1">
          <Card className="p-4 space-y-4">
            <div className="flex items-center gap-2 border-b border-slate-200 dark:border-slate-800 pb-2">
              <Truck size={17} className="text-blue-500" />
              <h3 className="font-mono text-xs font-bold uppercase tracking-wider text-slate-800 dark:text-slate-200">
                Transit Telemetry & Carrier
              </h3>
            </div>

            <div className="space-y-3 font-mono text-xs">
              <div>
                <span className="text-slate-400 text-[10px] uppercase block">Carrier Fleet</span>
                <p className="font-semibold text-slate-800 dark:text-slate-200">
                  CONCOR Special Heavy Freight Ltd
                </p>
                <p className="text-[11px] text-slate-500">Dedicated Petroleum Corridor Service</p>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <span className="text-slate-400 text-[10px] uppercase block">Vehicle No</span>
                  <p className="font-bold text-slate-900 dark:text-white">HR-06-EA-8841</p>
                </div>
                <div>
                  <span className="text-slate-400 text-[10px] uppercase block">E-Way Bill</span>
                  <p className="font-semibold text-slate-700 dark:text-slate-300">2410-8912-7741</p>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <span className="text-slate-400 text-[10px] uppercase block">Driver Details</span>
                  <p className="font-semibold text-slate-800 dark:text-slate-200">Balwinder Singh</p>
                  <p className="text-[11px] text-slate-500">+91 98765-XXXXX</p>
                </div>
                <div>
                  <span className="text-slate-400 text-[10px] uppercase block">Driving License</span>
                  <p className="text-slate-700 dark:text-slate-300 text-[11px]">DL-04201988102</p>
                </div>
              </div>

              <div className="p-2.5 bg-slate-50 dark:bg-slate-900 rounded border border-slate-200 dark:border-slate-800 space-y-1.5">
                <div className="flex items-center justify-between text-[11px]">
                  <span className="text-slate-500">Current Position</span>
                  <span className="text-emerald-600 dark:text-emerald-400 font-bold flex items-center gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
                    Live NavIC
                  </span>
                </div>
                <p className="font-semibold text-slate-800 dark:text-slate-200 text-xs">
                  NH-16 near Rajahmundry Waypoint, AP
                </p>
                <div className="flex items-center justify-between text-[10px] text-slate-500">
                  <span>Speed: 54 km/h</span>
                  <span>Heading: South-East (142°)</span>
                </div>
              </div>

              <div>
                <div className="flex items-center justify-between text-[11px] mb-1">
                  <span className="text-slate-500">Distance Completed</span>
                  <span className="font-bold text-slate-800 dark:text-slate-200">
                    938 / 1,380 km (68%)
                  </span>
                </div>
                <div className="w-full bg-slate-200 dark:bg-slate-800 h-2 rounded-full overflow-hidden">
                  <div className="bg-blue-600 h-full rounded-full" style={{ width: '68%' }} />
                </div>
                <div className="flex items-center justify-between text-[10px] text-slate-400 mt-1">
                  <span>Panipat Out-Gate</span>
                  <span>Visakh VRMP Site</span>
                </div>
              </div>
            </div>
          </Card>

          {/* Cryptographic Sovereign Anchor Proof */}
          <Card className="p-4 space-y-3">
            <div className="flex items-center gap-2 border-b border-slate-200 dark:border-slate-800 pb-2">
              <KeyRound size={16} className="text-emerald-500" />
              <h3 className="font-mono text-xs font-bold uppercase tracking-wider text-slate-800 dark:text-slate-200">
                Sovereign Cryptographic Proof
              </h3>
            </div>
            <div className="space-y-2 text-xs font-mono">
              <div>
                <span className="text-slate-400 text-[10px] uppercase block">Immutable SHA-256 Digest</span>
                <p className="text-[10px] text-slate-600 dark:text-slate-300 break-all font-mono bg-slate-100 dark:bg-slate-900 p-1.5 rounded">
                  {sha256Seal}
                </p>
              </div>
              <div className="flex items-center justify-between text-[11px]">
                <span className="text-slate-500">Consensus Anchor:</span>
                <span className="text-emerald-600 dark:text-emerald-400 font-bold">
                  5/5 CPSE Nodes Confirmed
                </span>
              </div>
              <div className="flex items-center justify-between text-[11px]">
                <span className="text-slate-500">CISF Security Out-Gate:</span>
                <span className="font-bold text-slate-700 dark:text-slate-300">PANIPAT-GATE-04</span>
              </div>
            </div>
          </Card>
        </div>

        {/* Right Column (or Full Page on Print): Sovereign CISF Material Gate Pass */}
        <div className="lg:col-span-2">
          <div className="bg-white text-black p-8 shadow-sm border-2 border-slate-900 rounded-sm font-sans print:border-none print:shadow-none print:p-0 print:m-0">
            {/* MoPNG Official Seal & Header */}
            <div className="border-b-2 border-black pb-4 mb-4 text-center relative">
              <div className="inline-block px-3 py-0.5 border border-black text-[11px] font-mono font-bold tracking-wider mb-2">
                GOVERNMENT OF INDIA • MINISTRY OF PETROLEUM & NATURAL GAS
              </div>
              <h2 className="text-xl font-bold tracking-wider uppercase font-mono">
                CENTRAL INDUSTRIAL SECURITY FORCE (CISF) UNIT
              </h2>
              <p className="text-xs font-mono font-bold tracking-widest uppercase mt-0.5 text-slate-800">
                SOVEREIGN INTER-DEPOT MATERIAL TRANSFER GATE PASS (NON-RETURNABLE)
              </p>
              <p className="text-[10px] font-mono text-slate-600 mt-1">
                Issued Under MoPNG Unified Surplus Allocation Policy & Samanvay-AI P2P Mesh Network
              </p>

              <div className="absolute right-0 top-0 hidden md:block print:block text-right">
                <span className="inline-block px-2 py-0.5 bg-black text-white text-[10px] font-mono font-bold uppercase">
                  NON-RETURNABLE
                </span>
              </div>
            </div>

            {/* Pass Metadata Header Bar */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 bg-slate-100 p-2.5 border border-black text-xs font-mono mb-4">
              <div>
                <span className="text-slate-600 text-[10px] uppercase block">Gate Pass No.</span>
                <strong className="text-black font-bold">MoPNG/CISF/GP-NR/2026/0412</strong>
              </div>
              <div>
                <span className="text-slate-600 text-[10px] uppercase block">Date & Time Issued</span>
                <strong className="text-black">2026-03-17 13:45 IST</strong>
              </div>
              <div>
                <span className="text-slate-600 text-[10px] uppercase block">Requisition Ref</span>
                <strong className="text-black font-bold">{id}</strong>
              </div>
              <div>
                <span className="text-slate-600 text-[10px] uppercase block">Category / Priority</span>
                <strong className="text-black">EMERGENCY MUTUAL AID</strong>
              </div>
            </div>

            {/* Consignor & Consignee Depots */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 border border-black p-3.5 mb-4 text-xs font-mono">
              <div className="space-y-1 border-b md:border-b-0 md:border-r border-black md:pr-4 pb-3 md:pb-0">
                <span className="text-[10px] uppercase font-bold text-slate-600 tracking-wider">
                  DISPATCHING CPSE NODE (CONSIGNOR)
                </span>
                <p className="font-bold text-sm text-black">
                  INDIAN OIL CORPORATION LIMITED (IOCL)
                </p>
                <p className="text-[11px] text-slate-700">
                  Panipat Refinery & Petrochemical Complex, Baholi, Panipat, Haryana - 132140
                </p>
                <p className="text-[10px] text-slate-600">
                  Plant Code: IOCL-PNP-01 • GSTIN: 06AAACI1681G1ZM
                </p>
                <p className="text-[10px] text-slate-600">
                  Dispatch Bay: Heavy Equipment Bay 04
                </p>
              </div>

              <div className="space-y-1 md:pl-2">
                <span className="text-[10px] uppercase font-bold text-slate-600 tracking-wider">
                  RECEIVING CPSE NODE (CONSIGNEE)
                </span>
                <p className="font-bold text-sm text-black">
                  HINDUSTAN PETROLEUM CORPORATION LIMITED (HPCL)
                </p>
                <p className="text-[11px] text-slate-700">
                  Visakh Refinery (VRMP Expansion Site), Malkapuram, Visakhapatnam, AP - 530011
                </p>
                <p className="text-[10px] text-slate-600">
                  Plant Code: HPCL-VSK-02 • GSTIN: 37AAACH1118B1ZP
                </p>
                <p className="text-[10px] text-slate-600">
                  Contact: S. R. Murthy (Chief Engineer - Turbomachinery)
                </p>
              </div>
            </div>

            {/* Carrier & Vehicle Schedule */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2 border border-black p-2.5 mb-4 text-xs font-mono bg-slate-50">
              <div>
                <span className="text-slate-600 text-[10px] uppercase block">Transport Carrier</span>
                <strong className="text-black">CONCOR Multi-Axle Logistics</strong>
              </div>
              <div>
                <span className="text-slate-600 text-[10px] uppercase block">Vehicle Reg. No.</span>
                <strong className="text-black font-bold text-sm">HR-06-EA-8841</strong>
              </div>
              <div>
                <span className="text-slate-600 text-[10px] uppercase block">Driver Name & DL</span>
                <strong className="text-black">B. Singh / DL-04201988102</strong>
              </div>
              <div>
                <span className="text-slate-600 text-[10px] uppercase block">E-Way Bill Number</span>
                <strong className="text-black">2410-8912-7741</strong>
              </div>
            </div>

            {/* Material Items Schedule */}
            <div className="mb-4">
              <span className="text-[10px] uppercase font-mono font-bold text-slate-700 tracking-wider block mb-1">
                SCHEDULE OF MATERIALS AUTHORIZED FOR TRANSIT
              </span>
              <table className="w-full border-collapse border border-black text-xs font-mono">
                <thead>
                  <tr className="bg-slate-200 border-b border-black text-left">
                    <th className="p-2 border-r border-black w-12 text-center">Sl.</th>
                    <th className="p-2 border-r border-black">Part Code & Description</th>
                    <th className="p-2 border-r border-black">Metallurgy / Heat No.</th>
                    <th className="p-2 border-r border-black">Mill Test Cert (MTC)</th>
                    <th className="p-2 border-r border-black text-center w-16">Qty</th>
                    <th className="p-2 text-right w-20">Weight (KG)</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-black">
                  <tr>
                    <td className="p-2 border-r border-black text-center font-bold">01</td>
                    <td className="p-2 border-r border-black">
                      <p className="font-bold text-black">Gas Turbine Rotor Assy (PRT-5512)</p>
                      <p className="text-[10px] text-slate-600">
                        High-Pressure 14-Stage Compressor & Hot Section Turbine Rotor
                      </p>
                    </td>
                    <td className="p-2 border-r border-black">
                      <p className="font-semibold">Ni-Cr-Mo Alloy Steel</p>
                      <p className="text-[10px] text-slate-600">Heat: HT-ROT-2024-881</p>
                    </td>
                    <td className="p-2 border-r border-black text-[11px]">
                      <p className="font-bold">MTC-BHEL-2024-09</p>
                      <span className="text-emerald-700 text-[10px]">✓ EN 10204 Type 3.1</span>
                    </td>
                    <td className="p-2 border-r border-black text-center font-bold">1 EA</td>
                    <td className="p-2 text-right font-semibold">4,850.0</td>
                  </tr>
                </tbody>
              </table>
            </div>

            {/* Statutory Certification Statement */}
            <div className="text-[10px] font-mono text-slate-700 border-l-2 border-black pl-3 py-1 mb-6 space-y-1">
              <p>
                <strong>CERTIFICATE OF MUTUAL CPSE TRANSFER:</strong> Certified that the materials listed above belong to
                the surplus pool of MoPNG CPSEs and are being transferred under official mutual assistance protocols.
                This movement is strictly non-commercial and exempt from state Octroi / local entry transit tariffs under
                Order MoPNG/E-DISP/2025/11.
              </p>
            </div>

            {/* Cryptographic QR Code & Three-Party Signatures */}
            <div className="grid grid-cols-3 gap-4 pt-4 border-t-2 border-black items-end">
              {/* Authorized Officer */}
              <div className="text-center font-mono space-y-1">
                <div className="w-36 mx-auto border-b border-black mb-2 pb-1">
                  <span className="font-serif italic text-sm text-slate-800">R. K. Srivastava</span>
                </div>
                <p className="font-bold text-xs uppercase text-black">Authorized Officer</p>
                <p className="text-[10px] text-slate-600">
                  Dy. General Manager (Materials & Stores)
                </p>
                <p className="text-[9px] text-slate-500">IOCL Panipat Refinery</p>
                <p className="text-[9px] font-mono text-slate-400">PKI: IOCL-DGM-0941#SIG</p>
              </div>

              {/* CISF Security Checkpoint Stamp */}
              <div className="text-center font-mono space-y-1 border-x border-dashed border-slate-400 px-2">
                <div className="w-28 h-14 mx-auto border-2 border-blue-900 rounded-sm flex flex-col items-center justify-center p-1 bg-blue-50/50">
                  <span className="text-[9px] font-bold text-blue-950 uppercase tracking-tighter">
                    CISF SECURITY OUT-GATE
                  </span>
                  <span className="text-[8px] font-bold text-blue-800">
                    PANIPAT REFINERY UNIT
                  </span>
                  <span className="text-[8px] font-mono text-blue-900">
                    PASS NO: GP-NR-0412
                  </span>
                  <span className="text-[7px] text-blue-700">CLEARED • 14:02 IST</span>
                </div>
                <p className="font-bold text-xs uppercase text-black mt-1">CISF Out-Gate In-Charge</p>
                <p className="text-[10px] text-slate-600">Sub-Inspector / Security Post #04</p>
              </div>

              {/* Real SVG QR Code & Cryptographic Seal */}
              <div className="flex flex-col items-center text-center font-mono space-y-1">
                <div className="border border-black p-1 bg-white inline-block">
                  <QRCodeSVG value={qrDataPayload} size={90} />
                </div>
                <p className="text-[9px] font-bold uppercase text-black">
                  Cryptographic Verification Seal
                </p>
                <p className="text-[8px] text-slate-500 font-mono break-all max-w-[170px]">
                  SHA256: {sha256Seal.slice(0, 24)}...
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
