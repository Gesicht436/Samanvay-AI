"use client";

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Card } from '@/components/ui';
import {
  Check,
  X,
  AlertTriangle,
  FileText,
  Flame,
  ShieldCheck,
  ShieldAlert,
  ArrowLeft,
  ZoomIn,
  ZoomOut,
  Maximize2,
  Layers,
  Sparkles,
  Database,
  ExternalLink,
} from 'lucide-react';
import { MTC_PRESETS, MTCInspectionData } from '@/lib/mockMTCs';

export default function ReviewPage() {
  const router = useRouter();
  const [mtcData, setMtcData] = useState<MTCInspectionData>(MTC_PRESETS['preset-1']);
  const [status, setStatus] = useState<'IN_STORAGE' | 'IDLE_SURPLUS' | 'TO_BE_CONSUMED'>('IDLE_SURPLUS');
  const [activeField, setActiveField] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'document' | 'raw_text'>('document');
  const [zoomLevel, setZoomLevel] = useState<number>(100);
  const [isCommitted, setIsCommitted] = useState(false);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const stored = sessionStorage.getItem('current_mtc');
      if (stored) {
        try {
          const parsed = JSON.parse(stored);
          setMtcData(parsed);
        } catch {
          // fallback to preset-1
        }
      }
    }
  }, []);

  const {
    filename,
    doc_type,
    is_scanned,
    confidence_score,
    requires_hitl,
    extracted_attributes,
    chemistry,
    carbon_equivalent_iiw,
    weldability,
    pren,
    mechanical,
    astm_conformance,
    warnings,
    raw_text,
    bounding_boxes,
  } = mtcData;

  const header = extracted_attributes.properties || {};

  const handleCommit = () => {
    setIsCommitted(true);
    setTimeout(() => {
      router.push('/inventory');
    }, 900);
  };

  const handleReject = () => {
    router.push('/inventory?tab=HITL');
  };

  return (
    <div className="flex flex-col h-full space-y-4 max-w-[1600px] mx-auto">
      {/* Top Action Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 bg-white dark:bg-slate-900 p-4 rounded-xl border border-slate-200 dark:border-slate-800 shadow-xs shrink-0">
        <div className="flex items-center gap-3">
          <button
            onClick={() => router.push('/upload')}
            className="p-1.5 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-md text-slate-500 transition-colors"
            title="Return to Intake"
          >
            <ArrowLeft size={18} />
          </button>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-base font-bold font-mono text-slate-900 dark:text-slate-100 truncate max-w-md">
                {filename}
              </h1>
              <span
                className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded-full border ${
                  is_scanned
                    ? 'bg-blue-50 dark:bg-blue-950/60 text-blue-700 dark:text-blue-300 border-blue-200 dark:border-blue-900'
                    : 'bg-emerald-50 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-300 border-emerald-200 dark:border-emerald-800'
                }`}
              >
                {is_scanned ? 'RASTER SCAN (DESKEWED)' : 'DIGITAL VECTOR PDF (<50MS)'}
              </span>
            </div>
            <p className="text-xs text-slate-500 font-mono mt-0.5">
              Cert No: {header.certificate_no || 'N/A'} · Heat: {header.heat_no || 'N/A'} · PO: {header.po_no || 'N/A'}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {/* Confidence Meter */}
          <div className="flex items-center gap-2 bg-slate-50 dark:bg-slate-800/80 px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700">
            <span className="text-xs font-mono text-slate-500">Confidence:</span>
            <span
              className={`text-xs font-mono font-bold ${
                confidence_score >= 0.95
                  ? 'text-emerald-600 dark:text-emerald-400'
                  : confidence_score >= 0.85
                  ? 'text-amber-600 dark:text-amber-400'
                  : 'text-rose-600 dark:text-rose-400'
              }`}
            >
              {(confidence_score * 100).toFixed(1)}%
            </span>
          </div>

          {/* ASTM Conformance Pill */}
          <span
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-mono font-bold border ${
              astm_conformance
                ? 'bg-emerald-50 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-300 border-emerald-200 dark:border-emerald-800'
                : 'bg-rose-50 dark:bg-rose-950/60 text-rose-700 dark:text-rose-300 border-rose-200 dark:border-rose-900'
            }`}
          >
            {astm_conformance ? <ShieldCheck size={16} /> : <ShieldAlert size={16} />}
            {astm_conformance ? 'ASTM CONFORMING' : 'BOUNDARY VIOLATION'}
          </span>

          {/* HITL Badge */}
          {requires_hitl && (
            <span className="flex items-center gap-1 px-2.5 py-1 bg-amber-100 dark:bg-amber-950/60 text-amber-800 dark:text-amber-300 border border-amber-300 dark:border-amber-800 text-xs font-mono font-bold rounded">
              <AlertTriangle size={14} /> HITL TRIAGE
            </span>
          )}
        </div>
      </div>

      {/* Split-Screen Main Content */}
      <div className="flex flex-col lg:flex-row gap-4 flex-1 min-h-0 overflow-hidden">
        {/* Left Pane: Interactive Document Preview with Bounding Boxes */}
        <Card className="flex-1 flex flex-col p-0 overflow-hidden border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm">
          {/* Document Toolbar */}
          <div className="p-3 border-b border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/60 flex items-center justify-between text-xs font-mono">
            <div className="flex items-center gap-2">
              <button
                onClick={() => setViewMode('document')}
                className={`px-2.5 py-1 rounded font-semibold transition-colors ${
                  viewMode === 'document'
                    ? 'bg-slate-900 dark:bg-slate-100 text-white dark:text-slate-900'
                    : 'text-slate-600 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-700'
                }`}
              >
                MTC Preview & Boxes
              </button>
              <button
                onClick={() => setViewMode('raw_text')}
                className={`px-2.5 py-1 rounded font-semibold transition-colors ${
                  viewMode === 'raw_text'
                    ? 'bg-slate-900 dark:bg-slate-100 text-white dark:text-slate-900'
                    : 'text-slate-600 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-700'
                }`}
              >
                Raw OCR Text Stream
              </button>
            </div>

            <div className="flex items-center gap-1.5 text-slate-500">
              <button
                onClick={() => setZoomLevel((z) => Math.max(75, z - 15))}
                className="p-1 hover:bg-slate-200 dark:hover:bg-slate-700 rounded"
                title="Zoom Out"
              >
                <ZoomOut size={16} />
              </button>
              <span className="w-10 text-center">{zoomLevel}%</span>
              <button
                onClick={() => setZoomLevel((z) => Math.min(150, z + 15))}
                className="p-1 hover:bg-slate-200 dark:hover:bg-slate-700 rounded"
                title="Zoom In"
              >
                <ZoomIn size={16} />
              </button>
            </div>
          </div>

          {/* Document Content Viewport */}
          <div className="flex-1 overflow-auto p-6 bg-slate-100 dark:bg-slate-950 flex items-start justify-center">
            {viewMode === 'raw_text' ? (
              <pre className="w-full h-full p-4 bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-800 rounded font-mono text-xs text-slate-800 dark:text-slate-200 whitespace-pre-wrap select-text leading-relaxed">
                {raw_text}
              </pre>
            ) : (
              <div
                style={{ transform: `scale(${zoomLevel / 100})`, transformOrigin: 'top center' }}
                className="w-full max-w-2xl bg-white text-slate-900 p-8 rounded shadow-lg border border-slate-300 relative transition-transform duration-150 select-text font-serif min-h-[850px]"
              >
                {/* Simulated Official MTC Certificate Header */}
                <div className="border-b-2 border-slate-900 pb-4 mb-4 text-center">
                  <h2 className="text-xl font-bold tracking-tight uppercase text-slate-900">
                    {header.manufacturer || 'LARSEN & TOUBRO HEAVY ENGINEERING'}
                  </h2>
                  <p className="text-xs font-mono text-slate-600 mt-1 uppercase">
                    QUALITY ASSURANCE & METALLURGY DIVISION · EN 10204 TYPE {extracted_attributes.standard.includes('3.2') ? '3.2' : '3.1'} INSPECTION CERTIFICATE
                  </p>
                </div>

                {/* Certificate Meta Grid */}
                <div className="grid grid-cols-2 gap-3 text-xs font-mono mb-4 border border-slate-300 p-3 bg-slate-50/50">
                  <div
                    className={`p-1 rounded transition-colors ${
                      activeField === 'certificate_no' ? 'bg-emerald-100 ring-2 ring-emerald-500' : ''
                    }`}
                  >
                    <span className="text-slate-500 block">Certificate No:</span>
                    <span className="font-bold">{header.certificate_no || 'MTC/2026/5516'}</span>
                  </div>
                  <div
                    className={`p-1 rounded transition-colors ${
                      activeField === 'po_no' ? 'bg-emerald-100 ring-2 ring-emerald-500' : ''
                    }`}
                  >
                    <span className="text-slate-500 block">Purchase Order No:</span>
                    <span className="font-bold">{header.po_no || 'PO-MOPNG-505403'}</span>
                  </div>
                  <div
                    className={`p-1 rounded transition-colors ${
                      activeField === 'heat_no' ? 'bg-emerald-100 ring-2 ring-emerald-500' : ''
                    }`}
                  >
                    <span className="text-slate-500 block">Heat / Melt No:</span>
                    <span className="font-bold text-slate-900">{header.heat_no || 'HT-2025-20300'}</span>
                  </div>
                  <div
                    className={`p-1 rounded transition-colors ${
                      activeField === 'metallurgy' ? 'bg-emerald-100 ring-2 ring-emerald-500' : ''
                    }`}
                  >
                    <span className="text-slate-500 block">Material Grade:</span>
                    <span className="font-bold text-slate-900">{extracted_attributes.metallurgy}</span>
                  </div>
                </div>

                {/* Product Description */}
                <div className="mb-4 text-xs font-mono border-b border-slate-200 pb-3">
                  <span className="text-slate-500 font-bold block mb-1">PRODUCT SPECIFICATION:</span>
                  <p className="font-semibold text-slate-800">
                    {extracted_attributes.item_type} {extracted_attributes.size_nb_mm} mm ({Math.round(extracted_attributes.size_nb_mm / 25.4)}") CLASS {extracted_attributes.pressure_class}# {extracted_attributes.facing_end} {extracted_attributes.schedule}
                  </p>
                </div>

                {/* Ladle Chemistry Table on Certificate */}
                <div
                  className={`mb-4 transition-all rounded p-1 ${
                    activeField === 'chemistry' ? 'ring-2 ring-emerald-500 bg-emerald-50' : ''
                  }`}
                >
                  <span className="text-xs font-mono font-bold text-slate-700 block mb-1">
                    CHEMICAL ANALYSIS (WEIGHT PERCENT):
                  </span>
                  <table className="w-full text-[11px] font-mono border-collapse border border-slate-300">
                    <thead className="bg-slate-100 text-slate-700">
                      <tr>
                        {Object.keys(chemistry).slice(0, 8).map((el) => (
                          <th key={el} className="border border-slate-300 p-1 text-center font-bold">
                            {el}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      <tr>
                        {Object.keys(chemistry).slice(0, 8).map((el) => (
                          <td key={el} className="border border-slate-300 p-1 text-center font-semibold">
                            {chemistry[el]?.toFixed(3)}
                          </td>
                        ))}
                      </tr>
                    </tbody>
                  </table>
                  <div className="mt-1 text-[10px] font-mono text-slate-600 flex justify-between">
                    <span>IIW CE: {carbon_equivalent_iiw?.toFixed(3)}%</span>
                    {pren && <span>PREN: {pren.toFixed(2)}</span>}
                  </div>
                </div>

                {/* Mechanical Properties on Certificate */}
                <div
                  className={`mb-6 transition-all rounded p-1 ${
                    activeField === 'mechanical' ? 'ring-2 ring-emerald-500 bg-emerald-50' : ''
                  }`}
                >
                  <span className="text-xs font-mono font-bold text-slate-700 block mb-1">
                    MECHANICAL TEST RESULTS (ROOM TEMPERATURE):
                  </span>
                  <div className="grid grid-cols-3 gap-2 text-xs font-mono border border-slate-300 p-2 bg-slate-50/30">
                    <div>
                      <span className="text-slate-500 block text-[10px]">YIELD STRENGTH</span>
                      <span className="font-bold">{mechanical.yield_strength_mpa || '—'} MPa</span>
                    </div>
                    <div>
                      <span className="text-slate-500 block text-[10px]">TENSILE STRENGTH</span>
                      <span className="font-bold">{mechanical.tensile_strength_mpa || '—'} MPa</span>
                    </div>
                    <div>
                      <span className="text-slate-500 block text-[10px]">ELONGATION</span>
                      <span className="font-bold">{mechanical.elongation_pct || '—'}%</span>
                    </div>
                  </div>
                </div>

                {/* Certification Stamp & TPI Sign-off */}
                <div className="mt-12 pt-6 border-t border-slate-300 flex items-center justify-between font-mono text-[10px] text-slate-600">
                  <div className="border border-emerald-600 text-emerald-800 p-2 rounded text-center rotate-[-2deg]">
                    <span className="block font-bold text-xs uppercase">{header.tpi_agency || 'BUREAU VERITAS (INDIA)'}</span>
                    <span>TPI INSPECTION APPROVED</span>
                  </div>
                  <div className="text-right">
                    <div className="w-32 border-b border-slate-900 mb-1 ml-auto"></div>
                    <span className="font-bold uppercase">Chief Metallurgist</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </Card>

        {/* Right Pane: Metallurgical Intelligence & Verification */}
        <Card className="flex-1 flex flex-col p-0 overflow-hidden border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm">
          <div className="p-3 border-b border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/60 flex items-center justify-between">
            <h2 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-800 dark:text-slate-200 flex items-center gap-2">
              <Sparkles size={14} className="text-emerald-500" />
              Metallurgical Intelligence Extraction
            </h2>
            <span className="text-[11px] font-mono text-slate-400">EN 10204 Automated Verification</span>
          </div>

          <div className="flex-1 overflow-y-auto p-5 space-y-6">
            {/* 1. Canonical Attributes */}
            <div>
              <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-500 mb-2">
                1. Canonical Material Specification
              </h3>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                <div
                  onMouseEnter={() => setActiveField('metallurgy')}
                  onMouseLeave={() => setActiveField(null)}
                  className="p-2.5 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/40 hover:border-emerald-500 transition-colors cursor-pointer"
                >
                  <span className="text-[10px] font-mono text-slate-400 block">STANDARD & GRADE</span>
                  <span className="text-sm font-bold font-mono text-slate-900 dark:text-slate-100">
                    {extracted_attributes.metallurgy}
                  </span>
                </div>

                <div
                  onMouseEnter={() => setActiveField('metallurgy')}
                  onMouseLeave={() => setActiveField(null)}
                  className="p-2.5 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/40 hover:border-emerald-500 transition-colors cursor-pointer"
                >
                  <span className="text-[10px] font-mono text-slate-400 block">ITEM TYPE</span>
                  <span className="text-sm font-bold font-mono text-slate-900 dark:text-slate-100">
                    {extracted_attributes.item_type}
                  </span>
                </div>

                <div className="p-2.5 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/40">
                  <span className="text-[10px] font-mono text-slate-400 block">NOMINAL SIZE</span>
                  <span className="text-sm font-bold font-mono text-slate-900 dark:text-slate-100">
                    {extracted_attributes.size_nb_mm} mm ({Math.round(extracted_attributes.size_nb_mm / 25.4)}")
                  </span>
                </div>

                <div className="p-2.5 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/40">
                  <span className="text-[10px] font-mono text-slate-400 block">PRESSURE CLASS</span>
                  <span className="text-sm font-bold font-mono text-slate-900 dark:text-slate-100">
                    {extracted_attributes.pressure_class}#
                  </span>
                </div>

                <div className="p-2.5 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/40">
                  <span className="text-[10px] font-mono text-slate-400 block">SCHEDULE</span>
                  <span className="text-sm font-bold font-mono text-slate-900 dark:text-slate-100">
                    {extracted_attributes.schedule}
                  </span>
                </div>

                <div className="p-2.5 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/40">
                  <span className="text-[10px] font-mono text-slate-400 block">FACING / END</span>
                  <span className="text-sm font-bold font-mono text-slate-900 dark:text-slate-100">
                    {extracted_attributes.facing_end}
                  </span>
                </div>
              </div>
            </div>

            {/* 2. IIW Carbon Equivalent & Weldability Gauge */}
            <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/50">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <Flame className="text-amber-500" size={16} />
                  <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-800 dark:text-slate-200">
                    IIW Carbon Equivalent & Weldability
                  </h3>
                </div>
                <span
                  className={`text-xs font-mono font-bold px-2 py-0.5 rounded-full border ${
                    weldability === 'STANDARD_WELDABLE'
                      ? 'bg-emerald-50 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-300 border-emerald-200 dark:border-emerald-800'
                      : weldability === 'PREHEAT_REQUIRED'
                      ? 'bg-amber-50 dark:bg-amber-950/60 text-amber-700 dark:text-amber-300 border-amber-200 dark:border-amber-800'
                      : 'bg-rose-50 dark:bg-rose-950/60 text-rose-700 dark:text-rose-300 border-rose-200 dark:border-rose-900'
                  }`}
                >
                  {weldability.replace('_', ' ')}
                </span>
              </div>

              <div className="flex items-baseline justify-between mb-2">
                <div className="flex items-baseline gap-2">
                  <span className="text-2xl font-bold font-mono text-slate-900 dark:text-slate-100">
                    {carbon_equivalent_iiw?.toFixed(3)}%
                  </span>
                  <span className="text-xs font-mono text-slate-500">
                    CE = C + Mn/6 + (Cr+Mo+V)/5 + (Ni+Cu)/15
                  </span>
                </div>
                {pren && (
                  <div className="flex items-baseline gap-1 font-mono text-xs">
                    <span className="text-slate-500">PREN:</span>
                    <span className="font-bold text-blue-600 dark:text-blue-400">{pren.toFixed(2)}</span>
                  </div>
                )}
              </div>

              {/* Visual Meter Bar */}
              <div className="w-full bg-slate-200 dark:bg-slate-700 h-2 rounded-full overflow-hidden flex">
                <div style={{ width: '60%' }} className="bg-emerald-500 h-full" title="Standard Weldable (<=0.43%)" />
                <div style={{ width: '20%' }} className="bg-amber-500 h-full" title="Preheat Required (0.43 - 0.48%)" />
                <div style={{ width: '20%' }} className="bg-rose-500 h-full" title="High Cracking Risk (>0.48%)" />
              </div>
              <div className="flex justify-between text-[10px] font-mono text-slate-400 mt-1">
                <span>0.0%</span>
                <span>0.43% (Preheat Threshold)</span>
                <span>0.48% (High Risk)</span>
                <span>0.70%</span>
              </div>
            </div>

            {/* 3. Chemical Composition Matrix */}
            <div
              onMouseEnter={() => setActiveField('chemistry')}
              onMouseLeave={() => setActiveField(null)}
              className="space-y-2"
            >
              <div className="flex items-center justify-between">
                <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-500">
                  2. Chemical Assay vs ASTM Limit
                </h3>
                <span className="text-[11px] font-mono text-emerald-600 dark:text-emerald-400 flex items-center gap-1">
                  <Check size={14} /> ASTM A105 Ladle Spec Verified
                </span>
              </div>

              <div className="border border-slate-200 dark:border-slate-800 rounded-lg overflow-hidden">
                <table className="w-full text-xs font-mono">
                  <thead className="bg-slate-50 dark:bg-slate-800/80 text-slate-500 border-b border-slate-200 dark:border-slate-800">
                    <tr>
                      <th className="p-2 text-left">Element</th>
                      <th className="p-2 text-right">Ladle %</th>
                      <th className="p-2 text-right">ASTM Permissible</th>
                      <th className="p-2 text-right">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                    {Object.entries(chemistry).map(([el, val]) => {
                      const isViolation = (el === 'C' && val > 0.35) || (el === 'S' && val > 0.025);
                      return (
                        <tr
                          key={el}
                          className={`hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors ${
                            isViolation ? 'bg-rose-50/50 dark:bg-rose-950/20' : ''
                          }`}
                        >
                          <td className="p-2 font-bold text-slate-800 dark:text-slate-200">{el}</td>
                          <td className="p-2 text-right font-bold">{val?.toFixed(3)}%</td>
                          <td className="p-2 text-right text-slate-400">
                            {el === 'C' ? '≤ 0.35%' : el === 'Mn' ? '0.60 - 1.05%' : el === 'P' ? '≤ 0.035%' : el === 'S' ? '≤ 0.025%' : 'Standard'}
                          </td>
                          <td className="p-2 text-right">
                            {isViolation ? (
                              <span className="text-[10px] text-rose-600 dark:text-rose-400 font-bold">OVER LIMIT</span>
                            ) : (
                              <span className="text-[10px] text-emerald-600 dark:text-emerald-400 font-bold">PASS</span>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>

            {/* 4. Mechanical Properties */}
            <div
              onMouseEnter={() => setActiveField('mechanical')}
              onMouseLeave={() => setActiveField(null)}
              className="space-y-2"
            >
              <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-500">
                3. Mechanical Properties & Ductility
              </h3>
              <div className="grid grid-cols-2 gap-3 font-mono text-xs">
                <div className="p-3 border border-slate-200 dark:border-slate-800 rounded-lg bg-slate-50/50 dark:bg-slate-800/40">
                  <span className="text-slate-400 block text-[10px]">YIELD STRENGTH (Re)</span>
                  <div className="flex items-baseline justify-between mt-1">
                    <span className="text-base font-bold text-slate-900 dark:text-slate-100">
                      {mechanical.yield_strength_mpa || '—'} MPa
                    </span>
                    <span className="text-[10px] text-slate-500">Min 250 MPa</span>
                  </div>
                </div>

                <div className="p-3 border border-slate-200 dark:border-slate-800 rounded-lg bg-slate-50/50 dark:bg-slate-800/40">
                  <span className="text-slate-400 block text-[10px]">TENSILE STRENGTH (Rm)</span>
                  <div className="flex items-baseline justify-between mt-1">
                    <span className="text-base font-bold text-slate-900 dark:text-slate-100">
                      {mechanical.tensile_strength_mpa || '—'} MPa
                    </span>
                    <span className="text-[10px] text-slate-500">485 - 655 MPa</span>
                  </div>
                </div>

                <div className="p-3 border border-slate-200 dark:border-slate-800 rounded-lg bg-slate-50/50 dark:bg-slate-800/40">
                  <span className="text-slate-400 block text-[10px]">ELONGATION (A5)</span>
                  <div className="flex items-baseline justify-between mt-1">
                    <span className="text-base font-bold text-slate-900 dark:text-slate-100">
                      {mechanical.elongation_pct || '—'}%
                    </span>
                    <span className="text-[10px] text-slate-500">Min 22%</span>
                  </div>
                </div>

                <div className="p-3 border border-slate-200 dark:border-slate-800 rounded-lg bg-slate-50/50 dark:bg-slate-800/40">
                  <span className="text-slate-400 block text-[10px]">BRINELL HARDNESS</span>
                  <div className="flex items-baseline justify-between mt-1">
                    <span className="text-base font-bold text-slate-900 dark:text-slate-100">
                      {mechanical.hardness_hb || '—'} HBW
                    </span>
                    <span className="text-[10px] text-slate-500">Max 187 HBW</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Warnings Alert Box if applicable */}
            {warnings.length > 0 && (
              <div className="p-3.5 bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-900/60 rounded-xl space-y-1 text-xs font-mono text-amber-800 dark:text-amber-300">
                <div className="flex items-center gap-1.5 font-bold">
                  <AlertTriangle size={16} className="text-amber-600" />
                  <span>Engineering Safety & Non-Conformance Flags</span>
                </div>
                <ul className="list-disc list-inside space-y-1 pt-1 opacity-90">
                  {warnings.map((w, idx) => (
                    <li key={idx}>{w}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Initial Plant Allocation */}
            <div className="border-t border-slate-200 dark:border-slate-800 pt-4">
              <label className="text-xs font-mono font-bold uppercase tracking-wider text-slate-500 block mb-1.5">
                Initial Plant Ledger Allocation
              </label>
              <select
                value={status}
                onChange={(e) => setStatus(e.target.value as any)}
                className="w-full p-2.5 bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-lg text-xs font-mono text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-1 focus:ring-emerald-500"
              >
                <option value="IDLE_SURPLUS">IDLE_SURPLUS · Broadcast to MoPNG Inter-CPSE Mesh</option>
                <option value="IN_STORAGE">IN_STORAGE · Reserved for Local Plant Operations</option>
                <option value="TO_BE_CONSUMED">TO_BE_CONSUMED · Scheduled Maintenance Turnaround</option>
              </select>
            </div>
          </div>

          {/* Sticky Decision Footer */}
          <div className="p-4 border-t border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 flex items-center justify-between gap-3 shrink-0">
            <button
              onClick={handleReject}
              className="px-4 py-2 border border-slate-300 dark:border-slate-700 rounded-lg font-mono text-xs font-semibold text-rose-600 dark:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/40 transition-colors flex items-center gap-1.5"
            >
              <X size={16} /> Reject to HITL Queue
            </button>

            <button
              onClick={handleCommit}
              disabled={isCommitted}
              className={`px-5 py-2 rounded-lg font-mono text-xs font-bold text-white shadow-sm flex items-center gap-2 transition-all ${
                isCommitted
                  ? 'bg-emerald-700 cursor-not-allowed'
                  : 'bg-emerald-600 hover:bg-emerald-500 active:scale-[0.99]'
              }`}
            >
              {isCommitted ? (
                <>
                  <Check size={16} /> Committed to Sovereign Ledger!
                </>
              ) : (
                <>
                  <Database size={16} /> Commit to Sovereign Ledger
                </>
              )}
            </button>
          </div>
        </Card>
      </div>
    </div>
  );
}
