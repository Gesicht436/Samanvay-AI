"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Card, CardHeader } from "@/components/ui/Card";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { useTheme } from "@/components/ThemeProvider";
import { DEPOT_MAP } from "@/lib/constants";
import { commitInventoryBill } from "@/lib/api";
import { formatInr } from "@/lib/formatters";
import { InventoryItemStatus } from "@/lib/types";
import {
  ArrowLeft,
  CheckCircle2,
  AlertCircle,
  Building2,
  Tag,
  Package,
  ShieldCheck,
  RotateCcw,
  FileCheck,
} from "lucide-react";

export default function ReviewPage() {
  const router = useRouter();
  const { activeCpse } = useTheme();

  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Form State
  const [cpse, setCpse] = useState<string>(activeCpse);
  const [depotId, setDepotId] = useState<string>("DEPOT-IOCL-PNP");
  const [depotLocation, setDepotLocation] = useState<string>("Panipat Refinery, Haryana");
  const [skuCode, setSkuCode] = useState<string>("");
  const [description, setDescription] = useState<string>("");
  const [poNo, setPoNo] = useState<string>("");
  const [heatNo, setHeatNo] = useState<string>("");
  const [itemType, setItemType] = useState<string>("FLANGE_WELD_NECK");
  const [sizeNbMm, setSizeNbMm] = useState<number>(100);
  const [pressureClass, setPressureClass] = useState<number>(300);
  const [metallurgy, setMetallurgy] = useState<string>("ASTM A105");
  const [facingEnd, setFacingEnd] = useState<string>("RF");
  const [standard, setStandard] = useState<string>("ASME B16.5");
  const [quantity, setQuantity] = useState<number>(15);
  const [unitCostInr, setUnitCostInr] = useState<number>(12400);
  const [status, setStatus] = useState<InventoryItemStatus>("TO_BE_CONSUMED");
  const [engineerId, setEngineerId] = useState<string>("MAYANK.ANAND (EE-MATERIALS)");
  const [actionNote, setActionNote] = useState<string>(
    "MTC physical & chemical verification verified against ASME B16.5 standards. Material inwarded to unit storage bay."
  );

  // Load draft from sessionStorage or defaults
  useEffect(() => {
    const rawDraft = sessionStorage.getItem("samanvay_review_draft");
    if (rawDraft) {
      try {
        const draft = JSON.parse(rawDraft);
        if (draft.cpse) setCpse(draft.cpse);
        if (draft.poNo) setPoNo(draft.poNo);
        if (draft.heatNumber) setHeatNo(draft.heatNumber);
        if (draft.materialGrade) setMetallurgy(draft.materialGrade);
        if (draft.standard) setStandard(draft.standard);
        if (draft.primaryItem) setDescription(draft.primaryItem);

        // Generate realistic initial SKU
        setSkuCode(`${draft.cpse || activeCpse}-INW-${Math.floor(100000 + Math.random() * 900000)}`);

        // Update depot default based on CPSE
        const defaultDepots = DEPOT_MAP[draft.cpse || activeCpse] || DEPOT_MAP.IOCL;
        if (defaultDepots.length > 0) {
          setDepotId(defaultDepots[0].id);
          setDepotLocation(defaultDepots[0].location);
        }
      } catch {
        // Fallback to normal default
      }
    } else {
      setSkuCode(`${activeCpse}-INW-${Math.floor(100000 + Math.random() * 900000)}`);
      setDescription('FLANGE, WELD NECK, 4" (DN100), CLASS 300, ASTM A105, RF, ASME B16.5');
      setPoNo(`PO-${activeCpse}-2026-9041`);
      setHeatNo("HT-2026-8819A");

      const defaultDepots = DEPOT_MAP[activeCpse] || DEPOT_MAP.IOCL;
      if (defaultDepots.length > 0) {
        setDepotId(defaultDepots[0].id);
        setDepotLocation(defaultDepots[0].location);
      }
    }
  }, [activeCpse]);

  const handleCpseChange = (newCpse: string) => {
    setCpse(newCpse);
    const depots = DEPOT_MAP[newCpse] || [];
    if (depots.length > 0) {
      setDepotId(depots[0].id);
      setDepotLocation(depots[0].location);
    }
    setSkuCode(`${newCpse}-INW-${Math.floor(100000 + Math.random() * 900000)}`);
  };

  const handleDepotChange = (newDepotId: string) => {
    setDepotId(newDepotId);
    const depots = DEPOT_MAP[cpse] || [];
    const found = depots.find((d) => d.id === newDepotId);
    if (found) setDepotLocation(found.location);
  };

  const totalValuation = quantity * unitCostInr;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setErrorMsg(null);
    setSuccessMsg(null);

    try {
      await commitInventoryBill({
        sku_code: skuCode,
        cpse,
        depot_id: depotId,
        depot_location: depotLocation,
        description,
        quantity,
        unit_cost_inr: unitCostInr,
        status,
        po_no: poNo,
        heat_no: heatNo,
        item_type: itemType,
        size_nb_mm: Number(sizeNbMm),
        pressure_class: Number(pressureClass),
        metallurgy,
        facing_end: facingEnd,
        standard,
        engineer_id: engineerId,
        action_note: actionNote,
      });

      setSuccessMsg("Inward item successfully committed to central plant inventory and Neo4j ledger!");
      sessionStorage.removeItem("samanvay_review_draft");

      setTimeout(() => {
        router.push("/inventory");
      }, 1200);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to commit inventory item. Please verify fields and try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Top Breadcrumb & Actions */}
      <div className="flex items-center justify-between">
        <Link
          href="/upload"
          className="inline-flex items-center gap-1.5 text-xs text-[var(--text-secondary)] hover:text-[var(--text-primary)] font-medium transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Upload & OCR</span>
        </Link>
        <span className="text-[11px] font-mono text-[var(--text-muted)]">
          Stage: Site Engineer Inward Verification
        </span>
      </div>

      {/* Header Banner */}
      <div>
        <h1 className="text-xl font-bold text-[var(--text-primary)]">
          Site Engineer Inward Procurement Review
        </h1>
        <p className="text-xs text-[var(--text-secondary)] mt-1">
          Review extracted technical specifications, assign initial lifecycle tags, adjust quantities or metallurgy, and commit the verified asset to the plant inventory ledger.
        </p>
      </div>

      {/* Alerts */}
      {errorMsg && (
        <div className="p-3 rounded-lg bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800 text-rose-800 dark:text-rose-300 text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {successMsg && (
        <div className="p-3 rounded-lg bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 text-emerald-800 dark:text-emerald-300 text-xs flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 shrink-0" />
          <span>{successMsg}</span>
        </div>
      )}

      {/* Form Card */}
      <form onSubmit={handleSubmit}>
        <Card className="space-y-6">
          {/* Section 1: Inward Identification & Depot */}
          <div>
            <div className="text-xs font-bold uppercase tracking-wider text-[var(--accent-primary)] mb-3 flex items-center gap-1.5">
              <Building2 className="w-4 h-4" />
              1. Facility & Receiving Depot
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div>
                <label className="text-[11px] font-semibold text-[var(--text-secondary)] block mb-1">
                  Receiving CPSE Enterprise
                </label>
                <select
                  value={cpse}
                  onChange={(e) => handleCpseChange(e.target.value)}
                  className="app-input w-full cursor-pointer"
                  required
                >
                  <option value="IOCL">IOCL — Indian Oil Corporation</option>
                  <option value="ONGC">ONGC — Oil & Natural Gas Corp</option>
                  <option value="BPCL">BPCL — Bharat Petroleum Corp</option>
                  <option value="HPCL">HPCL — Hindustan Petroleum Corp</option>
                  <option value="GAIL">GAIL — GAIL (India) Limited</option>
                </select>
              </div>

              <div>
                <label className="text-[11px] font-semibold text-[var(--text-secondary)] block mb-1">
                  Receiving Depot / Refinery
                </label>
                <select
                  value={depotId}
                  onChange={(e) => handleDepotChange(e.target.value)}
                  className="app-input w-full cursor-pointer"
                  required
                >
                  {(DEPOT_MAP[cpse] || []).map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.name} ({d.state})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-[11px] font-semibold text-[var(--text-secondary)] block mb-1">
                  Assigned Material SKU
                </label>
                <input
                  type="text"
                  value={skuCode}
                  onChange={(e) => setSkuCode(e.target.value)}
                  className="app-input w-full font-mono"
                  placeholder="e.g. IOCL-INW-00412"
                  required
                />
              </div>
            </div>
          </div>

          {/* Section 2: Procurement Document Details */}
          <div className="pt-4 border-t border-[var(--border-subtle)]">
            <div className="text-xs font-bold uppercase tracking-wider text-[var(--accent-primary)] mb-3 flex items-center gap-1.5">
              <FileCheck className="w-4 h-4" />
              2. Procurement Bill & Inspection Traceability
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="text-[11px] font-semibold text-[var(--text-secondary)] block mb-1">
                  Purchase Order (PO) Number
                </label>
                <input
                  type="text"
                  value={poNo}
                  onChange={(e) => setPoNo(e.target.value)}
                  className="app-input w-full font-mono"
                  placeholder="e.g. PO-IOCL-2026-9912"
                />
              </div>
              <div>
                <label className="text-[11px] font-semibold text-[var(--text-secondary)] block mb-1">
                  MTC Heat / Melt Cast Number
                </label>
                <input
                  type="text"
                  value={heatNo}
                  onChange={(e) => setHeatNo(e.target.value)}
                  className="app-input w-full font-mono text-emerald-600 dark:text-emerald-400"
                  placeholder="e.g. HT-2026-9981B"
                />
              </div>
            </div>
          </div>

          {/* Section 3: Engineering Technical Specs */}
          <div className="pt-4 border-t border-[var(--border-subtle)]">
            <div className="text-xs font-bold uppercase tracking-wider text-[var(--accent-primary)] mb-3 flex items-center gap-1.5">
              <Package className="w-4 h-4" />
              3. Technical Specifications & Governing Standards
            </div>

            <div className="space-y-3">
              <div>
                <label className="text-[11px] font-semibold text-[var(--text-secondary)] block mb-1">
                  Item Description (Standardized Refinery Title)
                </label>
                <input
                  type="text"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="app-input w-full font-medium"
                  required
                />
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
                <div>
                  <label className="text-[11px] font-semibold text-[var(--text-secondary)] block mb-1">
                    Equipment Type
                  </label>
                  <select
                    value={itemType}
                    onChange={(e) => setItemType(e.target.value)}
                    className="app-input w-full cursor-pointer text-xs"
                  >
                    <option value="FLANGE_WELD_NECK">Flange Weld Neck</option>
                    <option value="FLANGE_BLIND">Flange Blind</option>
                    <option value="GATE_VALVE">Gate Valve</option>
                    <option value="BALL_VALVE">Ball Valve</option>
                    <option value="CHECK_VALVE">Check Valve</option>
                    <option value="ELBOW_BUTTWELD">Buttweld Elbow</option>
                    <option value="PIPE_SEAMLESS">Seamless Pipe</option>
                    <option value="GASKET_SPIRAL_WOUND">Spiral Gasket</option>
                    <option value="STUD_BOLT">Stud Bolt Assembly</option>
                    <option value="MOTOR_FLAMEPROOF">Flameproof Motor</option>
                    <option value="MECHANICAL_SEAL">Mechanical Seal</option>
                  </select>
                </div>

                <div>
                  <label className="text-[11px] font-semibold text-[var(--text-secondary)] block mb-1">
                    Size NB (mm)
                  </label>
                  <select
                    value={sizeNbMm}
                    onChange={(e) => setSizeNbMm(Number(e.target.value))}
                    className="app-input w-full cursor-pointer font-mono"
                  >
                    <option value={25}>25mm (1&quot;)</option>
                    <option value={40}>40mm (1.5&quot;)</option>
                    <option value={50}>50mm (2&quot;)</option>
                    <option value={80}>80mm (3&quot;)</option>
                    <option value={100}>100mm (4&quot;)</option>
                    <option value={150}>150mm (6&quot;)</option>
                    <option value={200}>200mm (8&quot;)</option>
                    <option value={250}>250mm (10&quot;)</option>
                    <option value={300}>300mm (12&quot;)</option>
                  </select>
                </div>

                <div>
                  <label className="text-[11px] font-semibold text-[var(--text-secondary)] block mb-1">
                    Pressure Class
                  </label>
                  <select
                    value={pressureClass}
                    onChange={(e) => setPressureClass(Number(e.target.value))}
                    className="app-input w-full cursor-pointer font-mono"
                  >
                    <option value={150}>Class 150</option>
                    <option value={300}>Class 300</option>
                    <option value={600}>Class 600</option>
                    <option value={900}>Class 900</option>
                    <option value={1500}>Class 1500</option>
                    <option value={2500}>Class 2500</option>
                  </select>
                </div>

                <div>
                  <label className="text-[11px] font-semibold text-[var(--text-secondary)] block mb-1">
                    Metallurgy
                  </label>
                  <input
                    type="text"
                    value={metallurgy}
                    onChange={(e) => setMetallurgy(e.target.value)}
                    className="app-input w-full font-mono text-xs"
                    placeholder="e.g. ASTM A105"
                  />
                </div>

                <div>
                  <label className="text-[11px] font-semibold text-[var(--text-secondary)] block mb-1">
                    Facing / Standard
                  </label>
                  <input
                    type="text"
                    value={`${facingEnd} / ${standard}`}
                    onChange={(e) => {
                      const parts = e.target.value.split("/");
                      if (parts[0]) setFacingEnd(parts[0].trim());
                      if (parts[1]) setStandard(parts[1].trim());
                    }}
                    className="app-input w-full font-mono text-xs"
                    placeholder="e.g. RF / ASME B16.5"
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Section 4: Quantity & Pricing */}
          <div className="pt-4 border-t border-[var(--border-subtle)]">
            <div className="text-xs font-bold uppercase tracking-wider text-[var(--accent-primary)] mb-3 flex items-center gap-1.5">
              <Tag className="w-4 h-4" />
              4. Inward Quantity & Stock Valuation
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div>
                <label className="text-[11px] font-semibold text-[var(--text-secondary)] block mb-1">
                  Inward Quantity (Units)
                </label>
                <input
                  type="number"
                  min="1"
                  value={quantity}
                  onChange={(e) => setQuantity(Math.max(1, parseInt(e.target.value) || 1))}
                  className="app-input w-full font-mono font-bold"
                  required
                />
              </div>

              <div>
                <label className="text-[11px] font-semibold text-[var(--text-secondary)] block mb-1">
                  Unit Cost (INR)
                </label>
                <input
                  type="number"
                  min="0"
                  value={unitCostInr}
                  onChange={(e) => setUnitCostInr(Math.max(0, parseFloat(e.target.value) || 0))}
                  className="app-input w-full font-mono"
                  required
                />
              </div>

              <div>
                <label className="text-[11px] font-semibold text-[var(--text-secondary)] block mb-1">
                  Total Valuation (Computed)
                </label>
                <div className="app-input w-full bg-[var(--bg-tertiary)] font-mono font-bold text-[var(--accent-primary)] flex items-center">
                  {formatInr(totalValuation)}
                </div>
              </div>
            </div>
          </div>

          {/* Section 5: Initial Lifecycle Tag Selection */}
          <div className="pt-4 border-t border-[var(--border-subtle)]">
            <div className="text-xs font-bold uppercase tracking-wider text-[var(--accent-primary)] mb-3 flex items-center gap-1.5">
              <ShieldCheck className="w-4 h-4" />
              5. Initial Lifecycle Tag (Required by MoPNG Protocol)
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {/* Option A: To Be Consumed */}
              <label
                className={`p-3.5 rounded-lg border cursor-pointer transition-all flex items-start gap-3 ${
                  status === "TO_BE_CONSUMED"
                    ? "bg-amber-50/70 dark:bg-amber-950/30 border-amber-400 dark:border-amber-600 shadow-xs"
                    : "border-[var(--border-primary)] hover:bg-[var(--bg-tertiary)]"
                }`}
              >
                <input
                  type="radio"
                  name="lifecycle_status"
                  value="TO_BE_CONSUMED"
                  checked={status === "TO_BE_CONSUMED"}
                  onChange={() => setStatus("TO_BE_CONSUMED")}
                  className="mt-0.5"
                />
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-[var(--text-primary)]">
                      To Be Consumed (Allocated)
                    </span>
                    <StatusBadge status="TO_BE_CONSUMED" showDot={false} />
                  </div>
                  <p className="text-[11px] text-[var(--text-secondary)] mt-1 leading-relaxed">
                    Reserved for scheduled maintenance / upcoming turnaround. Private to plant; <strong>not broadcasted</strong> to other CPSEs.
                    If unconsumed after 90 days, the system prompts you to transition it to Idle Surplus.
                  </p>
                </div>
              </label>

              {/* Option B: In Storage */}
              <label
                className={`p-3.5 rounded-lg border cursor-pointer transition-all flex items-start gap-3 ${
                  status === "IN_STORAGE"
                    ? "bg-blue-50/70 dark:bg-blue-950/30 border-blue-400 dark:border-blue-600 shadow-xs"
                    : "border-[var(--border-primary)] hover:bg-[var(--bg-tertiary)]"
                }`}
              >
                <input
                  type="radio"
                  name="lifecycle_status"
                  value="IN_STORAGE"
                  checked={status === "IN_STORAGE"}
                  onChange={() => setStatus("IN_STORAGE")}
                  className="mt-0.5"
                />
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-[var(--text-primary)]">
                      In Storage (Warehouse Reserve)
                    </span>
                    <StatusBadge status="IN_STORAGE" showDot={false} />
                  </div>
                  <p className="text-[11px] text-[var(--text-secondary)] mt-1 leading-relaxed">
                    General buffer warehouse inventory maintained for plant operational reliability. Can be manually or automatically flagged as Idle Surplus when dormant.
                  </p>
                </div>
              </label>
            </div>
          </div>

          {/* Section 6: Engineer Verification Note */}
          <div className="pt-4 border-t border-[var(--border-subtle)] space-y-3">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="text-[11px] font-semibold text-[var(--text-secondary)] block mb-1">
                  Site Engineer Officer ID
                </label>
                <input
                  type="text"
                  value={engineerId}
                  onChange={(e) => setEngineerId(e.target.value)}
                  className="app-input w-full font-mono text-xs"
                  required
                />
              </div>
              <div>
                <label className="text-[11px] font-semibold text-[var(--text-secondary)] block mb-1">
                  Inward Action / Justification Note
                </label>
                <input
                  type="text"
                  value={actionNote}
                  onChange={(e) => setActionNote(e.target.value)}
                  className="app-input w-full text-xs"
                />
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="pt-4 border-t border-[var(--border-subtle)] flex items-center justify-end gap-3">
            <button
              type="button"
              onClick={() => router.push("/upload")}
              className="btn-secondary"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="btn-primary py-2 px-5 text-xs shadow-xs"
            >
              {loading ? (
                <>
                  <RotateCcw className="w-3.5 h-3.5 animate-spin" />
                  <span>Committing to Inventory...</span>
                </>
              ) : (
                <>
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>Commit to Plant Inventory Ledger</span>
                </>
              )}
            </button>
          </div>
        </Card>
      </form>
    </div>
  );
}
