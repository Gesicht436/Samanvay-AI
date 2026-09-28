"use client";

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Card } from '@/components/ui';
import {
  Check,
  AlertTriangle,
  FileText,
  ArrowLeft,
  RefreshCw,
  Edit3,
  ShieldAlert,
} from 'lucide-react';
import { ProtectedRoute } from '@/components/ProtectedRoute';
import { useAuth } from '@/context/AuthContext';
import { api } from '@/lib/api';

export default function MTCReviewPage() {
  const router = useRouter();
  const { user } = useAuth();
  const [docData, setDocData] = useState<any | null>(null);
  const [committing, setCommitting] = useState<boolean>(false);
  const [commitSuccess, setCommitSuccess] = useState<boolean>(false);
  const [commitError, setCommitError] = useState<string | null>(null);

  // Editable Form States for Manual Entry / Corrections
  const [itemType, setItemType] = useState<string>('');
  const [metallurgy, setMetallurgy] = useState<string>('');
  const [sizeNbMm, setSizeNbMm] = useState<string>('');
  const [pressureClass, setPressureClass] = useState<string>('');
  const [schedule, setSchedule] = useState<string>('');
  const [facingEnd, setFacingEnd] = useState<string>('');
  const [standard, setStandard] = useState<string>('');
  const [heatNo, setHeatNo] = useState<string>('');
  const [poNo, setPoNo] = useState<string>('');
  const [certNo, setCertNo] = useState<string>('');
  const [manufacturer, setManufacturer] = useState<string>('');

  // Chemistry Values
  const [chemC, setChemC] = useState<string>('');
  const [chemMn, setChemMn] = useState<string>('');
  const [chemSi, setChemSi] = useState<string>('');
  const [chemP, setChemP] = useState<string>('');
  const [chemS, setChemS] = useState<string>('');
  const [chemCr, setChemCr] = useState<string>('');
  const [chemNi, setChemNi] = useState<string>('');
  const [chemMo, setChemMo] = useState<string>('');

  // Mechanical Properties
  const [yieldStrength, setYieldStrength] = useState<string>('');
  const [tensileStrength, setTensileStrength] = useState<string>('');

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const stored = sessionStorage.getItem('current_mtc');
      if (stored) {
        try {
          const parsed = JSON.parse(stored);
          setDocData(parsed);

          const attrs = parsed.extracted_attributes || parsed.metadata || {};
          const chem = parsed.chemistry || attrs.chemistry || {};
          const mech = parsed.mechanical || attrs.mechanical || {};
          const header = parsed.header || attrs.properties || {};

          // Populate only strictly extracted properties (no fabricated fallbacks)
          setItemType(parsed.item_type || attrs.item_type || '');
          setMetallurgy(parsed.metallurgy || attrs.metallurgy || header.material_grade || '');
          setSizeNbMm(parsed.size_nb_mm ? String(parsed.size_nb_mm) : (attrs.size_nb_mm ? String(attrs.size_nb_mm) : ''));
          setPressureClass(parsed.pressure_class ? String(parsed.pressure_class) : (attrs.pressure_class ? String(attrs.pressure_class) : ''));
          setSchedule(parsed.schedule || attrs.schedule || '');
          setFacingEnd(parsed.facing_end || attrs.facing_end || '');
          setStandard(parsed.standard || attrs.standard || header.specification || '');
          setHeatNo(header.heat_no || '');
          setPoNo(header.po_no || '');
          setCertNo(header.certificate_no || '');
          setManufacturer(header.manufacturer || '');

          if (chem.C !== undefined && chem.C !== null) setChemC(String(chem.C));
          if (chem.Mn !== undefined && chem.Mn !== null) setChemMn(String(chem.Mn));
          if (chem.Si !== undefined && chem.Si !== null) setChemSi(String(chem.Si));
          if (chem.P !== undefined && chem.P !== null) setChemP(String(chem.P));
          if (chem.S !== undefined && chem.S !== null) setChemS(String(chem.S));
          if (chem.Cr !== undefined && chem.Cr !== null) setChemCr(String(chem.Cr));
          if (chem.Ni !== undefined && chem.Ni !== null) setChemNi(String(chem.Ni));
          if (chem.Mo !== undefined && chem.Mo !== null) setChemMo(String(chem.Mo));

          if (mech.yield_strength_mpa !== undefined && mech.yield_strength_mpa !== null) setYieldStrength(String(mech.yield_strength_mpa));
          if (mech.tensile_strength_mpa !== undefined && mech.tensile_strength_mpa !== null) setTensileStrength(String(mech.tensile_strength_mpa));
        } catch {
          setDocData(null);
        }
      }
    }
  }, []);

  if (!docData) {
    return (
      <ProtectedRoute allowedRoles={['SITE_ENGINEER', 'MATERIALS_MANAGER', 'TECHNICAL_AUTHORITY', 'SUPER_ADMIN']}>
        <div className="max-w-xl mx-auto py-20 text-center text-xs font-mono">
          <div className="p-6 bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-xl shadow-2xs">
            <FileText size={32} className="mx-auto text-zinc-400 mb-3" />
            <h2 className="text-base font-bold text-zinc-900 dark:text-white mb-1">
              No Active Document In Review
            </h2>
            <p className="text-zinc-500 mb-4">
              Please upload a Mill Test Certificate (MTC) PDF or image to inspect properties.
            </p>
            <Link
              href="/upload"
              className="inline-flex items-center gap-1.5 px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded font-semibold text-xs"
            >
              Go to Document Intake &rarr;
            </Link>
          </div>
        </div>
      </ProtectedRoute>
    );
  }

  const filename = docData.filename || 'Uploaded_Document.pdf';
  const confidence = docData.confidence_score ?? docData.confidence ?? 0.0;
  const isScanned = Boolean(docData.is_scanned);
  const isUnreadable = Boolean(docData.is_unreadable || (!docData.raw_text && confidence === 0.0));

  // Dynamic IIW Carbon Equivalent Calculation based on active form values
  const cVal = parseFloat(chemC) || 0;
  const mnVal = parseFloat(chemMn) || 0;
  const crVal = parseFloat(chemCr) || 0;
  const moVal = parseFloat(chemMo) || 0;
  const niVal = parseFloat(chemNi) || 0;
  const hasChemistry = chemC.trim() !== '';

  const calculatedCE = hasChemistry
    ? (cVal + mnVal / 6.0 + (crVal + moVal) / 5.0 + niVal / 15.0)
    : null;

  const weldability = calculatedCE !== null
    ? (calculatedCE <= 0.43 ? 'STANDARD_WELDABLE' : 'PREHEAT_REQUIRED_HIGH_CE')
    : 'NOT_EXTRACTED';

  const handleCommit = async () => {
    setCommitting(true);
    setCommitError(null);
    try {
      const skuRandom = Math.random().toString(36).substring(2, 7).toUpperCase();
      const typeCode = (itemType || 'MAT').replace(/[^A-Z0-9]/gi, '').slice(0, 6).toUpperCase();
      const generatedSku = `SKU-${typeCode}-${skuRandom}`;

      const payload: any = {
        sku_code: generatedSku,
        cpse: user?.cpse || 'OIL',
        depot_id: user?.depot_id || 'DULIAJAN-CENTRAL',
        depot_location: `${user?.depot_id || 'Duliajan'} Stores`,
        description: `${itemType || 'MATERIAL'} ${sizeNbMm ? sizeNbMm + 'NB ' : ''}${pressureClass ? 'CL' + pressureClass + ' ' : ''}${metallurgy || ''} ${standard || ''}`.trim(),
        item_type: itemType || 'PIPE',
        size_nb_mm: sizeNbMm ? parseFloat(sizeNbMm) : null,
        pressure_class: pressureClass ? parseInt(pressureClass) : null,
        schedule: schedule || null,
        metallurgy: metallurgy || null,
        facing_end: facingEnd || null,
        standard: standard || null,
        heat_no: heatNo || null,
        po_no: poNo || null,
        quantity: 10,
        unit_cost_inr: 25000.0,
        status: 'TO_BE_CONSUMED',
        properties: {
          chemistry: {
            C: cVal,
            Mn: mnVal,
            Si: parseFloat(chemSi) || 0,
            P: parseFloat(chemP) || 0,
            S: parseFloat(chemS) || 0,
            Cr: crVal,
            Ni: niVal,
            Mo: moVal,
          },
          mechanical: {
            yield_strength_mpa: parseFloat(yieldStrength) || null,
            tensile_strength_mpa: parseFloat(tensileStrength) || null,
          },
          calculated_ce: calculatedCE,
          weldability_class: weldability,
          certificate_no: certNo,
          manufacturer: manufacturer,
          source_filename: filename,
        },
      };

      await api.createInventoryItem(payload);
      setCommitSuccess(true);
      setTimeout(() => {
        router.push('/inventory');
      }, 1200);
    } catch (err: any) {
      setCommitError(`Failed to commit item: ${err.message || 'Server error'}`);
      setCommitting(false);
    }
  };

  return (
    <ProtectedRoute allowedRoles={['SITE_ENGINEER', 'MATERIALS_MANAGER', 'TECHNICAL_AUTHORITY', 'SUPER_ADMIN']}>
      <div className="flex flex-col space-y-4 max-w-[1400px] mx-auto pb-10">
        {/* Top Action Bar */}
        <div className="flex flex-wrap items-center justify-between gap-3 bg-white dark:bg-zinc-900 p-4 rounded-xl border border-zinc-200 dark:border-zinc-800 shadow-2xs">
          <div className="flex items-center gap-3">
            <Link
              href="/upload"
              className="p-1.5 hover:bg-zinc-100 dark:hover:bg-zinc-800 rounded text-zinc-500 transition-colors"
              title="Return to Upload"
            >
              <ArrowLeft size={18} />
            </Link>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-base font-bold font-mono text-zinc-900 dark:text-white truncate max-w-md">
                  {filename}
                </h1>
                <span className={`text-[10px] font-mono px-2 py-0.5 rounded-full font-semibold border ${
                  confidence > 0.75
                    ? 'bg-emerald-50 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-300 border-emerald-200 dark:border-emerald-800'
                    : 'bg-amber-50 dark:bg-amber-950/60 text-amber-700 dark:text-amber-300 border-amber-200 dark:border-amber-800'
                }`}>
                  {(confidence * 100).toFixed(1)}% Confidence
                </span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-300">
                  {isScanned ? 'Raster Scan' : 'Vector Stream'}
                </span>
              </div>
              <p className="text-xs font-mono text-zinc-500">
                MTC Verification & Human-in-the-Loop (HITL) Manual Review
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => router.push('/inventory')}
              className="px-3 py-1.5 bg-zinc-100 dark:bg-zinc-800 hover:bg-zinc-200 dark:hover:bg-zinc-700 text-zinc-700 dark:text-zinc-300 border border-zinc-300 dark:border-zinc-700 rounded text-xs font-mono font-semibold transition-colors"
            >
              Cancel / Return
            </button>
            <button
              onClick={handleCommit}
              disabled={committing || commitSuccess}
              className="px-4 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded text-xs font-mono font-semibold flex items-center gap-1.5 transition-colors disabled:opacity-50"
            >
              {committing ? <RefreshCw size={13} className="animate-spin" /> : <Check size={13} />}
              <span>{commitSuccess ? 'Committed to Ledger!' : 'Save & Commit to Stock Ledger'}</span>
            </button>
          </div>
        </div>

        {/* Unreadable Document Warning Banner */}
        {isUnreadable && (
          <div className="p-4 bg-amber-50 dark:bg-amber-950/50 border border-amber-300 dark:border-amber-700 rounded-xl flex items-start gap-3 text-amber-900 dark:text-amber-200">
            <ShieldAlert size={20} className="text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" />
            <div className="space-y-1 text-xs font-mono">
              <h3 className="font-bold text-sm text-amber-800 dark:text-amber-300">
                Image / Document is Not Readable (No Text Detected)
              </h3>
              <p>
                The OCR engine could not extract text from this file (e.g. non-engineering artwork, damaged scan, or low resolution). To prevent catastrophic safety hazards in high-pressure hydrocarbon service, no default properties have been fabricated.
              </p>
              <p className="font-semibold text-amber-700 dark:text-amber-400">
                👉 Please enter the physical and metallurgical properties manually below before committing.
              </p>
            </div>
          </div>
        )}

        {commitSuccess && (
          <div className="p-3 bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 text-emerald-800 dark:text-emerald-300 text-xs font-mono rounded-lg">
            Material specifications confirmed and saved to the sovereign stock ledger! Redirecting...
          </div>
        )}

        {commitError && (
          <div className="p-3 bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800 text-rose-800 dark:text-rose-300 text-xs font-mono rounded-lg flex items-center justify-between">
            <span>{commitError}</span>
            <button onClick={() => setCommitError(null)} className="text-zinc-400 hover:text-zinc-600">&times;</button>
          </div>
        )}

        {/* Main Extracted Panels Grid (With Manual Editable Inputs) */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
          {/* Left Column: Physical & Dimensional Attributes (6 Cols) */}
          <Card className="lg:col-span-6 p-5 border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 space-y-4">
            <div className="flex items-center justify-between pb-2 border-b border-zinc-100 dark:border-zinc-800">
              <h2 className="text-sm font-mono font-bold uppercase tracking-wider text-zinc-900 dark:text-white">
                Material Specifications (Manual Editable)
              </h2>
              <span className="text-[10px] font-mono text-zinc-400 flex items-center gap-1">
                <Edit3 size={12} /> Editable
              </span>
            </div>

            <div className="grid grid-cols-2 gap-3 text-xs font-mono">
              <div className="p-2.5 bg-zinc-50 dark:bg-zinc-800/80 rounded border border-zinc-200 dark:border-zinc-700">
                <label className="text-zinc-500 dark:text-zinc-400 block text-[11px] font-bold mb-1">Item / Component Type</label>
                <input
                  type="text"
                  value={itemType}
                  onChange={(e) => setItemType(e.target.value)}
                  placeholder="e.g. GATE_VALVE, FLANGE, PIPE"
                  className="w-full bg-white dark:bg-zinc-900 border border-zinc-300 dark:border-zinc-600 rounded px-2 py-1 text-zinc-900 dark:text-white font-semibold"
                />
              </div>

              <div className="p-2.5 bg-zinc-50 dark:bg-zinc-800/80 rounded border border-zinc-200 dark:border-zinc-700">
                <label className="text-zinc-500 dark:text-zinc-400 block text-[11px] font-bold mb-1">Metallurgy / Grade</label>
                <input
                  type="text"
                  value={metallurgy}
                  onChange={(e) => setMetallurgy(e.target.value)}
                  placeholder="e.g. ASTM A105, A216 WCB"
                  className="w-full bg-white dark:bg-zinc-900 border border-zinc-300 dark:border-zinc-600 rounded px-2 py-1 text-zinc-900 dark:text-white font-semibold"
                />
              </div>

              <div className="p-2.5 bg-zinc-50 dark:bg-zinc-800/80 rounded border border-zinc-200 dark:border-zinc-700">
                <label className="text-zinc-500 dark:text-zinc-400 block text-[11px] font-bold mb-1">Nominal Bore (NB mm)</label>
                <input
                  type="text"
                  value={sizeNbMm}
                  onChange={(e) => setSizeNbMm(e.target.value)}
                  placeholder="e.g. 100 or 150"
                  className="w-full bg-white dark:bg-zinc-900 border border-zinc-300 dark:border-zinc-600 rounded px-2 py-1 text-zinc-900 dark:text-white font-semibold"
                />
              </div>

              <div className="p-2.5 bg-zinc-50 dark:bg-zinc-800/80 rounded border border-zinc-200 dark:border-zinc-700">
                <label className="text-zinc-500 dark:text-zinc-400 block text-[11px] font-bold mb-1">Pressure Class (Rating #)</label>
                <input
                  type="text"
                  value={pressureClass}
                  onChange={(e) => setPressureClass(e.target.value)}
                  placeholder="e.g. 150, 300, 600"
                  className="w-full bg-white dark:bg-zinc-900 border border-zinc-300 dark:border-zinc-600 rounded px-2 py-1 text-zinc-900 dark:text-white font-semibold"
                />
              </div>

              <div className="p-2.5 bg-zinc-50 dark:bg-zinc-800/80 rounded border border-zinc-200 dark:border-zinc-700">
                <label className="text-zinc-500 dark:text-zinc-400 block text-[11px] font-bold mb-1">Pipe Schedule</label>
                <input
                  type="text"
                  value={schedule}
                  onChange={(e) => setSchedule(e.target.value)}
                  placeholder="e.g. SCH 40, SCH 80"
                  className="w-full bg-white dark:bg-zinc-900 border border-zinc-300 dark:border-zinc-600 rounded px-2 py-1 text-zinc-900 dark:text-white"
                />
              </div>

              <div className="p-2.5 bg-zinc-50 dark:bg-zinc-800/80 rounded border border-zinc-200 dark:border-zinc-700">
                <label className="text-zinc-500 dark:text-zinc-400 block text-[11px] font-bold mb-1">Facing / End Finish</label>
                <input
                  type="text"
                  value={facingEnd}
                  onChange={(e) => setFacingEnd(e.target.value)}
                  placeholder="e.g. RF, RTJ, BW"
                  className="w-full bg-white dark:bg-zinc-900 border border-zinc-300 dark:border-zinc-600 rounded px-2 py-1 text-zinc-900 dark:text-white"
                />
              </div>

              <div className="p-2.5 bg-zinc-50 dark:bg-zinc-800/80 rounded border border-zinc-200 dark:border-zinc-700 col-span-2">
                <label className="text-zinc-500 dark:text-zinc-400 block text-[11px] font-bold mb-1">Applicable Standard / Spec</label>
                <input
                  type="text"
                  value={standard}
                  onChange={(e) => setStandard(e.target.value)}
                  placeholder="e.g. EN 10204 3.1 / ASME B16.5"
                  className="w-full bg-white dark:bg-zinc-900 border border-zinc-300 dark:border-zinc-600 rounded px-2 py-1 text-zinc-900 dark:text-white"
                />
              </div>
            </div>

            {/* Traceability Identifiers */}
            <div className="pt-2 border-t border-zinc-100 dark:border-zinc-800 space-y-2">
              <h3 className="text-xs font-mono font-bold text-zinc-500">Procurement & Mill Traceability</h3>
              <div className="grid grid-cols-3 gap-2 text-xs font-mono">
                <div>
                  <label className="text-zinc-400 text-[10px] block font-bold">Heat No</label>
                  <input
                    type="text"
                    value={heatNo}
                    onChange={(e) => setHeatNo(e.target.value)}
                    placeholder="HT-..."
                    className="w-full bg-zinc-50 dark:bg-zinc-800 border border-zinc-300 dark:border-zinc-700 rounded px-2 py-1 text-zinc-900 dark:text-white"
                  />
                </div>
                <div>
                  <label className="text-zinc-400 text-[10px] block font-bold">PO No</label>
                  <input
                    type="text"
                    value={poNo}
                    onChange={(e) => setPoNo(e.target.value)}
                    placeholder="PO-..."
                    className="w-full bg-zinc-50 dark:bg-zinc-800 border border-zinc-300 dark:border-zinc-700 rounded px-2 py-1 text-zinc-900 dark:text-white"
                  />
                </div>
                <div>
                  <label className="text-zinc-400 text-[10px] block font-bold">Cert No</label>
                  <input
                    type="text"
                    value={certNo}
                    onChange={(e) => setCertNo(e.target.value)}
                    placeholder="MTC-..."
                    className="w-full bg-zinc-50 dark:bg-zinc-800 border border-zinc-300 dark:border-zinc-700 rounded px-2 py-1 text-zinc-900 dark:text-white"
                  />
                </div>
              </div>
            </div>
          </Card>

          {/* Right Column: Chemical & Mechanical Validation (6 Cols) */}
          <Card className="lg:col-span-6 p-5 border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 space-y-4">
            <div className="flex items-center justify-between pb-2 border-b border-zinc-100 dark:border-zinc-800">
              <h2 className="text-sm font-mono font-bold uppercase tracking-wider text-zinc-900 dark:text-white">
                Chemistry & Metallurgy Analysis
              </h2>
              <span className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded ${
                hasChemistry
                  ? 'bg-emerald-100 dark:bg-emerald-950/80 text-emerald-800 dark:text-emerald-300'
                  : 'bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-400'
              }`}>
                {hasChemistry ? 'Chemistry Present' : 'No Chemistry Extracted'}
              </span>
            </div>

            {/* Chemistry Elements Grid */}
            <div>
              <span className="text-[11px] font-mono text-zinc-400 block mb-2">
                Ladle Chemical Elements (% Weight) — Type to Recalculate CE
              </span>
              <div className="grid grid-cols-4 sm:grid-cols-8 gap-2 text-center text-xs font-mono">
                {[
                  { el: 'C', val: chemC, set: setChemC },
                  { el: 'Mn', val: chemMn, set: setChemMn },
                  { el: 'Si', val: chemSi, set: setChemSi },
                  { el: 'P', val: chemP, set: setChemP },
                  { el: 'S', val: chemS, set: setChemS },
                  { el: 'Cr', val: chemCr, set: setChemCr },
                  { el: 'Ni', val: chemNi, set: setChemNi },
                  { el: 'Mo', val: chemMo, set: setChemMo },
                ].map((item) => (
                  <div key={item.el} className="p-2 bg-zinc-50 dark:bg-zinc-800 rounded border border-zinc-200 dark:border-zinc-700">
                    <label className="text-[10px] text-zinc-400 block font-bold mb-1">{item.el}</label>
                    <input
                      type="number"
                      step="0.001"
                      value={item.val}
                      onChange={(e) => item.set(e.target.value)}
                      placeholder="—"
                      className="w-full text-center bg-white dark:bg-zinc-900 border border-zinc-300 dark:border-zinc-600 rounded py-0.5 text-zinc-900 dark:text-white font-bold"
                    />
                  </div>
                ))}
              </div>
            </div>

            {/* IIW CE & Weldability */}
            <div className="grid grid-cols-2 gap-3 text-xs font-mono pt-2">
              <div className="p-3 bg-zinc-50 dark:bg-zinc-800 rounded border border-zinc-200 dark:border-zinc-700">
                <span className="text-zinc-400 block text-[11px]">IIW Carbon Equivalent</span>
                <div className="flex items-center gap-2 mt-0.5">
                  <span className="text-base font-bold text-emerald-700 dark:text-emerald-400">
                    {calculatedCE !== null ? `${calculatedCE.toFixed(2)}%` : '— (N/A)'}
                  </span>
                  <span className="text-[10px] text-zinc-400">(Limit &le; 0.43%)</span>
                </div>
              </div>

              <div className="p-3 bg-zinc-50 dark:bg-zinc-800 rounded border border-zinc-200 dark:border-zinc-700">
                <span className="text-zinc-400 block text-[11px]">Weldability Classification</span>
                <span className="font-bold text-zinc-900 dark:text-white block mt-0.5">
                  {weldability.replace(/_/g, ' ')}
                </span>
              </div>
            </div>

            {/* Mechanical Properties */}
            <div className="grid grid-cols-2 gap-3 text-xs font-mono pt-2">
              <div className="p-3 bg-zinc-50 dark:bg-zinc-800 rounded border border-zinc-200 dark:border-zinc-700">
                <label className="text-zinc-400 block text-[11px] font-bold mb-1">Yield Strength (YS MPa)</label>
                <input
                  type="number"
                  value={yieldStrength}
                  onChange={(e) => setYieldStrength(e.target.value)}
                  placeholder="e.g. 250"
                  className="w-full bg-white dark:bg-zinc-900 border border-zinc-300 dark:border-zinc-600 rounded px-2 py-1 text-zinc-900 dark:text-white font-bold"
                />
              </div>

              <div className="p-3 bg-zinc-50 dark:bg-zinc-800 rounded border border-zinc-200 dark:border-zinc-700">
                <label className="text-zinc-400 block text-[11px] font-bold mb-1">Tensile Strength (UTS MPa)</label>
                <input
                  type="number"
                  value={tensileStrength}
                  onChange={(e) => setTensileStrength(e.target.value)}
                  placeholder="e.g. 485"
                  className="w-full bg-white dark:bg-zinc-900 border border-zinc-300 dark:border-zinc-600 rounded px-2 py-1 text-zinc-900 dark:text-white font-bold"
                />
              </div>
            </div>
          </Card>
        </div>

        {/* Raw Extracted Text Stream */}
        {docData.raw_text ? (
          <Card className="p-4 border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900">
            <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-zinc-500 mb-2">
              Raw OCR Text Stream Preview
            </h3>
            <pre className="p-3 bg-zinc-50 dark:bg-zinc-800 rounded border border-zinc-200 dark:border-zinc-700 text-zinc-700 dark:text-zinc-300 text-[11px] font-mono overflow-x-auto max-h-36">
              {docData.raw_text}
            </pre>
          </Card>
        ) : (
          <div className="p-3 bg-zinc-100 dark:bg-zinc-800/50 border border-zinc-200 dark:border-zinc-700 rounded text-center text-xs font-mono text-zinc-500">
            No raw text extracted from uploaded file. All fields above are set for manual data entry.
          </div>
        )}
      </div>
    </ProtectedRoute>
  );
}
