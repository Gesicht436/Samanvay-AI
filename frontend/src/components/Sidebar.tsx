"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useTheme, CPSE_OPTIONS } from "./ThemeProvider";
import { ThemeToggle } from "./ThemeToggle";
import {
  UploadCloud,
  Package,
  Search,
  Truck,
  ShieldCheck,
  Building2,
  Menu,
  X,
  Layers,
} from "lucide-react";

export function Sidebar() {
  const pathname = usePathname();
  const { activeCpse, setActiveCpse, activeDepot } = useTheme();
  const [isMobileOpen, setIsMobileOpen] = useState(false);

  const navItems = [
    {
      href: "/upload",
      label: "Upload & OCR",
      description: "Bill & MTC ingestion",
      icon: <UploadCloud className="w-4 h-4" />,
    },
    {
      href: "/inventory",
      label: "Plant Inventory",
      description: "Lifecycle & surplus tags",
      icon: <Package className="w-4 h-4" />,
    },
    {
      href: "/discover",
      label: "Spare Discovery",
      description: "Cross-CPSE search & indent",
      icon: <Search className="w-4 h-4" />,
    },
    {
      href: "/requests",
      label: "Requests & Tracking",
      description: "Supply confirm & transit",
      icon: <Truck className="w-4 h-4" />,
    },
    {
      href: "/audit",
      label: "Sovereign Audit",
      description: "CVC / CAG ledger",
      icon: <ShieldCheck className="w-4 h-4" />,
    },
  ];

  const currentCpseOption = CPSE_OPTIONS.find((c) => c.id === activeCpse) || CPSE_OPTIONS[0];

  return (
    <>
      {/* Mobile Top Bar */}
      <div className="lg:hidden flex items-center justify-between p-3 bg-[var(--bg-secondary)] border-b border-[var(--border-primary)] sticky top-0 z-40">
        <div className="flex items-center gap-2">
          <button
            onClick={() => setIsMobileOpen(!isMobileOpen)}
            className="p-1.5 rounded-md text-[var(--text-secondary)] hover:bg-[var(--bg-tertiary)] cursor-pointer"
          >
            {isMobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
          <div className="flex items-center gap-1.5 font-bold text-sm text-[var(--text-primary)]">
            <span className="w-2 h-2 rounded-full bg-[var(--accent-primary)]"></span>
            Samanvay-AI
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[11px] font-semibold px-2 py-0.5 rounded bg-[var(--bg-tertiary)] text-[var(--accent-primary)]">
            {activeCpse}
          </span>
          <ThemeToggle />
        </div>
      </div>

      {/* Mobile Overlay */}
      {isMobileOpen && (
        <div
          className="lg:hidden fixed inset-0 z-40 bg-black/40 backdrop-blur-xs"
          onClick={() => setIsMobileOpen(false)}
        />
      )}

      {/* Sidebar Desktop & Mobile Drawer */}
      <aside
        className={`fixed lg:sticky top-0 left-0 z-50 lg:z-30 h-screen w-64 bg-[var(--bg-secondary)] border-r border-[var(--border-primary)] flex flex-col justify-between transition-transform duration-200 ease-in-out shrink-0 ${
          isMobileOpen ? "translate-x-0 shadow-2xl" : "-translate-x-full lg:translate-x-0"
        }`}
      >
        {/* Header */}
        <div className="p-4 border-b border-[var(--border-subtle)]">
          <Link
            href="/upload"
            className="flex items-center gap-2 text-[var(--text-primary)] hover:opacity-90 transition-opacity"
            onClick={() => setIsMobileOpen(false)}
          >
            <div className="w-7 h-7 rounded-lg bg-[var(--accent-primary)] flex items-center justify-center text-white shadow-xs">
              <Layers className="w-4 h-4" />
            </div>
            <div>
              <div className="font-bold text-sm tracking-tight leading-none">
                Samanvay<span className="text-[var(--accent-primary)]">-AI</span>
              </div>
              <div className="text-[10px] text-[var(--text-muted)] mt-0.5 leading-none">
                MoPNG Sovereign Portal
              </div>
            </div>
          </Link>
        </div>

        {/* Navigation Links */}
        <div className="p-3 flex-1 overflow-y-auto space-y-1">
          <div className="text-[10px] uppercase font-bold tracking-wider text-[var(--text-muted)] px-2.5 py-1.5">
            Main Navigation
          </div>
          {navItems.map((item) => {
            const isActive = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => setIsMobileOpen(false)}
                className={`flex items-center gap-3 px-2.5 py-2 rounded-lg text-xs font-medium transition-all ${
                  isActive
                    ? "bg-[var(--accent-subtle)] text-[var(--accent-primary)] font-semibold border border-[var(--accent-border)] shadow-xs"
                    : "text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-tertiary)]"
                }`}
              >
                <div className={`${isActive ? "text-[var(--accent-primary)]" : "text-[var(--text-muted)]"}`}>
                  {item.icon}
                </div>
                <div className="flex-1 truncate">
                  <div className="truncate">{item.label}</div>
                  <div className="text-[10px] text-[var(--text-muted)] truncate font-normal">
                    {item.description}
                  </div>
                </div>
              </Link>
            );
          })}
        </div>

        {/* Footer: Facility Selector & Theme Toggle */}
        <div className="p-3 border-t border-[var(--border-subtle)] bg-[var(--bg-tertiary)]/50 space-y-2.5">
          {/* Active Operating Facility */}
          <div className="space-y-1">
            <div className="flex items-center justify-between text-[10px] text-[var(--text-muted)] font-semibold px-0.5">
              <span className="flex items-center gap-1">
                <Building2 className="w-3 h-3 text-[var(--accent-primary)]" />
                Active Facility:
              </span>
              <span className="font-mono text-[var(--accent-primary)] font-bold">{activeCpse}</span>
            </div>
            <select
              value={activeCpse}
              onChange={(e) => setActiveCpse(e.target.value)}
              className="w-full text-xs p-1.5 rounded-md bg-[var(--bg-secondary)] border border-[var(--border-primary)] text-[var(--text-primary)] cursor-pointer focus:outline-none focus:border-[var(--accent-primary)]"
            >
              {CPSE_OPTIONS.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.id} — {c.name.split(" ")[0]}
                </option>
              ))}
            </select>
            <div className="text-[10px] text-[var(--text-secondary)] truncate px-0.5">
              Depot: {currentCpseOption.defaultDepotName.split(",")[0]}
            </div>
          </div>

          {/* User Info & Theme */}
          <div className="flex items-center justify-between pt-2 border-t border-[var(--border-subtle)]">
            <div className="flex items-center gap-2 truncate">
              <div className="w-6 h-6 rounded-full bg-[var(--accent-subtle)] border border-[var(--accent-border)] flex items-center justify-center text-[10px] font-bold text-[var(--accent-primary)]">
                {activeCpse[0]}
              </div>
              <div className="truncate">
                <div className="text-[11px] font-bold text-[var(--text-primary)] truncate">Site Engineer</div>
                <div className="text-[9px] text-[var(--text-muted)] truncate">MoPNG Certified</div>
              </div>
            </div>
            <ThemeToggle />
          </div>
        </div>
      </aside>
    </>
  );
}
