'use client';

import React from 'react';
import Link from 'next/link';
import { useAuth } from '@/context/AuthContext';
import { ThemeToggle } from '@/components/ThemeToggle';
import { Shield, ArrowRight, UserCheck, KeyRound, UserPlus } from 'lucide-react';

export function PublicNavbar() {
  const { user, isAuthenticated } = useAuth();

  return (
    <header className="sticky top-0 z-50 w-full bg-white/95 dark:bg-slate-900/95 backdrop-blur-md border-b border-slate-200 dark:border-slate-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand & Emblem */}
        <Link href="/" className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-emerald-600 flex items-center justify-center font-bold font-mono text-white text-lg shadow-sm">
            S
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-base tracking-tight text-slate-900 dark:text-white">
                Samanvay-AI
              </span>
              <span className="hidden sm:inline-block px-1.5 py-0.5 text-[10px] font-mono font-semibold bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300 rounded border border-emerald-300 dark:border-emerald-700">
                MoPNG Sovereign
              </span>
            </div>
            <p className="text-[11px] font-mono text-slate-500 dark:text-slate-400 leading-tight">
              Cross-CPSE Spare Parts & Material Sharing Mesh
            </p>
          </div>
        </Link>

        {/* Center Nav Links (Desktop) */}
        <nav className="hidden md:flex items-center gap-6 text-xs font-medium text-slate-600 dark:text-slate-300">
          <Link href="/#mission" className="hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors">
            Mission & Impact
          </Link>
          <Link href="/#safety-gates" className="hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors">
            21 Safety Gates
          </Link>
          <Link href="/#cpse-mesh" className="hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors">
            CPSE Topology
          </Link>
          <Link href="/#governance" className="hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors">
            Audit Ledger
          </Link>
        </nav>

        {/* Actions & Session */}
        <div className="flex items-center gap-3">
          <ThemeToggle />

          {isAuthenticated && user ? (
            <Link
              href="/dashboard"
              className="flex items-center gap-2 px-3.5 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-semibold transition-all shadow-xs"
            >
              <UserCheck size={14} />
              <span>Enter Workspace ({user.cpse})</span>
              <ArrowRight size={13} />
            </Link>
          ) : (
            <div className="flex items-center gap-2">
              <Link
                href="/login"
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-700 dark:text-slate-200 hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors"
              >
                <KeyRound size={13} />
                <span>Sign In</span>
              </Link>
              <Link
                href="/signup"
                className="flex items-center gap-1.5 px-3.5 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-semibold transition-all shadow-xs"
              >
                <UserPlus size={13} />
                <span>Register Officer</span>
              </Link>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
