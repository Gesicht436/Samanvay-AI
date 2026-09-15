"use client";

import { useEffect, useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import {
  fetchRequisitions,
  approveRequisition,
  createRequisition,
  rejectRequisition,
  dispatchRequisition,
  deliverRequisition,
  fetchDepots,
  estimateRoute,
  fetchInventoryLocks,
  verifyGatePass,
} from "@/lib/api";
import {
  InterCPSERequisition,
  DigitalMaterialGatePass,
  UrgencyLevel,
  DepotLocation,
  RouteEstimate,
  InventoryLock,
  GatePassVerification,
} from "@/lib/types";
import {
  Truck,
  CheckCircle2,
  AlertTriangle,
  PlusCircle,
  FileText,
  Printer,
  X,
  ArrowRight,
  Copy,
  Check,
  ShieldCheck,
  Lock,
  RotateCcw,
  MapPin,
  Clock,
  Download,
} from "lucide-react";
import { exportToCsv } from "@/lib/exportUtils";

function TransfersContent() {
  const searchParams = useSearchParams();


  const [requisitions, setRequisitions] = useState<InterCPSERequisition[]>([]);
  const [depots, setDepots] = useState<DepotLocation[]>([]);
  const [inventoryLocks, setInventoryLocks] = useState<InventoryLock[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedTab, setSelectedTab] = useState<string>("ALL");
  const [copiedHash, setCopiedHash] = useState(false);

  // Modals state
  const [activeGatePass, setActiveGatePass] = useState<DigitalMaterialGatePass | null>(null);
  const [gatePassVerification, setGatePassVerification] = useState<GatePassVerification | null>(null);
  const [verifyingPass, setVerifyingPass] = useState(false);

  const [approvingReq, setApprovingReq] = useState<InterCPSERequisition | null>(null);
  const [rejectingReq, setRejectingReq] = useState<InterCPSERequisition | null>(null);
  const [rejectReason, setRejectReason] = useState("Material reserved for imminent internal unit turnaround maintenance.");

  const [isNewIndentModalOpen, setIsNewIndentModalOpen] = useState(false);
  const [submittingApproval, setSubmittingApproval] = useState(false);
  const [submittingNewReq, setSubmittingNewReq] = useState(false);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  // Route preview in New Indent modal
  const [routePreview, setRoutePreview] = useState<RouteEstimate | null>(null);
  const [calculatingRoute, setCalculatingRoute] = useState(false);

  // Approval Form State
  const [approvalForm, setApprovalForm] = useState({
    approver_name: "Dr. S. K. Roy, Executive Director (Materials, ONGC)",
    vehicle_no: "HR-06-EA-8841",
    driver_name: "Rajesh Kumar Yadav",
    driver_id_no: "DL-042019948123",
  });

  // New Requisition Form State
  const [newReqForm, setNewReqForm] = useState({
    source_cpse: "BPCL",
    source_depot: "Mumbai Refinery, Mahul, Maharashtra",
    source_unit: "FCCU (Fluid Catalytic Cracking Unit)",
    target_cpse: "ONGC",
    target_depot: "Uran Plant, Maharashtra",
    sku_code: "ONGC-MAT-0005512",
    item_description: "MOTOR FLAMEPROOF 37KW 4P 415V EX D IIC T4 GB 1500RPM",
    required_qty: 2,
    unit_cost_inr: 185000,
    justification: "Main reflux pump drive motor high bearing vibration. Inter-depot requisition.",
    urgency_level: "EMERGENCY_SHUTDOWN" as UrgencyLevel,
  });

  useEffect(() => {
    loadData();

    // Auto-fill from search params if opened from Dashboard
    const paramSku = searchParams.get("sku");
    if (paramSku) {
      setNewReqForm((prev) => ({
        ...prev,
        sku_code: paramSku,
        target_cpse: searchParams.get("target_cpse") || prev.target_cpse,
        target_depot: searchParams.get("target_depot") || prev.target_depot,
        item_description: searchParams.get("desc") || prev.item_description,
        required_qty: parseInt(searchParams.get("qty") || "1"),
        unit_cost_inr: parseFloat(searchParams.get("cost") || "15000"),
        justification: "Inter-depot transfer requisition initiated from catalog search.",
      }));
      setIsNewIndentModalOpen(true);
    }
  }, [searchParams]);

  // Recalculate route whenever origin or target depot changes
  useEffect(() => {
    if (!isNewIndentModalOpen) return;
    const calc = async () => {
      setCalculatingRoute(true);
      try {
        const est = await estimateRoute(newReqForm.target_depot, newReqForm.source_depot, 1.2);
        setRoutePreview(est);
      } catch {
        setRoutePreview(null);
      } finally {
        setCalculatingRoute(false);
      }
    };
    calc();
  }, [newReqForm.source_depot, newReqForm.target_depot, isNewIndentModalOpen]);

  const loadData = async () => {
    setLoading(true);
    const [reqs, depotList, locks] = await Promise.all([
      fetchRequisitions(),
      fetchDepots(),
      fetchInventoryLocks(),
    ]);
    setRequisitions(reqs);
    setDepots(depotList);
    setInventoryLocks(locks);
    setLoading(false);
  };

  const handleApproveSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!approvingReq) return;
    setSubmittingApproval(true);
    try {
      const updated = await approveRequisition(approvingReq.requisition_id, approvalForm);
      setRequisitions((prev) =>
        prev.map((item) => (item.requisition_id === updated.requisition_id ? updated : item))
      );
      setApprovingReq(null);
      setActiveGatePass(updated.gate_pass || null);
      setGatePassVerification(null);
      // Refresh inventory locks
      const updatedLocks = await fetchInventoryLocks();
      setInventoryLocks(updatedLocks);
    } finally {
      setSubmittingApproval(false);
    }
  };

  const handleRejectSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!rejectingReq) return;
    setActionLoading(rejectingReq.requisition_id);
    try {
      const updated = await rejectRequisition(rejectingReq.requisition_id, {
        rejection_reason: rejectReason,
        rejected_by: "Dr. S. K. Roy, Executive Director (Materials)",
      });
      setRequisitions((prev) =>
        prev.map((item) => (item.requisition_id === updated.requisition_id ? updated : item))
      );
      setRejectingReq(null);
      const updatedLocks = await fetchInventoryLocks();
      setInventoryLocks(updatedLocks);
    } finally {
      setActionLoading(null);
    }
  };

  const handleDispatch = async (reqId: string) => {
    setActionLoading(reqId);
    try {
      const updated = await dispatchRequisition(reqId);
      setRequisitions((prev) =>
        prev.map((item) => (item.requisition_id === updated.requisition_id ? updated : item))
      );
    } finally {
      setActionLoading(null);
    }
  };

  const handleDeliver = async (reqId: string) => {
    setActionLoading(reqId);
    try {
      const updated = await deliverRequisition(reqId);
      setRequisitions((prev) =>
        prev.map((item) => (item.requisition_id === updated.requisition_id ? updated : item))
      );
      const updatedLocks = await fetchInventoryLocks();
      setInventoryLocks(updatedLocks);
    } finally {
      setActionLoading(null);
    }
  };

  const handleVerifyGatePass = async (gatePassNo: string) => {
    setVerifyingPass(true);
    try {
      const result = await verifyGatePass(gatePassNo);
      setGatePassVerification(result);
    } finally {
      setVerifyingPass(false);
    }
  };

  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmittingNewReq(true);
    try {
      const created = await createRequisition(newReqForm);
      setRequisitions((prev) => [created, ...prev]);
      setIsNewIndentModalOpen(false);
      const updatedLocks = await fetchInventoryLocks();
      setInventoryLocks(updatedLocks);
    } catch (err: any) {
      alert(err.message || "Failed to create requisition.");
    } finally {
      setSubmittingNewReq(false);
    }
  };

  const handleCopyHash = (hash: string) => {
    navigator.clipboard.writeText(hash);
    setCopiedHash(true);
    setTimeout(() => setCopiedHash(false), 2000);
  };

  // Presets for new indent without buzzwords or emojis
  const loadPreset = (presetKey: string) => {
    if (presetKey === "motor") {
      setNewReqForm({
        source_cpse: "BPCL",
        source_depot: "Mumbai Refinery, Mahul, Maharashtra",
        source_unit: "FCCU Unit",
        target_cpse: "ONGC",
        target_depot: "Uran Plant, Maharashtra",
        sku_code: "ONGC-MAT-0005512",
        item_description: "MOTOR FLAMEPROOF 37KW 4P 415V EX D IIC T4 GB 1500RPM",
        required_qty: 2,
        unit_cost_inr: 185000,
        justification: "Main reflux pump drive motor high bearing vibration. Requisition from Uran.",
        urgency_level: "EMERGENCY_SHUTDOWN",
      });
    } else if (presetKey === "flange") {
      setNewReqForm({
        source_cpse: "IOCL",
        source_depot: "Panipat Refinery, Haryana",
        source_unit: "Crude Distillation Unit (CDU-2)",
        target_cpse: "ONGC",
        target_depot: "Hazira Gas Processing Plant, Gujarat",
        sku_code: "ONGC-MAT-0000092",
        item_description: 'FLANGE, WELD NECK, 4" (DN100), CLASS 300, ASTM A105, RF, ASME B16.5',
        required_qty: 15,
        unit_cost_inr: 12400,
        justification: "Critical path replacement for turnaround shutdown maintenance.",
        urgency_level: "EMERGENCY_SHUTDOWN",
      });
    } else if (presetKey === "seal") {
      setNewReqForm({
        source_cpse: "IOCL",
        source_depot: "Mathura Refinery, Uttar Pradesh",
        source_unit: "Hydrocracker Heavy Oil Pump P-102B",
        target_cpse: "BPCL",
        target_depot: "Mumbai Refinery, Mahul, Maharashtra",
        sku_code: "BPCL-SAP-0008891",
        item_description: "SEAL MECHANICAL 50MM CARTRIDGE DUAL PRESSURIZED PLAN 53A SIC/SIC API 682",
        required_qty: 4,
        unit_cost_inr: 92000,
        justification: "API 682 Plan 53A barrier fluid seal leak detected on hydrocarbon pump.",
        urgency_level: "PLANNED_MAINTENANCE",
      });
    } else if (presetKey === "bearing") {
      setNewReqForm({
        source_cpse: "ONGC",
        source_depot: "Ankleshwar Asset, Gujarat",
        source_unit: "Gas Compressor Substation",
        target_cpse: "IOCL",
        target_depot: "Gujarat Refinery (Koyali), Vadodara",
        sku_code: "IOCL-SAP-0004120",
        item_description: "BEARING DEEP GROOVE BALL 50X110X27MM C3 CLEARANCE SKF ISO 15 (6310-2RS1/C3)",
        required_qty: 10,
        unit_cost_inr: 14200,
        justification: "Compressor auxiliary motor preventative bearing replacement under ISO 15.",
        urgency_level: "ROUTINE",
      });
    }
  };

  const pendingCount = requisitions.filter((r) => r.status === "PENDING_APPROVAL").length;
  const approvedCount = requisitions.filter((r) => r.status === "APPROVED_FOR_DISPATCH").length;
  const inTransitCount = requisitions.filter((r) => r.status === "IN_TRANSIT").length;
  const deliveredCount = requisitions.filter((r) => r.status === "DELIVERED").length;

  const filteredRequisitions = requisitions.filter((r) => {
    if (selectedTab === "ALL") return true;
    if (selectedTab === "EMERGENCY_SHUTDOWN") return r.urgency_level === "EMERGENCY_SHUTDOWN";
    return r.status === selectedTab;
  });

  const handleExportTransfersCsv = () => {
    exportToCsv(filteredRequisitions, "Samanvay_Transfer_Indents", {
      requisition_id: "Indent ID",
      created_at: "Created Date",
      source_cpse: "Recipient CPSE",
      source_depot: "Recipient Depot",
      source_unit: "Recipient Unit",
      target_cpse: "Donor CPSE",
      target_depot: "Donor Depot",
      sku_code: "SKU Code",
      item_description: "Item Description",
      required_qty: "Quantity",
      unit_cost_inr: "Unit Cost (INR)",
      total_value_inr: "Total Value (INR)",
      urgency_level: "Priority Level",
      status: "Status",
      approved_by: "Approving Officer",
    });
  };

  return (
    <div className="space-y-4">
      {/* 1. Header */}
      <div className="bg-white border border-[#d5d9d9] rounded p-4 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-lg font-bold text-[#0f1111]">
            Inter-Depot Material Transfers & Gate Passes
          </h1>
          <p className="text-xs text-[#565959] mt-0.5">
            Cross-CPSE material transfer indents, automated inventory reservation locks, and official CISF outward gate passes.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleExportTransfersCsv}
            className="btn-amazon-white px-3 py-1.5 rounded text-xs font-semibold flex items-center gap-1.5 cursor-pointer"
            title="Export filtered indents to CSV/Excel"
          >
            <Download className="w-3.5 h-3.5 text-[#565959]" />
            Export CSV
          </button>

          <button
            onClick={() => setSelectedTab(selectedTab === "INVENTORY_LOCKS" ? "ALL" : "INVENTORY_LOCKS")}
            className={`px-3 py-1.5 rounded text-xs font-semibold border transition-all flex items-center gap-1.5 cursor-pointer ${
              selectedTab === "INVENTORY_LOCKS"
                ? "bg-[#232f3e] text-white border-[#232f3e]"
                : "bg-white text-[#0f1111] border-[#d5d9d9] hover:bg-[#f7fafa]"
            }`}
          >
            <Lock className="w-3.5 h-3.5 text-[#ff9900]" />
            Surplus Reservation Locks ({inventoryLocks.length})
          </button>

          <button
            onClick={() => setIsNewIndentModalOpen(true)}
            className="btn-amazon-primary px-3.5 py-1.5 rounded text-xs font-bold transition-all flex items-center gap-1.5 cursor-pointer shadow-sm"
          >
            <PlusCircle className="w-3.5 h-3.5 text-[#0f1111]" />
            Create Transfer Indent
          </button>
        </div>
      </div>


      {/* 2. Filter Tabs */}
      <div className="flex items-center gap-1 border-b border-[#d5d9d9] pb-1 overflow-x-auto text-xs font-semibold">
        {[
          { id: "ALL", label: `All Indents (${requisitions.length})` },
          { id: "PENDING_APPROVAL", label: `Pending Approval (${pendingCount})` },
          { id: "APPROVED_FOR_DISPATCH", label: `Approved (${approvedCount})` },
          { id: "IN_TRANSIT", label: `In-Transit (${inTransitCount})` },
          { id: "DELIVERED", label: `Delivered (${deliveredCount})` },
          { id: "EMERGENCY_SHUTDOWN", label: "Emergency Priority" },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setSelectedTab(tab.id)}
            className={`px-3 py-1.5 rounded transition-all cursor-pointer whitespace-nowrap ${
              selectedTab === tab.id
                ? "bg-[#232f3e] text-[#ff9900] font-bold"
                : "text-[#565959] hover:text-[#0f1111] hover:bg-[#eaeded]"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* 3. Main Content: Requisitions Table or Inventory Locks */}
      {selectedTab === "INVENTORY_LOCKS" ? (
        <div className="bg-white border border-[#d5d9d9] rounded overflow-hidden shadow-sm">
          <div className="p-3 bg-[#f8f9fa] border-b border-[#d5d9d9] flex items-center justify-between">
            <div>
              <h2 className="text-xs font-bold text-[#0f1111] uppercase tracking-wider">
                Real-Time Surplus Inventory Reservation Ledger
              </h2>
              <p className="text-[11px] text-[#565959]">
                Prevents duplicate requisitions and race conditions by locking stock when indents are created.
              </p>
            </div>
            <span className="text-xs font-mono font-bold text-[#007185]">
              {inventoryLocks.filter((l) => l.lock_status !== "AVAILABLE").length} Active Locks
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead className="bg-[#f2f3f3] text-[#565959] font-bold uppercase tracking-wider border-b border-[#d5d9d9]">
                <tr>
                  <th className="py-2.5 px-3">SKU Code</th>
                  <th className="py-2.5 px-3">Depot & Owner CPSE</th>
                  <th className="py-2.5 px-3">Material Description</th>
                  <th className="py-2.5 px-3 text-center">Total Stock</th>
                  <th className="py-2.5 px-3 text-center">Available Stock</th>
                  <th className="py-2.5 px-3 text-center">Reserved Stock</th>
                  <th className="py-2.5 px-3">Reservation Status</th>
                  <th className="py-2.5 px-3">Active Indents</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#e5e7eb] text-[#0f1111]">
                {inventoryLocks.map((lock) => (
                  <tr key={lock.sku_code} className="hover:bg-[#f7fafa]">
                    <td className="py-2.5 px-3 font-mono font-bold">{lock.sku_code}</td>
                    <td className="py-2.5 px-3">
                      <span className="font-bold">{lock.cpse}</span>
                      <div className="text-[11px] text-[#565959]">{lock.depot}</div>
                    </td>
                    <td className="py-2.5 px-3 max-w-xs truncate">{lock.item_description}</td>
                    <td className="py-2.5 px-3 text-center font-semibold">{lock.total_stock}</td>
                    <td className="py-2.5 px-3 text-center font-bold text-[#067d62]">
                      {lock.available_stock}
                    </td>
                    <td className="py-2.5 px-3 text-center font-bold text-[#b12704]">
                      {lock.reserved_stock}
                    </td>
                    <td className="py-2.5 px-3">
                      {lock.lock_status === "AVAILABLE" && (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-50 text-[#067d62] border border-emerald-300">
                          <Check className="w-3 h-3" /> Available
                        </span>
                      )}
                      {lock.lock_status === "PARTIALLY_RESERVED" && (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold bg-amber-50 text-[#b12704] border border-amber-300">
                          <Lock className="w-3 h-3" /> Reserved
                        </span>
                      )}
                      {lock.lock_status === "LOCKED" && (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold bg-red-50 text-[#c40000] border border-red-300">
                          <Lock className="w-3 h-3" /> Fully Locked
                        </span>
                      )}
                    </td>
                    <td className="py-2.5 px-3 font-mono text-[11px] text-[#007185]">
                      {lock.active_requisition_ids.length > 0 ? (
                        lock.active_requisition_ids.join(", ")
                      ) : (
                        <span className="text-[#565959]">—</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        <div className="bg-white border border-[#d5d9d9] rounded overflow-hidden shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead className="bg-[#f2f3f3] text-[#565959] font-bold uppercase tracking-wider border-b border-[#d5d9d9]">
                <tr>
                  <th className="py-2.5 px-3">Indent ID & Date</th>
                  <th className="py-2.5 px-3">Routing (Recipient &rarr; Donor)</th>
                  <th className="py-2.5 px-3">Material Description & SKU</th>
                  <th className="py-2.5 px-3 text-center">Quantity</th>
                  <th className="py-2.5 px-3 text-right">Total Cost</th>
                  <th className="py-2.5 px-3">Status</th>
                  <th className="py-2.5 px-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#e5e7eb] text-[#0f1111]">
                {loading ? (
                  <tr>
                    <td colSpan={7} className="py-10 text-center text-[#565959]">
                      Loading transfer indents...
                    </td>
                  </tr>
                ) : filteredRequisitions.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="py-10 text-center text-[#565959]">
                      No transfer indents found matching the selected filter.
                    </td>
                  </tr>
                ) : (
                  filteredRequisitions.map((req) => (
                    <tr key={req.requisition_id} className="hover:bg-[#f7fafa] transition-colors">
                      <td className="py-2.5 px-3 align-top">
                        <div className="font-mono font-bold text-xs text-[#0f1111]">
                          {req.requisition_id}
                        </div>
                        <div className="text-[10px] text-[#565959] mt-0.5">
                          {new Date(req.created_at).toLocaleDateString("en-IN", {
                            day: "numeric",
                            month: "short",
                            year: "numeric",
                          })}
                        </div>
                        {req.urgency_level === "EMERGENCY_SHUTDOWN" && (
                          <div className="text-[10px] text-[#c40000] font-bold mt-0.5">
                            Emergency Priority
                          </div>
                        )}
                      </td>

                      <td className="py-2.5 px-3 align-top space-y-0.5">
                        <div className="text-xs font-semibold">
                          <span className="font-bold">{req.source_cpse}</span> ({req.source_depot.split(",")[0]})
                        </div>
                        <div className="flex items-center gap-1 text-[11px] text-[#565959]">
                          <ArrowRight className="w-3 h-3 text-slate-400 shrink-0" />
                          <span>From:</span>
                          <strong>{req.target_cpse} ({req.target_depot.split(",")[0]})</strong>
                        </div>
                      </td>

                      <td className="py-2.5 px-3 align-top max-w-xs">
                        <div className="font-semibold text-[#0f1111] line-clamp-2">
                          {req.item_description}
                        </div>
                        <div className="font-mono text-[10px] text-[#007185] mt-0.5">
                          SKU: {req.sku_code}
                        </div>
                      </td>

                      <td className="py-2.5 px-3 align-top text-center font-bold">
                        {req.required_qty} Units
                      </td>

                      <td className="py-2.5 px-3 align-top text-right font-mono font-bold">
                        ₹{req.total_value_inr.toLocaleString("en-IN")}
                      </td>

                      <td className="py-2.5 px-3 align-top">
                        {req.status === "PENDING_APPROVAL" && (
                          <span className="inline-block px-2 py-0.5 rounded text-[11px] font-bold bg-amber-50 border border-amber-300 text-[#b12704]">
                            Pending Approval
                          </span>
                        )}
                        {req.status === "APPROVED_FOR_DISPATCH" && (
                          <span className="inline-block px-2 py-0.5 rounded text-[11px] font-bold bg-emerald-50 border border-emerald-300 text-[#067d62]">
                            Approved / Ready
                          </span>
                        )}
                        {req.status === "IN_TRANSIT" && (
                          <span className="inline-block px-2 py-0.5 rounded text-[11px] font-bold bg-sky-50 border border-sky-300 text-[#007185]">
                            In-Transit
                          </span>
                        )}
                        {req.status === "DELIVERED" && (
                          <span className="inline-block px-2 py-0.5 rounded text-[11px] font-bold bg-slate-100 border border-slate-300 text-[#067d62]">
                            Delivered
                          </span>
                        )}
                        {req.status === "REJECTED" && (
                          <span className="inline-block px-2 py-0.5 rounded text-[11px] font-bold bg-red-50 border border-red-300 text-[#c40000]">
                            Rejected
                          </span>
                        )}
                      </td>

                      <td className="py-2.5 px-3 align-top text-right space-y-1">
                        {req.status === "PENDING_APPROVAL" && (
                          <div className="flex items-center justify-end gap-1.5">
                            <button
                              onClick={() => setApprovingReq(req)}
                              className="btn-amazon-primary px-2.5 py-1 rounded text-xs font-bold inline-flex items-center gap-1 cursor-pointer"
                            >
                              Approve
                            </button>
                            <button
                              onClick={() => setRejectingReq(req)}
                              className="btn-amazon-white px-2 py-1 rounded text-xs font-semibold text-[#c40000] cursor-pointer"
                            >
                              Reject
                            </button>
                          </div>
                        )}

                        {req.status === "APPROVED_FOR_DISPATCH" && (
                          <div className="flex items-center justify-end gap-1.5">
                            <button
                              onClick={() => {
                                setActiveGatePass(req.gate_pass || null);
                                setGatePassVerification(null);
                              }}
                              className="btn-amazon-white px-2.5 py-1 rounded text-xs font-semibold inline-flex items-center gap-1 cursor-pointer"
                            >
                              <FileText className="w-3 h-3 text-[#007185]" />
                              Gate Pass
                            </button>
                            <button
                              onClick={() => handleDispatch(req.requisition_id)}
                              disabled={actionLoading === req.requisition_id}
                              className="btn-amazon-primary px-2 py-1 rounded text-xs font-bold inline-flex items-center gap-1 cursor-pointer"
                              title="Refinery Gate Checkpoint Exit Scan"
                            >
                              <Truck className="w-3 h-3" />
                              Exit Gate
                            </button>
                          </div>
                        )}

                        {req.status === "IN_TRANSIT" && (
                          <div className="flex items-center justify-end gap-1.5">
                            <button
                              onClick={() => {
                                setActiveGatePass(req.gate_pass || null);
                                setGatePassVerification(null);
                              }}
                              className="btn-amazon-white px-2.5 py-1 rounded text-xs font-semibold inline-flex items-center gap-1 cursor-pointer"
                            >
                              <FileText className="w-3 h-3 text-[#007185]" />
                              Gate Pass
                            </button>
                            <button
                              onClick={() => handleDeliver(req.requisition_id)}
                              disabled={actionLoading === req.requisition_id}
                              className="bg-emerald-600 hover:bg-emerald-700 text-white px-2 py-1 rounded text-xs font-bold inline-flex items-center gap-1 cursor-pointer"
                              title="Confirm Inbound Receipt at Destination Depot"
                            >
                              <CheckCircle2 className="w-3 h-3" />
                              Receive
                            </button>
                          </div>
                        )}

                        {req.status === "DELIVERED" && req.gate_pass && (
                          <button
                            onClick={() => {
                              setActiveGatePass(req.gate_pass || null);
                              setGatePassVerification(null);
                            }}
                            className="btn-amazon-white px-2.5 py-1 rounded text-xs font-semibold inline-flex items-center gap-1 cursor-pointer"
                          >
                            <FileText className="w-3 h-3 text-[#007185]" />
                            Gate Pass
                          </button>
                        )}

                        {req.status === "REJECTED" && (
                          <div className="text-[11px] text-[#565959] italic max-w-xs">
                            {req.rejection_reason || "Indent rejected by materials officer."}
                          </div>
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* MODAL 1: Approval Dialog */}
      {approvingReq && (
        <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-xs flex items-center justify-center p-4 overflow-y-auto">
          <div className="bg-white border border-[#d5d9d9] rounded max-w-lg w-full p-5 space-y-3.5 shadow-xl relative text-[#0f1111]">
            <button
              onClick={() => setApprovingReq(null)}
              className="absolute top-4 right-4 text-slate-400 hover:text-[#0f1111] p-1"
            >
              <X className="w-4 h-4" />
            </button>

            <div>
              <h3 className="text-sm font-bold text-[#0f1111]">
                Approve Inter-Depot Material Transfer
              </h3>
              <p className="text-xs text-[#565959] mt-0.5">
                Indent: <strong className="font-mono text-[#0f1111]">{approvingReq.requisition_id}</strong> •
                Item: {approvingReq.item_description} ({approvingReq.required_qty} Units)
              </p>
            </div>

            <div className="bg-[#f8f9fa] border border-[#d5d9d9] p-2.5 rounded text-xs space-y-1">
              <div className="flex justify-between">
                <span className="text-[#565959]">Donor Depot:</span>
                <strong>{approvingReq.target_cpse} ({approvingReq.target_depot})</strong>
              </div>
              <div className="flex justify-between">
                <span className="text-[#565959]">Recipient Depot:</span>
                <strong>{approvingReq.source_cpse} ({approvingReq.source_depot})</strong>
              </div>
              <div className="flex justify-between">
                <span className="text-[#565959]">Total Value:</span>
                <strong className="text-[#067d62]">₹{approvingReq.total_value_inr.toLocaleString("en-IN")}</strong>
              </div>
            </div>

            <form onSubmit={handleApproveSubmit} className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-[#0f1111] mb-1">
                  Approving Officer
                </label>
                <input
                  type="text"
                  required
                  value={approvalForm.approver_name}
                  onChange={(e) => setApprovalForm({ ...approvalForm, approver_name: e.target.value })}
                  className="amazon-input w-full p-1.5 text-xs"
                />
              </div>

              <div className="grid grid-cols-2 gap-2.5">
                <div>
                  <label className="block text-xs font-semibold text-[#0f1111] mb-1">
                    Vehicle Reg. No
                  </label>
                  <input
                    type="text"
                    required
                    value={approvalForm.vehicle_no}
                    onChange={(e) => setApprovalForm({ ...approvalForm, vehicle_no: e.target.value })}
                    className="amazon-input w-full p-1.5 text-xs font-mono"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-[#0f1111] mb-1">
                    Driver Full Name
                  </label>
                  <input
                    type="text"
                    required
                    value={approvalForm.driver_name}
                    onChange={(e) => setApprovalForm({ ...approvalForm, driver_name: e.target.value })}
                    className="amazon-input w-full p-1.5 text-xs"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-[#0f1111] mb-1">
                  Driver License / ID No
                </label>
                <input
                  type="text"
                  required
                  value={approvalForm.driver_id_no}
                  onChange={(e) => setApprovalForm({ ...approvalForm, driver_id_no: e.target.value })}
                  className="amazon-input w-full p-1.5 text-xs font-mono"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2 border-t border-[#eaeded]">
                <button
                  type="button"
                  onClick={() => setApprovingReq(null)}
                  className="btn-amazon-white px-3 py-1.5 rounded text-xs font-semibold cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submittingApproval}
                  className="btn-amazon-primary px-3.5 py-1.5 rounded text-xs font-bold cursor-pointer disabled:opacity-50"
                >
                  {submittingApproval ? "Generating Pass..." : "Approve & Generate Gate Pass"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL 1B: Rejection Dialog */}
      {rejectingReq && (
        <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-xs flex items-center justify-center p-4 overflow-y-auto">
          <div className="bg-white border border-[#d5d9d9] rounded max-w-md w-full p-5 space-y-3.5 shadow-xl relative text-[#0f1111]">
            <button
              onClick={() => setRejectingReq(null)}
              className="absolute top-4 right-4 text-slate-400 hover:text-[#0f1111] p-1"
            >
              <X className="w-4 h-4" />
            </button>

            <div>
              <h3 className="text-sm font-bold text-[#c40000]">
                Reject Transfer Indent & Release Inventory Lock
              </h3>
              <p className="text-xs text-[#565959] mt-0.5">
                Requisition <strong className="font-mono">{rejectingReq.requisition_id}</strong> will be cancelled and reserved stock ({rejectingReq.required_qty} units) returned to donor CPSE inventory.
              </p>
            </div>

            <form onSubmit={handleRejectSubmit} className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-[#0f1111] mb-1">
                  Reason for Rejection
                </label>
                <textarea
                  rows={3}
                  required
                  value={rejectReason}
                  onChange={(e) => setRejectReason(e.target.value)}
                  className="amazon-input w-full p-1.5 text-xs"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2 border-t border-[#eaeded]">
                <button
                  type="button"
                  onClick={() => setRejectingReq(null)}
                  className="btn-amazon-white px-3 py-1.5 rounded text-xs font-semibold cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={actionLoading === rejectingReq.requisition_id}
                  className="bg-[#c40000] hover:bg-[#a10000] text-white px-3.5 py-1.5 rounded text-xs font-bold cursor-pointer disabled:opacity-50"
                >
                  Confirm Rejection
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL 2: Printable Gate Pass with Scannable QR Code */}
      {activeGatePass && (
        <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-xs flex items-center justify-center p-4 overflow-y-auto">
          <div className="bg-white border border-[#d5d9d9] rounded max-w-2xl w-full p-6 shadow-xl relative space-y-4 text-[#0f1111]">
            {/* Toolbar */}
            <div className="flex items-center justify-between border-b border-[#eaeded] pb-2.5 no-print">
              <span className="text-xs font-bold text-[#0f1111]">
                CISF Digital Material Gate Pass
              </span>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => handleVerifyGatePass(activeGatePass.gate_pass_no)}
                  disabled={verifyingPass}
                  className="btn-amazon-white px-2.5 py-1 rounded text-xs font-semibold flex items-center gap-1 cursor-pointer"
                  title="Simulate Perimeter Security Gate Scanner"
                >
                  <ShieldCheck className="w-3.5 h-3.5 text-[#067d62]" />
                  {verifyingPass ? "Scanning..." : "Verify Gate Security"}
                </button>
                <button
                  onClick={() => window.print()}
                  className="btn-amazon-primary px-3 py-1 rounded text-xs font-bold flex items-center gap-1 cursor-pointer"
                >
                  <Printer className="w-3.5 h-3.5" />
                  Print Pass
                </button>
                <button
                  onClick={() => setActiveGatePass(null)}
                  className="text-slate-400 hover:text-[#0f1111] p-1 rounded cursor-pointer"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* Verification Status Banner */}
            {gatePassVerification && (
              <div className="p-2.5 bg-emerald-50 border border-emerald-300 rounded text-xs text-[#067d62] space-y-0.5 no-print">
                <div className="flex items-center gap-1.5 font-bold">
                  <CheckCircle2 className="w-4 h-4 text-[#067d62]" />
                  <span>CISF Security Clearance: AUTHENTICATED</span>
                </div>
                <div className="text-[11px] text-[#565959]">
                  {gatePassVerification.verification_message}
                </div>
              </div>
            )}

            {/* Document Canvas */}
            <div className="border border-[#0f1111] p-5 rounded bg-white space-y-4 printable-card text-xs">
              <div className="flex items-start justify-between border-b border-[#0f1111] pb-3">
                <div className="space-y-0.5">
                  <div className="font-bold text-sm text-[#0f1111] uppercase tracking-wide">
                    Outward Material Movement Gate Pass
                  </div>
                  <div className="text-[11px] text-[#565959]">
                    Central Industrial Security Force (CISF) • Ministry of Petroleum & Natural Gas
                  </div>
                  <div className="text-[10px] text-[#565959] font-mono">
                    Token: {activeGatePass.cisf_verification_seal}
                  </div>
                </div>

                {/* Scannable QR Code */}
                <div className="flex flex-col items-center">
                  {activeGatePass.qr_code_svg ? (
                    <div
                      className="w-20 h-20 border border-[#d5d9d9] p-1 rounded bg-white"
                      dangerouslySetInnerHTML={{ __html: activeGatePass.qr_code_svg }}
                    />
                  ) : (
                    <div className="w-20 h-20 border border-[#d5d9d9] flex items-center justify-center text-[9px] font-mono text-[#565959]">
                      QR_CODE
                    </div>
                  )}
                  <span className="text-[9px] text-[#565959] mt-0.5 font-mono">Scan for CISF Audit</span>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3 text-xs">
                <div className="bg-[#f8f9fa] p-2.5 rounded border border-[#d5d9d9]">
                  <div className="text-[#565959] text-[10px] uppercase font-bold">Pass Number</div>
                  <div className="font-mono font-bold text-xs">{activeGatePass.gate_pass_no}</div>
                  <div className="text-[#565959] text-[10px] mt-0.5">Indent: {activeGatePass.requisition_id}</div>
                </div>

                <div className="bg-[#f8f9fa] p-2.5 rounded border border-[#d5d9d9]">
                  <div className="text-[#565959] text-[10px] uppercase font-bold">GST E-Way Bill</div>
                  <div className="font-mono font-bold text-xs">{activeGatePass.gst_eway_bill_no}</div>
                  <div className="text-[#565959] text-[10px] mt-0.5">
                    Issued: {new Date(activeGatePass.issue_timestamp).toLocaleDateString("en-IN")}
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3 text-xs">
                <div className="p-2.5 border border-[#d5d9d9] rounded">
                  <div className="text-[10px] font-bold text-[#565959] uppercase">Issuing Depot (Donor)</div>
                  <div className="font-bold">{activeGatePass.issuing_cpse}</div>
                  <div className="text-[#565959] text-[11px]">{activeGatePass.issuing_depot}</div>
                </div>
                <div className="p-2.5 border border-[#d5d9d9] rounded">
                  <div className="text-[10px] font-bold text-[#565959] uppercase">Receiving Depot</div>
                  <div className="font-bold">{activeGatePass.receiving_cpse}</div>
                  <div className="text-[#565959] text-[11px]">{activeGatePass.receiving_depot}</div>
                </div>
              </div>

              {/* Transit & Fleet Info */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 bg-[#f8f9fa] p-2.5 rounded border border-[#d5d9d9] text-[11px]">
                <div>
                  <span className="text-[#565959] block">Vehicle No:</span>
                  <strong className="font-mono">{activeGatePass.vehicle_no}</strong>
                </div>
                <div>
                  <span className="text-[#565959] block">Driver:</span>
                  <strong>{activeGatePass.driver_name}</strong>
                </div>
                <div>
                  <span className="text-[#565959] block">Transit Distance:</span>
                  <strong>{activeGatePass.transit_distance_km} km</strong>
                </div>
                <div>
                  <span className="text-[#565959] block">Est. Transit Duration:</span>
                  <strong>{activeGatePass.estimated_transit_hours} Hours</strong>
                </div>
              </div>

              <div className="pt-2 border-t border-[#d5d9d9] space-y-1 text-[10px] text-[#565959]">
                <div className="flex items-center justify-between">
                  <span className="font-mono truncate max-w-md">
                    SHA-256 Audit Seal: {activeGatePass.sha256_hash}
                  </span>
                  <button
                    onClick={() => handleCopyHash(activeGatePass.sha256_hash)}
                    className="btn-amazon-white px-1.5 py-0.5 rounded cursor-pointer no-print shrink-0"
                    title="Copy Hash"
                  >
                    {copiedHash ? <Check className="w-3 h-3 text-[#067d62] inline" /> : <Copy className="w-3 h-3 inline" />}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* MODAL 3: New Transfer Indent with Live GIS Route Preview */}
      {isNewIndentModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-xs flex items-center justify-center p-4 overflow-y-auto">
          <div className="bg-white border border-[#d5d9d9] rounded max-w-xl w-full p-5 space-y-3.5 shadow-xl relative text-[#0f1111]">
            <button
              onClick={() => setIsNewIndentModalOpen(false)}
              className="absolute top-4 right-4 text-slate-400 hover:text-[#0f1111] p-1 cursor-pointer"
            >
              <X className="w-4 h-4" />
            </button>

            <div>
              <h3 className="text-sm font-bold text-[#0f1111]">
                Create Inter-Depot Material Transfer Indent
              </h3>
              <p className="text-xs text-[#565959] mt-0.5">
                Requisition surplus inventory across CPSE refineries with automated reservation locks.
              </p>
            </div>

            {/* Quick Fill Buttons */}
            <div className="space-y-1">
              <span className="text-[11px] text-[#565959] font-semibold block">
                Quick Fill Preset:
              </span>
              <div className="flex flex-wrap gap-1 text-xs">
                <button
                  type="button"
                  onClick={() => loadPreset("motor")}
                  className="bg-[#f8f9fa] hover:bg-slate-100 border border-[#d5d9d9] px-2 py-0.5 rounded text-[11px] text-[#0f1111] cursor-pointer"
                >
                  Motor 37kW (Uran)
                </button>
                <button
                  type="button"
                  onClick={() => loadPreset("flange")}
                  className="bg-[#f8f9fa] hover:bg-slate-100 border border-[#d5d9d9] px-2 py-0.5 rounded text-[11px] text-[#0f1111] cursor-pointer"
                >
                  WN Flange 4" 300# (Hazira)
                </button>
                <button
                  type="button"
                  onClick={() => loadPreset("seal")}
                  className="bg-[#f8f9fa] hover:bg-slate-100 border border-[#d5d9d9] px-2 py-0.5 rounded text-[11px] text-[#0f1111] cursor-pointer"
                >
                  Mech Seal Plan 53A (Mumbai)
                </button>
                <button
                  type="button"
                  onClick={() => loadPreset("bearing")}
                  className="bg-[#f8f9fa] hover:bg-slate-100 border border-[#d5d9d9] px-2 py-0.5 rounded text-[11px] text-[#0f1111] cursor-pointer"
                >
                  Bearing 6310-C3 (Koyali)
                </button>
              </div>
            </div>

            <form onSubmit={handleCreateSubmit} className="space-y-3">
              <div className="grid grid-cols-3 gap-2">
                <div>
                  <label className="block text-xs font-semibold text-[#0f1111] mb-1">
                    Requesting CPSE
                  </label>
                  <select
                    value={newReqForm.source_cpse}
                    onChange={(e) => setNewReqForm({ ...newReqForm, source_cpse: e.target.value })}
                    className="amazon-input w-full p-1.5 text-xs"
                  >
                    <option value="IOCL">IOCL</option>
                    <option value="ONGC">ONGC</option>
                    <option value="BPCL">BPCL</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-[#0f1111] mb-1">
                    Depot / Refinery
                  </label>
                  <select
                    value={newReqForm.source_depot}
                    onChange={(e) => setNewReqForm({ ...newReqForm, source_depot: e.target.value })}
                    className="amazon-input w-full p-1.5 text-xs"
                  >
                    {depots.map((d) => (
                      <option key={d.depot_id} value={d.name}>
                        {d.cpse}: {d.name}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-[#0f1111] mb-1">
                    Process Unit
                  </label>
                  <input
                    type="text"
                    required
                    value={newReqForm.source_unit}
                    onChange={(e) => setNewReqForm({ ...newReqForm, source_unit: e.target.value })}
                    className="amazon-input w-full p-1.5 text-xs"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-xs font-semibold text-[#0f1111] mb-1">
                    Donor CPSE (Surplus Holding)
                  </label>
                  <select
                    value={newReqForm.target_cpse}
                    onChange={(e) => setNewReqForm({ ...newReqForm, target_cpse: e.target.value })}
                    className="amazon-input w-full p-1.5 text-xs"
                  >
                    <option value="ONGC">ONGC</option>
                    <option value="IOCL">IOCL</option>
                    <option value="BPCL">BPCL</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-[#0f1111] mb-1">
                    Donor Depot
                  </label>
                  <select
                    value={newReqForm.target_depot}
                    onChange={(e) => setNewReqForm({ ...newReqForm, target_depot: e.target.value })}
                    className="amazon-input w-full p-1.5 text-xs"
                  >
                    {depots.map((d) => (
                      <option key={d.depot_id} value={d.name}>
                        {d.cpse}: {d.name}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {/* GIS Logistics Route Preview */}
              {routePreview && (
                <div className="bg-[#f8f9fa] border border-[#d5d9d9] p-2.5 rounded text-xs space-y-1">
                  <div className="flex items-center justify-between text-[#565959] text-[11px] font-bold uppercase">
                    <span className="flex items-center gap-1">
                      <MapPin className="w-3 h-3 text-[#ff9900]" />
                      GIS Logistics Route Estimate
                    </span>
                    <span>{routePreview.primary_corridor}</span>
                  </div>
                  <div className="grid grid-cols-4 gap-2 pt-1">
                    <div>
                      <span className="text-[#565959] block text-[10px]">Road Distance:</span>
                      <strong className="text-xs">{routePreview.road_distance_km} km</strong>
                    </div>
                    <div>
                      <span className="text-[#565959] block text-[10px]">Transit Duration:</span>
                      <strong className="text-xs">{routePreview.total_transit_hours} Hours ({routePreview.estimated_transit_days} Days)</strong>
                    </div>
                    <div>
                      <span className="text-[#565959] block text-[10px]">Est. Freight Rate:</span>
                      <strong className="text-xs text-[#067d62]">₹{routePreview.freight_cost_inr.toLocaleString("en-IN")}</strong>
                    </div>
                    <div>
                      <span className="text-[#565959] block text-[10px]">CO2 Avoidance:</span>
                      <strong className="text-xs text-[#007185]">{routePreview.co2_avoided_vs_import_kg} kg</strong>
                    </div>
                  </div>
                </div>
              )}

              <div>
                <label className="block text-xs font-semibold text-[#0f1111] mb-1">
                  Material Description
                </label>
                <input
                  type="text"
                  required
                  value={newReqForm.item_description}
                  onChange={(e) => setNewReqForm({ ...newReqForm, item_description: e.target.value })}
                  className="amazon-input w-full p-1.5 text-xs"
                />
              </div>

              <div className="grid grid-cols-3 gap-2">
                <div>
                  <label className="block text-xs font-semibold text-[#0f1111] mb-1">
                    SKU Code
                  </label>
                  <input
                    type="text"
                    required
                    value={newReqForm.sku_code}
                    onChange={(e) => setNewReqForm({ ...newReqForm, sku_code: e.target.value })}
                    className="amazon-input w-full p-1.5 text-xs font-mono"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-[#0f1111] mb-1">
                    Quantity
                  </label>
                  <input
                    type="number"
                    min="1"
                    required
                    value={newReqForm.required_qty}
                    onChange={(e) => setNewReqForm({ ...newReqForm, required_qty: parseInt(e.target.value) || 1 })}
                    className="amazon-input w-full p-1.5 text-xs"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-[#0f1111] mb-1">
                    Unit Cost (₹)
                  </label>
                  <input
                    type="number"
                    min="1"
                    required
                    value={newReqForm.unit_cost_inr}
                    onChange={(e) => setNewReqForm({ ...newReqForm, unit_cost_inr: parseFloat(e.target.value) || 0 })}
                    className="amazon-input w-full p-1.5 text-xs"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-xs font-semibold text-[#0f1111] mb-1">
                    Priority Level
                  </label>
                  <select
                    value={newReqForm.urgency_level}
                    onChange={(e) => setNewReqForm({ ...newReqForm, urgency_level: e.target.value as UrgencyLevel })}
                    className="amazon-input w-full p-1.5 text-xs"
                  >
                    <option value="EMERGENCY_SHUTDOWN">Emergency Priority</option>
                    <option value="PLANNED_MAINTENANCE">Planned Maintenance</option>
                    <option value="ROUTINE">Routine Replenishment</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-[#0f1111] mb-1">
                    Total Value
                  </label>
                  <div className="w-full bg-[#f8f9fa] border border-[#d5d9d9] rounded p-1.5 text-xs font-bold text-[#067d62]">
                    ₹{(newReqForm.required_qty * newReqForm.unit_cost_inr).toLocaleString("en-IN")}
                  </div>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-[#0f1111] mb-1">
                  Justification
                </label>
                <textarea
                  rows={2}
                  required
                  value={newReqForm.justification}
                  onChange={(e) => setNewReqForm({ ...newReqForm, justification: e.target.value })}
                  className="amazon-input w-full p-1.5 text-xs"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2 border-t border-[#eaeded]">
                <button
                  type="button"
                  onClick={() => setIsNewIndentModalOpen(false)}
                  className="btn-amazon-white px-3 py-1.5 rounded text-xs font-semibold cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submittingNewReq}
                  className="btn-amazon-primary px-3.5 py-1.5 rounded text-xs font-bold cursor-pointer disabled:opacity-50"
                >
                  {submittingNewReq ? "Submitting..." : "Submit Indent & Lock Stock"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default function TransfersPage() {
  return (
    <Suspense fallback={<div className="p-8 text-center text-xs text-slate-500">Loading Transfers...</div>}>
      <TransfersContent />
    </Suspense>
  );
}
