"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  Search,
  MapPin,
  CheckCircle2,
  Package,
  Layers,
  Truck,
  ChevronDown,
  Building2,
  FileText,
} from "lucide-react";

export default function TopNav() {
  const pathname = usePathname();
  const router = useRouter();

  const [selectedCpse, setSelectedCpse] = useState("ALL");
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedDepot, setSelectedDepot] = useState("IOCL - Panipat Refinery");
  const [depotDropdownOpen, setDepotDropdownOpen] = useState(false);

  const depots = [
    { label: "IOCL - Panipat Refinery", cpse: "IOCL" },
    { label: "ONGC - Hazira Processing Plant", cpse: "ONGC" },
    { label: "BPCL - Mumbai Refinery, Mahul", cpse: "BPCL" },
    { label: "IOCL - Mathura Refinery", cpse: "IOCL" },
    { label: "ONGC - Uran Plant, Raigad", cpse: "ONGC" },
  ];

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;
    router.push(`/dashboard?q=${encodeURIComponent(searchQuery.trim())}&cpse=${encodeURIComponent(selectedCpse)}`);
  };

  const navLinks = [
    {
      name: "Inventory & Spare Parts Search",
      href: "/dashboard",
      icon: Package,
    },
    {
      name: "Material Standardization & Ingestion",
      href: "/deduplication",
      icon: Layers,
    },
    {
      name: "Verification Queue",
      href: "/hitl",
      icon: CheckCircle2,
      badge: "3",
    },
    {
      name: "Inter-Depot Transfers",
      href: "/transfers",
      icon: Truck,
    },
    {
      name: "Audit Ledger",
      href: "/audits",
      icon: FileText,
    },
  ];


  return (
    <header className="sticky top-0 z-40 w-full shadow-sm bg-white no-print">
      {/* 1. Top Bar */}
      <div className="bg-[#131921] text-white px-4 py-2.5 flex items-center justify-between gap-4">
        {/* Brand & Location */}
        <div className="flex items-center gap-5 shrink-0">
          <Link href="/dashboard" className="flex items-center gap-2 group">
            <span className="text-base font-bold tracking-tight text-white group-hover:text-[#febd69] transition-colors">
              Samanvay <span className="text-xs font-normal text-slate-300">| Material Harmonization</span>
            </span>
          </Link>

          {/* Depot Location Selector */}
          <div className="relative hidden lg:block">
            <button
              onClick={() => setDepotDropdownOpen(!depotDropdownOpen)}
              className="flex items-center gap-1.5 px-2 py-1 rounded hover:bg-[#232f3e] text-left transition-all cursor-pointer text-xs"
            >
              <MapPin className="w-3.5 h-3.5 text-slate-400" />
              <div>
                <span className="text-[10px] text-slate-400 block leading-tight">Location</span>
                <span className="font-semibold text-white flex items-center gap-1">
                  {selectedDepot.split(" - ")[0]}
                  <ChevronDown className="w-3 h-3 text-slate-400" />
                </span>
              </div>
            </button>

            {depotDropdownOpen && (
              <div className="absolute left-0 mt-1.5 w-64 bg-white rounded shadow-lg border border-[#d5d9d9] text-[#0f1111] z-50 p-1.5 text-xs">
                <div className="font-semibold text-slate-600 px-2 py-1 border-b border-slate-100 flex items-center gap-1.5">
                  <Building2 className="w-3.5 h-3.5 text-[#007185]" />
                  Select Operating Depot
                </div>
                <div className="mt-1 space-y-0.5">
                  {depots.map((d) => (
                    <button
                      key={d.label}
                      onClick={() => {
                        setSelectedDepot(d.label);
                        setDepotDropdownOpen(false);
                      }}
                      className={`w-full text-left px-2 py-1.5 rounded hover:bg-slate-100 flex items-center justify-between transition-colors ${
                        selectedDepot === d.label ? "bg-amber-50 font-bold text-[#b12704]" : ""
                      }`}
                    >
                      <span className="truncate">{d.label}</span>
                      <span className="text-[10px] font-mono px-1 bg-slate-200 text-slate-700 rounded">
                        {d.cpse}
                      </span>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Search Bar */}
        <form
          onSubmit={handleSearchSubmit}
          className="flex-1 max-w-2xl flex items-center rounded overflow-hidden bg-white focus-within:ring-2 focus-within:ring-[#ff9900]"
        >
          <select
            value={selectedCpse}
            onChange={(e) => setSelectedCpse(e.target.value)}
            aria-label="Filter search by CPSE"
            className="bg-[#eaeded] hover:bg-[#d5d9d9] text-[#0f1111] text-xs font-semibold px-3 py-2 border-r border-[#cdcdcd] focus:outline-none cursor-pointer"
          >
            <option value="ALL">All CPSEs</option>
            <option value="IOCL">IOCL</option>
            <option value="ONGC">ONGC</option>
            <option value="BPCL">BPCL</option>
          </select>

          <input
            type="text"
            placeholder="Search material description, SKU, or standard (e.g. Flange 4IN 300#, Gate Valve, Motor)..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="flex-1 px-3 py-1.5 text-xs text-[#0f1111] placeholder-slate-400 focus:outline-none"
          />

          <button
            type="submit"
            aria-label="Search catalog"
            className="bg-[#febd69] hover:bg-[#f3a847] text-[#131921] px-4 py-2 flex items-center justify-center transition-colors cursor-pointer"
          >
            <Search className="w-4 h-4" />
          </button>
        </form>

        {/* User Info */}
        <div className="text-right text-xs shrink-0">
          <div className="text-[10px] text-slate-400">Logged in as</div>
          <div className="font-semibold text-white">Mayank Anand (IOCL)</div>
        </div>
      </div>

      {/* 2. Sub-Navigation Bar */}
      <div className="bg-[#232f3e] text-slate-200 text-xs font-medium px-4 py-1 flex items-center justify-start gap-2 border-t border-[#37475a] overflow-x-auto">
        {navLinks.map((item) => {
          const isActive = pathname === item.href;
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded transition-all whitespace-nowrap ${
                isActive
                  ? "bg-[#131921] text-[#ff9900] font-bold"
                  : "hover:text-white hover:bg-[#37475a] text-slate-300"
              }`}
            >
              <Icon className={`w-3.5 h-3.5 ${isActive ? "text-[#ff9900]" : "text-slate-400"}`} />
              <span>{item.name}</span>
              {item.badge && (
                <span className="ml-1 text-[10px] px-1.5 py-0.2 rounded-full font-bold bg-[#ff9900] text-black">
                  {item.badge}
                </span>
              )}
            </Link>
          );
        })}
      </div>
    </header>
  );
}
