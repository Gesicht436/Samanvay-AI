'use client';

import React, { ReactNode } from 'react';
import { usePathname } from 'next/navigation';
import { Sidebar } from '@/components/Sidebar';
import { UserHeaderBadge } from '@/components/UserHeaderBadge';
import { PublicNavbar } from '@/components/PublicNavbar';

interface AppShellProps {
  children: ReactNode;
}

export function AppShell({ children }: AppShellProps) {
  const pathname = usePathname();
  const isPublicPage = pathname === '/' || pathname === '/login' || pathname === '/signup';

  if (isPublicPage) {
    return (
      <div className="flex flex-col min-h-screen bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 font-sans">
        <PublicNavbar />
        <main className="flex-1">
          {children}
        </main>
        <footer className="border-t border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/60 py-8 px-4 text-center text-xs text-slate-500 dark:text-slate-400">
          <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <span className="font-semibold text-slate-800 dark:text-slate-200">
                Samanvay-AI | SIH26099
              </span>
              <span>·</span>
              <span>Ministry of Petroleum & Natural Gas (MoPNG)</span>
            </div>
            <div className="flex items-center gap-4 text-[11px] font-mono">
              <span>OIL</span>
              <span>•</span>
              <span>IOCL</span>
              <span>•</span>
              <span>ONGC</span>
              <span>•</span>
              <span>BPCL</span>
              <span>•</span>
              <span>HPCL</span>
              <span>•</span>
              <span>GAIL</span>
              <span>•</span>
              <span>NRL</span>
            </div>
            <p className="text-[11px]">
              Strictly compliant with BIS, OISD, EIL 6-44, and Make in India (DPIIT) guidelines.
            </p>
          </div>
        </footer>
      </div>
    );
  }

  // Internal Authenticated Workspace Layout
  return (
    <div className="flex h-screen overflow-hidden font-sans bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0">
        <header className="h-14 border-b border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 flex items-center justify-between px-6 shrink-0 no-print">
          <div className="flex items-center gap-3">
            <span className="font-semibold text-sm tracking-wide text-slate-900 dark:text-slate-100">
              MINISTRY OF PETROLEUM & NATURAL GAS
            </span>
            <span className="text-xs text-slate-400">|</span>
            <span className="text-xs font-mono text-slate-600 dark:text-slate-300">
              Inter-CPSE Spare Parts & Material Sharing Mesh
            </span>
          </div>
          <div className="flex items-center gap-3">
            <UserHeaderBadge />
            <div className="flex items-center gap-2 px-2.5 py-1 bg-slate-100 dark:bg-slate-800 rounded text-xs font-mono text-slate-700 dark:text-slate-300">
              <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
              <span>Backend Gateway: Connected</span>
            </div>
          </div>
        </header>
        <main className="flex-1 overflow-auto bg-slate-50 dark:bg-slate-950 p-6 print:p-0 print:bg-white">
          {children}
        </main>
      </div>
    </div>
  );
}
