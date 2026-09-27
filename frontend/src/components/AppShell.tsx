'use client';

import React, { useState, ReactNode } from 'react';
import { usePathname } from 'next/navigation';
import { Sidebar } from '@/components/Sidebar';
import { PublicNavbar } from '@/components/PublicNavbar';
import { CommandPalette } from '@/components/CommandPalette';
import { useTheme } from '@/components/ThemeProvider';
import { Search, ChevronRight, Building2, Menu } from 'lucide-react';

import { useAuth } from '@/context/AuthContext';

interface AppShellProps {
  children: ReactNode;
}

const CPSE_OPTIONS = [
  { id: 'OIL', name: 'OIL (Duliajan)' },
  { id: 'IOCL', name: 'IOCL (Panipat)' },
  { id: 'ONGC', name: 'ONGC (Mumbai)' },
  { id: 'BPCL', name: 'BPCL (Kochi)' },
  { id: 'HPCL', name: 'HPCL (Visakh)' },
  { id: 'GAIL', name: 'GAIL (Pata)' },
  { id: 'NRL', name: 'NRL (Numaligarh)' },
];

const CPSE_DEPOTS: Record<string, string[]> = {
  OIL: ['Duliajan Central Stores', 'Digboi Warehouse', 'Moran Depot'],
  IOCL: ['Panipat Refinery Stores', 'Mathura Refinery Depot', 'Vadodara Stockyard'],
  ONGC: ['Mumbai Uran Plant', 'Hazira Plant Stores', 'Ankleshwar Base Depot'],
  BPCL: ['Kochi Refinery Depot', 'Mumbai Mahul Terminal', 'Bina Depot'],
  HPCL: ['Visakh Refinery Stores', 'Mumbai Refinery Depot', 'Bathinda Terminal'],
  GAIL: ['Pata Petrochemical Complex', 'Vijaipur Gas Plant', 'Hazira Terminal'],
  NRL: ['Numaligarh Refinery Depot', 'Siliguri Terminal'],
};

const ROUTE_TITLES: Record<string, string> = {
  '/dashboard': 'Command Center',
  '/discover': 'Surplus Discovery',
  '/inventory': 'Stock Ledger',
  '/upload': 'MTC Intake',
  '/upload/review': 'MTC Specification Review',
  '/requests': 'Consignments & Gate Passes',
  '/audit': 'Sovereign Audit Ledger',
  '/admin/users': 'User Approvals',
};

export function AppShell({ children }: AppShellProps) {
  const pathname = usePathname();
  const { cpse, setCpse } = useTheme();
  const { user } = useAuth();
  const [commandPaletteOpen, setCommandPaletteOpen] = useState(false);
  const [mobileDrawerOpen, setMobileDrawerOpen] = useState(false);
  const [adminDepot, setAdminDepot] = useState<string>('ALL');

  const isSuperAdmin = user?.role === 'SUPER_ADMIN';

  // Automatically lock CPSE context to the logged-in user's assigned CPSE if not SUPER_ADMIN
  React.useEffect(() => {
    if (user && !isSuperAdmin && user.cpse && user.cpse !== cpse) {
      setCpse(user.cpse);
    }
  }, [user, isSuperAdmin, cpse, setCpse]);

  // Auto-close mobile drawer on route change
  React.useEffect(() => {
    setMobileDrawerOpen(false);
  }, [pathname]);

  // Lock body scroll when mobile drawer is open
  React.useEffect(() => {
    if (mobileDrawerOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [mobileDrawerOpen]);

  const isPublicPage = pathname === '/' || pathname === '/login' || pathname === '/signup';

  if (isPublicPage) {
    return (
      <div className="flex flex-col min-h-screen bg-zinc-50 dark:bg-zinc-950 text-zinc-900 dark:text-zinc-100 font-sans">
        <PublicNavbar />
        <main className="flex-1">{children}</main>
        <footer className="border-t border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900/60 py-6 px-4 text-center text-xs text-zinc-500 dark:text-zinc-400">
          <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <span className="font-semibold text-zinc-800 dark:text-zinc-200">
                Samanvay-AI
              </span>
              <span>·</span>
              <span>Ministry of Petroleum & Natural Gas (MoPNG)</span>
            </div>
            <div className="flex items-center gap-3 text-zinc-400 dark:text-zinc-500 font-mono text-[11px]">
              <span>OIL</span>
              <span>IOCL</span>
              <span>ONGC</span>
              <span>BPCL</span>
              <span>HPCL</span>
              <span>GAIL</span>
              <span>NRL</span>
            </div>
            <p className="text-[11px]">
              Compliant with OISD, ASME B16.5, ASTM A105/A350, and DPIIT guidelines.
            </p>
          </div>
        </footer>
      </div>
    );
  }

  const currentTitle = ROUTE_TITLES[pathname] || (pathname.startsWith('/requests/') ? 'Consignment Gate Pass' : 'Workspace');

  return (
    <div className="flex h-screen overflow-hidden font-sans bg-zinc-50 dark:bg-zinc-950 text-zinc-900 dark:text-zinc-100 antialiased">
      {/* 1. Desktop Sidebar (Hidden on mobile) */}
      <div className="hidden md:flex md:shrink-0">
        <Sidebar />
      </div>

      {/* 2. Mobile Backdrop Overlay */}
      <div
        className={`fixed inset-0 z-40 bg-black/60 backdrop-blur-xs transition-opacity duration-200 md:hidden ${
          mobileDrawerOpen ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none'
        }`}
        onClick={() => setMobileDrawerOpen(false)}
        aria-hidden="true"
      />

      {/* 3. Mobile Slide-Over Sheet */}
      <div
        className={`fixed inset-y-0 left-0 z-50 w-72 max-w-[85vw] bg-white dark:bg-zinc-950 shadow-2xl transition-transform duration-200 ease-in-out md:hidden flex flex-col ${
          mobileDrawerOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
        role="dialog"
        aria-modal="true"
        aria-label="Navigation Menu"
      >
        <Sidebar isMobile={true} onCloseMobile={() => setMobileDrawerOpen(false)} />
      </div>

      {/* 4. Main Workspace Frame */}
      <div className="flex-1 flex flex-col min-w-0 w-full overflow-hidden">
        {/* Compact 48px Utility Bar */}
        <header className="h-12 border-b border-zinc-200 dark:border-zinc-800 bg-white/80 dark:bg-zinc-900/80 backdrop-blur-xs flex items-center justify-between px-3 sm:px-4 shrink-0 no-print z-10">
          {/* Left: Mobile Hamburger + Breadcrumbs */}
          <div className="flex items-center gap-1.5 sm:gap-2 min-w-0">
            {/* Hamburger Button for Mobile */}
            <button
              type="button"
              onClick={() => setMobileDrawerOpen(true)}
              className="md:hidden p-2 -ml-1 text-zinc-600 dark:text-zinc-300 hover:text-zinc-900 dark:hover:text-zinc-100 hover:bg-zinc-100 dark:hover:bg-zinc-800 rounded-md transition-colors min-h-[40px] min-w-[40px] flex items-center justify-center"
              aria-label="Open navigation menu"
            >
              <Menu size={18} />
            </button>

            {/* Breadcrumbs */}
            <div className="flex items-center gap-1.5 text-xs min-w-0">
              <span className="font-mono text-zinc-400 dark:text-zinc-500 hidden sm:inline">
                MoPNG Mesh
              </span>
              <ChevronRight size={12} className="text-zinc-400 dark:text-zinc-600 hidden sm:inline shrink-0" />
              <span className="font-medium text-zinc-900 dark:text-zinc-100 truncate max-w-[130px] sm:max-w-none">
                {currentTitle}
              </span>
            </div>
          </div>

          {/* Right: Command Palette Trigger + CPSE Tenant Switcher */}
          <div className="flex items-center gap-1.5 sm:gap-2.5">
            {/* Command Palette Button */}
            <button
              onClick={() => setCommandPaletteOpen(true)}
              className="flex items-center gap-2 px-2 sm:px-2.5 py-1 rounded-md bg-zinc-100 dark:bg-zinc-800/80 border border-zinc-200 dark:border-zinc-700/60 hover:border-zinc-300 dark:hover:border-zinc-600 text-xs text-zinc-500 dark:text-zinc-400 transition-colors shadow-2xs min-h-[34px]"
              title="Search parts, actions (⌘K)"
              aria-label="Search"
            >
              <Search size={13} className="text-zinc-400" />
              <span className="hidden md:inline">Search parts, actions...</span>
              <kbd className="hidden md:inline-flex items-center px-1 py-0.2 text-[10px] font-mono text-zinc-400 bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded">
                ⌘K
              </kbd>
            </button>

            {/* CPSE & Depot Indicator / Switcher */}
            {isSuperAdmin ? (
              <div className="flex items-center gap-1.5 px-2 py-1 rounded-md bg-zinc-100 dark:bg-zinc-800/80 border border-zinc-200 dark:border-zinc-700/60 text-xs font-mono min-h-[34px]">
                <span className="w-1.5 h-1.5 rounded-full bg-amber-500 shrink-0" title="Super Admin Mode: Tenant Switching Enabled" />
                <Building2 size={12} className="text-zinc-400 shrink-0 hidden sm:inline" />
                <select
                  value={cpse}
                  onChange={(e) => {
                    setCpse(e.target.value);
                    setAdminDepot('ALL');
                  }}
                  className="bg-transparent text-xs font-mono font-medium text-zinc-800 dark:text-zinc-200 outline-hidden cursor-pointer"
                  title="Switch active CPSE tenant context"
                >
                  {CPSE_OPTIONS.map((c) => (
                    <option key={c.id} value={c.id} className="bg-white dark:bg-zinc-900 text-zinc-900 dark:text-zinc-100">
                      {c.id}
                    </option>
                  ))}
                </select>

                {/* Depot Dual Selector for Super Admin */}
                <select
                  value={adminDepot}
                  onChange={(e) => setAdminDepot(e.target.value)}
                  className="bg-transparent text-xs font-mono text-zinc-600 dark:text-zinc-400 outline-hidden cursor-pointer border-l border-zinc-300 dark:border-zinc-700 pl-1.5 hidden lg:inline max-w-[150px] truncate"
                  title="Filter active Depot/Unit"
                >
                  <option value="ALL" className="bg-white dark:bg-zinc-900 text-zinc-900 dark:text-zinc-100">All Units</option>
                  {(CPSE_DEPOTS[cpse] || []).map((d) => (
                    <option key={d} value={d} className="bg-white dark:bg-zinc-900 text-zinc-900 dark:text-zinc-100">
                      {d}
                    </option>
                  ))}
                </select>
              </div>
            ) : (
              <div
                className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-zinc-100 dark:bg-zinc-800/80 border border-zinc-200 dark:border-zinc-700/60 text-xs font-mono min-h-[34px]"
                title={`Assigned Organization: ${user?.cpse || cpse} | Unit: ${user?.depot_id || 'Primary Depot'}`}
              >
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 shrink-0" title="Assigned Unit Active" />
                <Building2 size={12} className="text-zinc-400 shrink-0 hidden sm:inline" />
                <span className="font-semibold text-zinc-800 dark:text-zinc-200">{user?.cpse || cpse}</span>
                {user?.depot_id && (
                  <span className="text-zinc-500 dark:text-zinc-400 border-l border-zinc-300 dark:border-zinc-700 pl-1.5 hidden md:inline truncate max-w-[160px]">
                    {user.depot_id}
                  </span>
                )}
              </div>
            )}
          </div>
        </header>

        {/* Scrollable Viewport */}
        <main className="flex-1 overflow-auto bg-zinc-50/50 dark:bg-zinc-950 p-3 sm:p-5 md:p-6 print:p-0 print:bg-white">
          {children}
        </main>
      </div>

      {/* Global Command Palette */}
      <CommandPalette
        isOpen={commandPaletteOpen}
        onClose={() => setCommandPaletteOpen(false)}
      />
    </div>
  );
}
