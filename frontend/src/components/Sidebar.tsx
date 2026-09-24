"use client";

import React, { useEffect } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useTheme } from './ThemeProvider';
import { useAuth } from '@/context/AuthContext';
import {
  LayoutDashboard,
  Upload,
  Package,
  Search,
  Truck,
  ShieldCheck,
  Building2,
  KeyRound,
  LogOut,
  User as UserIcon,
  UserCheck,
} from 'lucide-react';
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
  const { user, isAuthenticated, logout } = useAuth();

  // Sync active CPSE context with logged-in user tenant
  useEffect(() => {
    if (user?.cpse && CPSE_OPTIONS.some((c) => c.id === user.cpse)) {
      setCpse(user.cpse);
    }
  }, [user, setCpse]);

  const role = user?.role || 'SITE_ENGINEER';

  const allLinks = [
    {
      name: 'Command Center',
      href: '/dashboard',
      icon: LayoutDashboard,
      exact: true,
      roles: ['SITE_ENGINEER', 'MATERIALS_MANAGER', 'TECHNICAL_AUTHORITY', 'CISF_SECURITY', 'VIGILANCE_AUDITOR', 'SUPER_ADMIN'],
    },
    {
      name: 'Surplus Discovery',
      href: '/discover',
      icon: Search,
      roles: ['SITE_ENGINEER', 'MATERIALS_MANAGER', 'TECHNICAL_AUTHORITY', 'VIGILANCE_AUDITOR', 'SUPER_ADMIN'],
    },
    {
      name: 'Stock Ledger',
      href: '/inventory',
      icon: Package,
      roles: ['SITE_ENGINEER', 'MATERIALS_MANAGER', 'TECHNICAL_AUTHORITY', 'VIGILANCE_AUDITOR', 'SUPER_ADMIN'],
    },
    {
      name: 'Document Intake',
      href: '/upload',
      icon: Upload,
      roles: ['SITE_ENGINEER', 'MATERIALS_MANAGER', 'TECHNICAL_AUTHORITY', 'SUPER_ADMIN'],
    },
    {
      name: 'Consignments',
      href: '/requests',
      icon: Truck,
      roles: ['SITE_ENGINEER', 'MATERIALS_MANAGER', 'TECHNICAL_AUTHORITY', 'CISF_SECURITY', 'VIGILANCE_AUDITOR', 'SUPER_ADMIN'],
    },
    {
      name: 'Audit Trail',
      href: '/audit',
      icon: ShieldCheck,
      roles: ['VIGILANCE_AUDITOR', 'SUPER_ADMIN'],
    },
    {
      name: 'User Approvals',
      href: '/admin/users',
      icon: UserCheck,
      roles: ['SUPER_ADMIN'],
    },
  ];

  const visibleLinks = allLinks.filter(
    (link) => !user || link.roles.includes(role) || role === 'SUPER_ADMIN'
  );

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
        {visibleLinks.map((link) => {
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

      {/* User Persona / Session Panel */}
      <div className="px-3 pb-2">
        {isAuthenticated && user ? (
          <div className="p-2.5 rounded-lg bg-white dark:bg-slate-800/90 border border-slate-200 dark:border-slate-700 shadow-2xs">
            <div className="flex items-start justify-between gap-1.5 mb-1">
              <div className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
                <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                  {user.cpse} IDENTITY
                </span>
              </div>
              <button
                type="button"
                onClick={() => logout()}
                className="text-slate-400 hover:text-rose-600 dark:hover:text-rose-400 p-0.5 rounded cursor-pointer"
                title="Sign Out"
              >
                <LogOut size={13} />
              </button>
            </div>
            <p className="text-xs font-semibold text-slate-900 dark:text-slate-100 truncate">
              {user.full_name}
            </p>
            <div className="flex items-center justify-between mt-1 text-[10px] font-mono text-slate-500 dark:text-slate-400">
              <span className="truncate">{user.role.replace('_', ' ')}</span>
            </div>
          </div>
        ) : (
          <Link
            href="/login"
            className="flex items-center justify-between p-2.5 rounded-lg bg-white dark:bg-slate-800 border border-dashed border-slate-300 dark:border-slate-700 hover:border-emerald-500 dark:hover:border-emerald-500 text-xs text-slate-600 dark:text-slate-300 transition-colors shadow-2xs"
          >
            <div className="flex items-center gap-2">
              <UserIcon size={14} className="text-slate-400" />
              <span>Sign In</span>
            </div>
            <span className="text-[10px] font-mono text-emerald-600 dark:text-emerald-400 font-semibold">
              Go →
            </span>
          </Link>
        )}
      </div>

      {/* Footer with ThemeToggle strictly at bottom-left */}
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
