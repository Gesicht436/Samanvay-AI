'use client';

import React from 'react';
import Link from 'next/link';
import { useAuth } from '@/context/AuthContext';
import { UserCheck, ArrowRight, KeyRound, UserPlus } from 'lucide-react';

// AUTH-006 Phase 2: production builds must not offer public signup. The
// build-mode flag reuses the framework's existing NODE_ENV mechanism.
const isProductionBuild = process.env.NODE_ENV === 'production';
  const { user, isAuthenticated } = useAuth();

  return (
    <div className="pt-4 flex flex-wrap items-center justify-center gap-4">
      {isAuthenticated && user ? (
        <div className="p-4 bg-white dark:bg-zinc-800 border border-emerald-500 dark:border-emerald-600 rounded-xl shadow-xs flex flex-col sm:flex-row items-center gap-4">
          <div className="text-left">
            <div className="flex items-center gap-2">
              <UserCheck className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
              <p className="font-bold text-xs text-zinc-900 dark:text-white">
                Logged in as {user.full_name}
              </p>
              <span className="px-1.5 py-0.5 text-[10px] font-mono bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300 rounded">
                {user.cpse} · {user.role.replace('_', ' ')}
              </span>
            </div>
            <p className="text-[11px] text-zinc-500 font-mono mt-0.5">
              Assigned Depot: {user.depot_id}
            </p>
          </div>
          <Link
            href="/dashboard"
            className="py-2.5 px-5 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-xs rounded-lg transition-all shadow-xs flex items-center gap-2 shrink-0"
          >
            <span>Enter My Authorized Workspace</span>
            <ArrowRight size={14} />
          </Link>
        </div>
      ) : (
        <>
          <Link
            href="/login"
            className="py-3 px-6 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-xs rounded-lg transition-all shadow-xs flex items-center gap-2"
          >
            <KeyRound size={15} />
            <span>Sign In to Sovereign Node</span>
            <ArrowRight size={14} />
          </Link>

          {!isProductionBuild && (
            <Link
              href="/signup"
              className="py-3 px-6 bg-white dark:bg-zinc-800 hover:bg-zinc-100 dark:hover:bg-zinc-700 text-zinc-800 dark:text-zinc-100 font-semibold text-xs rounded-lg border border-zinc-300 dark:border-zinc-700 transition-all flex items-center gap-2"
            >
              <UserPlus size={15} />
              <span>Register CPSE Officer</span>
            </Link>
          )}
        </>
      )}
    </div>
  );
}
