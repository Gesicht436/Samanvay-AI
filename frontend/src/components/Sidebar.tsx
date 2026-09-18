"use client";

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useTheme } from './ThemeProvider';
import { CPSE_DEPOTS } from '@/lib/constants';
import { LayoutDashboard, Upload, Package, Search, Truck, ShieldCheck, Building2 } from 'lucide-react';

export function Sidebar() {
  const pathname = usePathname();
  const { cpse, setCpse } = useTheme();

  const links = [
    { name: 'Command Center', href: '/', icon: LayoutDashboard, exact: true },
    { name: 'Document Intake', href: '/upload', icon: Upload },
    { name: 'Stock Ledger', href: '/inventory', icon: Package, badge: '1,420' },
    { name: 'Surplus Discovery', href: '/discover', icon: Search },
    { name: 'Consignments', href: '/requests', icon: Truck, badge: '2 Active', badgeAlert: true },
    { name: 'Audit Trail', href: '/audit', icon: ShieldCheck },
  ];

  return (
    <aside className="w-64 h-full bg-slate-900 border-r border-slate-800 text-slate-100 flex flex-col no-print shrink-0 select-none">
      <div className="p-4 border-b border-slate-800/80">
        <div className="flex items-center gap-2 mb-3">
          <div className="w-8 h-8 rounded-lg bg-emerald-600 flex items-center justify-center font-bold font-mono text-white text-base shadow-sm">
            S
          </div>
          <div>
            <h1 className="text-base font-bold tracking-tight text-white leading-tight">Samanvay-AI</h1>
            <p className="text-[10px] font-mono text-slate-400">MoPNG Inter-CPSE Mesh</p>
          </div>
        </div>

        <div className="bg-slate-800/80 rounded-md p-2 border border-slate-700/60">
          <div className="flex items-center gap-1.5 text-[11px] font-mono text-slate-400 mb-1">
            <Building2 size={12} className="text-emerald-400" />
            <span>OPERATING CPSE NODE</span>
          </div>
          <select 
            value={cpse} 
            onChange={(e) => setCpse(e.target.value)}
            className="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-xs font-medium text-slate-200 focus:outline-none focus:ring-1 focus:ring-emerald-500 cursor-pointer"
          >
            {CPSE_DEPOTS.map(d => (
              <option key={d.id} value={d.id}>{d.name}</option>
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
                  : 'text-slate-300 hover:bg-slate-800/80 hover:text-white'
              }`}
            >
              <div className="flex items-center gap-2.5">
                <Icon size={18} className={isActive ? 'text-white' : 'text-slate-400'} />
                <span>{link.name}</span>
              </div>
              {link.badge && (
                <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded ${
                  link.badgeAlert 
                    ? (isActive ? 'bg-white/20 text-white font-bold' : 'bg-amber-500/20 text-amber-300 border border-amber-500/30')
                    : (isActive ? 'bg-emerald-700 text-emerald-100' : 'bg-slate-800 text-slate-400')
                }`}>
                  {link.badge}
                </span>
              )}
            </Link>
          );
        })}
      </nav>
      
      <div className="p-3 border-t border-slate-800 text-[11px] text-slate-400 font-mono flex items-center justify-between">
        <span>SOVEREIGN NODE #01</span>
        <span className="text-emerald-400 font-semibold">ONLINE</span>
      </div>
    </aside>
  );
}
