'use client';

import React from 'react';
import Link from 'next/link';
import { useAuth } from '@/context/AuthContext';
import { ThemeToggle } from '@/components/ThemeToggle';
import { ArrowRight, UserCheck, KeyRound, UserPlus } from 'lucide-react';

// AUTH-006 Phase 2: production builds must not offer public signup. The
// build-mode flag reuses the framework's existing NODE_ENV mechanism.
const isProductionBuild = process.env.NODE_ENV === 'production';
  const { user, isAuthenticated } = useAuth();

  return (
    <header className="sticky top-0 z-50 w-full bg-white/90 dark:bg-zinc-950/90 backdrop-blur-md border-b border-zinc-200 dark:border-zinc-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 h-12 flex items-center justify-between">
        {/* Brand & Emblem */}
        <Link href="/" className="flex items-center gap-2.5">
          <div className="w-6 h-6 rounded-md bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900 flex items-center justify-center font-mono font-bold text-xs shrink-0 tracking-tighter">
            SV
          </div>
          <div className="flex items-center gap-2">
            <span className="font-semibold text-xs tracking-tight text-zinc-900 dark:text-zinc-100">
              SAMANVAY-AI
            </span>
            <span className="hidden sm:inline-block px-1.5 py-0.2 text-[9px] font-mono font-medium text-zinc-500 bg-zinc-100 dark:bg-zinc-800 rounded border border-zinc-200 dark:border-zinc-750">
              MoPNG Mesh
            </span>
          </div>
        </Link>

        {/* Center Nav Links (Desktop) */}
        <nav className="hidden md:flex items-center gap-6 text-xs text-zinc-600 dark:text-zinc-400">
          <Link href="/#mission" className="hover:text-zinc-900 dark:hover:text-zinc-100 transition-colors">
            Mission
          </Link>
          <Link href="/#safety-gates" className="hover:text-zinc-900 dark:hover:text-zinc-100 transition-colors">
            21 Safety Gates
          </Link>
          <Link href="/#cpse-mesh" className="hover:text-zinc-900 dark:hover:text-zinc-100 transition-colors">
            CPSE Mesh
          </Link>
          <Link href="/#governance" className="hover:text-zinc-900 dark:hover:text-zinc-100 transition-colors">
            Audit Ledger
          </Link>
        </nav>

        {/* Actions & Session */}
        <div className="flex items-center gap-2.5">
          <ThemeToggle />

          {isAuthenticated && user ? (
            <Link
              href="/dashboard"
              className="flex items-center gap-1.5 px-3 py-1 bg-zinc-900 hover:bg-zinc-800 text-white dark:bg-zinc-100 dark:hover:bg-zinc-200 dark:text-zinc-900 rounded-md text-xs font-medium transition-colors"
            >
              <UserCheck size={13} />
              <span>Workspace ({user.cpse})</span>
              <ArrowRight size={12} />
            </Link>
          ) : (
            <div className="flex items-center gap-2">
              <Link
                href="/login"
                className="flex items-center gap-1.5 px-2.5 py-1 text-xs text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100 transition-colors"
              >
                <KeyRound size={13} />
                <span>Sign In</span>
              </Link>
              {!isProductionBuild && (
                <Link
                  href="/signup"
                  className="flex items-center gap-1.5 px-3 py-1 bg-zinc-900 hover:bg-zinc-800 text-white dark:bg-zinc-100 dark:hover:bg-zinc-200 dark:text-zinc-900 rounded-md text-xs font-medium transition-colors"
                >
                  <UserPlus size={13} />
                  <span>Register</span>
                </Link>
              )}
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
