"use client";

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useTheme } from './ThemeProvider';
import { LayoutDashboard, Upload, Package, Search, Truck, ShieldCheck, Building2 } from 'lucide-react';
import { ThemeToggle } from './ThemeToggle';

const CPSE_OPTIONS = [
  { id: 'OIL', name: 'Oil India Limited (OIL)' },
  { id: 'IOCL', name: 'Indian Oil Corporation (IOCL)' },
  { id: 'ONGC', name: 'Oil & Natural Gas Corp (ONGC)' },
  { id: 'BPCL', name: 'Bharat Petroleum (BPCL)' },
  { id: 'HPCL', name: 'Hindustan Petroleum (HPCL)' },
  { id: 'GAIL', name: 'GAIL (India) Limited' },
  { id: 'NRL', name: 'Numaligarh Refinery (NRL)' },
];

export function Sidebar() {
  const pathname = usePathname();
  const { cpse, setCpse } = useTheme();

  const links = [
    { name: 'Command Center', href: '/', icon: LayoutDashboard, exact: true },
    { name: 'Document Intake', href: '/upload', icon: Upload },
    { name: 'Stock Ledger', href: '/inventory', icon: Package },
    { name: 'Surplus Discovery', href: '/discover', icon: Search },
    { name: 'Consignments', href: '/requests', icon: Truck },
    { name: 'Audit Trail', href: '/audit', icon: ShieldCheck },
  ];

  return (
    <aside className="w-64 h-full bg-slate-100 dark:bg-slate-900 border-r border-slate-200 dark:border-slate-800 text-slate-800 dark:text-slate-100 flex flex-col no-print shrink-0 select-none">
      <div className="p-4 border-b border-slate-200 dark:border-slate-800">
        <div className="flex items-center gap-2 mb-3">
          <div className="w-8 h-8 rounded-lg bg-emerald-600 flex items-center justify-center font-bold font-mono text-white text-base shadow-xs">
            S
          </div>
          <div>
            <h1 className="text-base font-bold tracking-tight text-slate-900 dark:text-white leading-tight">Samanvay-AI</h1>
            <p className="text-[11px] font-mono text-emerald-700 dark:text-emerald-400 font-semibold">MoPNG Inter-CPSE Mesh</p>
          </div>
        </div>

        <div className="bg-white dark:bg-slate-800/80 rounded-md p-2 border border-slate-200 dark:border-slate-700/60 shadow-2xs">
          <div className="flex items-center gap-1.5 text-[10px] font-mono text-slate-500 dark:text-slate-400 mb-1">
            <Building2 size={12} className="text-emerald-600 dark:text-emerald-400" />
            <span>ACTIVE CPSE CONTEXT</span>
          </div>
          <select 
            value={cpse} 
            onChange={(e) => setCpse(e.target.value)}
            className="w-full bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded px-2 py-1 text-xs font-medium text-slate-900 dark:text-slate-200 focus:outline-hidden focus:ring-1 focus:ring-emerald-500 cursor-pointer"
          >
            {CPSE_OPTIONS.map(c => (
              <option key={c.id} value={c.id}>{c.name}</option>
            ))}
          </select>
        </div>
      </div>
      
      <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
        {links.map((link) => {
          const Icon = link.icon;
          const isActive = link.exact ? pathname === link.href : pathname.startsWith(link.href);
          return (
            <Link
              key={link.name}
              href={link.href}
              className={`flex items-center justify-between px-3 py-2 rounded-md text-sm transition-all ${
                isActive 
                  ? 'bg-emerald-600 text-white font-medium shadow-xs' 
                  : 'text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-800/80 hover:text-slate-900 dark:hover:text-white'
              }`}
            >
              <div className="flex items-center gap-2.5">
                <Icon size={18} className={isActive ? 'text-white' : 'text-slate-500 dark:text-slate-400'} />
                <span>{link.name}</span>
              </div>
            </Link>
          );
        })}
      </nav>
      
      <div className="p-3 border-t border-slate-200 dark:border-slate-800 flex flex-col gap-2">
        <ThemeToggle />
        <div className="flex items-center justify-between text-[11px] font-mono text-slate-500 dark:text-slate-400 px-1 pt-1 border-t border-slate-200/60 dark:border-slate-800/60">
          <span>CPSE NODE</span>
          <span className="text-emerald-600 dark:text-emerald-400 font-semibold">{cpse} · CONNECTED</span>
        </div>
      </div>
    </aside>
  );
}
