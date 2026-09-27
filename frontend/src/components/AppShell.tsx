'use client';

import React, { useState, ReactNode } from 'react';
import { usePathname } from 'next/navigation';
import { Sidebar } from '@/components/Sidebar';
import { PublicNavbar } from '@/components/PublicNavbar';
import { CommandPalette } from '@/components/CommandPalette';
import { useTheme } from '@/components/ThemeProvider';
import { Search, ChevronRight, Building2 } from 'lucide-react';

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
  const [commandPaletteOpen, setCommandPaletteOpen] = useState(false);

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
      {/* Collapsible Sidebar */}
      <Sidebar />

      {/* Main Workspace Frame */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Compact 48px Utility Bar */}
        <header className="h-12 border-b border-zinc-200 dark:border-zinc-800 bg-white/80 dark:bg-zinc-900/80 backdrop-blur-xs flex items-center justify-between px-4 shrink-0 no-print z-10">
          {/* Breadcrumbs */}
          <div className="flex items-center gap-2 text-xs min-w-0">
            <span className="font-mono text-zinc-400 dark:text-zinc-500 hidden sm:inline">
              MoPNG Mesh
            </span>
            <ChevronRight size={12} className="text-zinc-400 dark:text-zinc-600 hidden sm:inline" />
            <span className="font-medium text-zinc-900 dark:text-zinc-100 truncate">
              {currentTitle}
            </span>
          </div>

          {/* Center/Right: Command Palette Trigger + CPSE Tenant Switcher */}
          <div className="flex items-center gap-2.5">
            {/* Command Palette Button */}
            <button
              onClick={() => setCommandPaletteOpen(true)}
              className="flex items-center gap-2 px-2.5 py-1 rounded-md bg-zinc-100 dark:bg-zinc-800/80 border border-zinc-200 dark:border-zinc-700/60 hover:border-zinc-300 dark:hover:border-zinc-600 text-xs text-zinc-500 dark:text-zinc-400 transition-colors shadow-2xs"
            >
              <Search size={13} className="text-zinc-400" />
              <span className="hidden md:inline">Search parts, actions...</span>
              <kbd className="inline-flex items-center px-1 py-0.2 text-[10px] font-mono text-zinc-400 bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded">
                ⌘K
              </kbd>
            </button>

            {/* CPSE Tenant Switcher Dropdown */}
            <div className="flex items-center gap-1.5 px-2 py-1 rounded-md bg-zinc-100 dark:bg-zinc-800/80 border border-zinc-200 dark:border-zinc-700/60 text-xs font-mono">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 shrink-0" title="Backend Gateway: Live" />
              <Building2 size={12} className="text-zinc-400 shrink-0" />
              <select
                value={cpse}
                onChange={(e) => setCpse(e.target.value)}
                className="bg-transparent text-xs font-mono font-medium text-zinc-800 dark:text-zinc-200 outline-hidden cursor-pointer pr-1"
                title="Select active CPSE tenant context"
              >
                {CPSE_OPTIONS.map((c) => (
                  <option key={c.id} value={c.id} className="bg-white dark:bg-zinc-900 text-zinc-900 dark:text-zinc-100">
                    {c.id}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </header>

        {/* Scrollable Viewport */}
        <main className="flex-1 overflow-auto bg-zinc-50/50 dark:bg-zinc-950 p-5 md:p-6 print:p-0 print:bg-white">
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
