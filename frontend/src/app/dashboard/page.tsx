"use client";

import { useEffect, useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { fetchSpares } from "@/lib/api";
import { InterCPSESpare } from "@/lib/types";
import {
  Search,
  Truck,
  Building2,
  Package,
  Layers,
  ArrowRight,
  Filter,
  Download,
} from "lucide-react";
import { exportToCsv } from "@/lib/exportUtils";


function DashboardContent() {
  const searchParams = useSearchParams();
  const urlQuery = searchParams.get("q") || "";
  const urlCpse = searchParams.get("cpse") || "ALL";

  const [spares, setSpares] = useState<InterCPSESpare[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchFilter, setSearchFilter] = useState(urlQuery);
  const [selectedCpse, setSelectedCpse] = useState(urlCpse);
  const [selectedCategory, setSelectedCategory] = useState("ALL");

  useEffect(() => {
    loadSpares();
  }, []);

  useEffect(() => {
    if (urlQuery) setSearchFilter(urlQuery);
    if (urlCpse) setSelectedCpse(urlCpse);
  }, [urlQuery, urlCpse]);

  const loadSpares = async () => {
    setLoading(true);
    const data = await fetchSpares("ALL", "ALL");
    setSpares(data);
    setLoading(false);
  };

  const filteredSpares = spares.filter((item) => {
    if (selectedCpse !== "ALL" && item.owner_cpse !== selectedCpse) return false;

    if (selectedCategory !== "ALL") {
      const desc = item.description.toUpperCase();
      if (selectedCategory === "FLANGE" && !desc.includes("FLANGE") && !desc.includes("FLG")) return false;
      if (selectedCategory === "VALVE" && !desc.includes("VALVE") && !desc.includes("VLV")) return false;
      if (selectedCategory === "MOTOR" && !desc.includes("MOTOR") && !desc.includes("MTR")) return false;
      if (selectedCategory === "SEAL" && !desc.includes("SEAL")) return false;
      if (selectedCategory === "BEARING" && !desc.includes("BEARING") && !desc.includes("BRG")) return false;
      if (selectedCategory === "FITTING" && !desc.includes("ELBOW") && !desc.includes("FERRULE")) return false;
    }

    if (searchFilter.trim()) {
      const q = searchFilter.toLowerCase();
      const matchesSku = item.equivalent_sku.toLowerCase().includes(q);
      const matchesDesc = item.description.toLowerCase().includes(q);
      const matchesDepot = item.depot_location.toLowerCase().includes(q);
      const matchesCanon = item.canonical_description.toLowerCase().includes(q);
      if (!matchesSku && !matchesDesc && !matchesDepot && !matchesCanon) return false;
    }

    return true;
  });

  const handleExportInventoryCsv = () => {
    exportToCsv(filteredSpares, "Samanvay_Surplus_Inventory", {
      equivalent_sku: "SKU Code",
      owner_cpse: "Owner CPSE",
      description: "Material Description",
      depot_location: "Depot Location",
      available_qty: "Available Quantity",
      days_idle: "Days Idle",
      unit_cost: "Unit Cost (INR)",
      total_value_inr: "Total Value (INR)",
      canonical_id: "Canonical ID",
      canonical_description: "Canonical Master Description",
    });
  };

  return (
    <div className="space-y-4">
      {/* 1. Header & Quick Actions */}
      <div className="bg-white border border-[#d5d9d9] rounded p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-sm">
        <div>
          <h1 className="text-lg font-bold text-[#0f1111]">
            Cross-CPSE Inventory & Spare Parts Search
          </h1>
          <p className="text-xs text-[#565959] mt-0.5">
            Search available material stock across IOCL, ONGC, and BPCL refinery and plant depots.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleExportInventoryCsv}
            className="btn-amazon-white px-3 py-1.5 rounded text-xs font-semibold flex items-center gap-1.5 cursor-pointer"
            title="Export filtered items to CSV/Excel"
          >
            <Download className="w-3.5 h-3.5 text-[#565959]" />
            Export CSV
          </button>
          <Link
            href="/deduplication"
            className="btn-amazon-white px-3 py-1.5 rounded text-xs font-semibold flex items-center gap-1.5"
          >
            <Layers className="w-3.5 h-3.5 text-[#565959]" />
            Standardize Material
          </Link>
          <Link
            href="/transfers"
            className="btn-amazon-primary px-3 py-1.5 rounded text-xs font-bold flex items-center gap-1.5"
          >
            <Truck className="w-3.5 h-3.5" />
            Transfer Indents
          </Link>
        </div>
      </div>


      {/* 2. Filter & Search Controls */}
      <div className="bg-white border border-[#d5d9d9] rounded p-3.5 flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 shadow-sm">
        <div className="flex-1 flex flex-col sm:flex-row items-stretch sm:items-center gap-2.5">
          {/* Search Input */}
          <div className="relative flex-1">
            <input
              type="text"
              placeholder="Search by description, SKU, standard, or location..."
              value={searchFilter}
              onChange={(e) => setSearchFilter(e.target.value)}
              className="amazon-input w-full pl-8 pr-3 py-1.5 text-xs"
            />
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-2" />
          </div>

          {/* CPSE Filter */}
          <select
            value={selectedCpse}
            onChange={(e) => setSelectedCpse(e.target.value)}
            className="amazon-input text-xs font-semibold px-2.5 py-1.5 bg-white cursor-pointer"
          >
            <option value="ALL">All CPSEs</option>
            <option value="IOCL">IOCL</option>
            <option value="ONGC">ONGC</option>
            <option value="BPCL">BPCL</option>
          </select>

          {/* Category Filter */}
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="amazon-input text-xs font-semibold px-2.5 py-1.5 bg-white cursor-pointer"
          >
            <option value="ALL">All Equipment Categories</option>
            <option value="FLANGE">Flanges</option>
            <option value="VALVE">Valves</option>
            <option value="MOTOR">Electric Motors</option>
            <option value="SEAL">Mechanical Seals</option>
            <option value="BEARING">Bearings</option>
            <option value="FITTING">Fittings & Elbows</option>
          </select>
        </div>

        <div className="text-xs text-[#565959] shrink-0 self-center">
          Showing <strong>{filteredSpares.length}</strong> items
        </div>
      </div>

      {/* 3. High-Density Inventory Table */}
      <div className="bg-white border border-[#d5d9d9] rounded overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead className="bg-[#f2f3f3] text-[#565959] font-bold uppercase tracking-wider border-b border-[#d5d9d9]">
              <tr>
                <th className="py-2.5 px-3">Local SKU</th>
                <th className="py-2.5 px-3">Description</th>
                <th className="py-2.5 px-3">CPSE</th>
                <th className="py-2.5 px-3">Depot Location</th>
                <th className="py-2.5 px-3 text-center">Available Qty</th>
                <th className="py-2.5 px-3 text-right">Unit Price</th>
                <th className="py-2.5 px-3 text-right">Total Value</th>
                <th className="py-2.5 px-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#e5e7eb] text-[#0f1111]">
              {loading ? (
                <tr>
                  <td colSpan={8} className="py-10 text-center text-[#565959]">
                    Loading catalog inventory...
                  </td>
                </tr>
              ) : filteredSpares.length === 0 ? (
                <tr>
                  <td colSpan={8} className="py-10 text-center text-[#565959]">
                    No material matching the search criteria was found.
                  </td>
                </tr>
              ) : (
                filteredSpares.map((item, idx) => (
                  <tr key={idx} className="hover:bg-[#f7fafa] transition-colors">
                    <td className="py-2.5 px-3 font-mono font-bold text-[#007185]">
                      {item.equivalent_sku}
                    </td>
                    <td className="py-2.5 px-3 max-w-md">
                      <div className="font-semibold text-[#0f1111]">{item.description}</div>
                      {item.canonical_description && item.canonical_description !== item.description && (
                        <div className="text-[11px] text-[#565959] mt-0.5 truncate" title={item.canonical_description}>
                          Canonical: {item.canonical_description}
                        </div>
                      )}
                    </td>
                    <td className="py-2.5 px-3 font-bold">
                      <span
                        className={`inline-block px-2 py-0.2 rounded text-[11px] font-bold ${
                          item.owner_cpse === "ONGC"
                            ? "bg-amber-100 text-amber-900 border border-amber-300"
                            : item.owner_cpse === "BPCL"
                            ? "bg-blue-100 text-blue-900 border border-blue-300"
                            : "bg-orange-100 text-orange-900 border border-orange-300"
                        }`}
                      >
                        {item.owner_cpse}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-[#565959] text-xs">
                      {item.depot_location}
                    </td>
                    <td className="py-2.5 px-3 text-center font-bold text-[#0f1111]">
                      {item.available_qty}
                    </td>
                    <td className="py-2.5 px-3 text-right font-mono text-[#565959]">
                      ₹{item.unit_cost.toLocaleString("en-IN")}
                    </td>
                    <td className="py-2.5 px-3 text-right font-mono font-bold text-[#0f1111]">
                      ₹{item.total_value_inr.toLocaleString("en-IN")}
                    </td>
                    <td className="py-2.5 px-3 text-right">
                      <Link
                        href={`/transfers?sku=${encodeURIComponent(item.equivalent_sku)}&target_cpse=${encodeURIComponent(item.owner_cpse)}&target_depot=${encodeURIComponent(item.depot_location)}&desc=${encodeURIComponent(item.description)}&qty=${item.available_qty}&cost=${item.unit_cost}`}
                        className="btn-amazon-primary inline-flex items-center gap-1 px-2.5 py-1 rounded text-xs font-bold"
                      >
                        <Truck className="w-3 h-3 text-[#0f1111]" />
                        <span>Request Transfer</span>
                      </Link>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

export default function DashboardPage() {
  return (
    <Suspense fallback={<div className="p-8 text-center text-xs text-slate-500">Loading Inventory...</div>}>
      <DashboardContent />
    </Suspense>
  );
}
