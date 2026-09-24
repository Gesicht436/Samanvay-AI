'use client';

import React, { ReactNode } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import { ShieldAlert, ArrowLeft, KeyRound, Building2, Lock } from 'lucide-react';

interface ProtectedRouteProps {
  children: ReactNode;
  allowedRoles?: string[];
}

export function ProtectedRoute({ children, allowedRoles }: ProtectedRouteProps) {
  const { user, isAuthenticated, isLoading } = useAuth();
  const pathname = usePathname();
  const router = useRouter();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-3 border-emerald-600 border-t-transparent rounded-full animate-spin"></div>
          <p className="text-xs font-mono text-slate-500 dark:text-slate-400">
            Verifying Sovereign Identity Claims...
          </p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated || !user) {
    return (
      <div className="max-w-md mx-auto my-12 p-6 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl shadow-sm text-center">
        <div className="w-12 h-12 mx-auto mb-4 rounded-xl bg-amber-100 dark:bg-amber-950/60 flex items-center justify-center text-amber-600 dark:text-amber-400">
          <Lock className="w-6 h-6" />
        </div>
        <h2 className="text-base font-bold text-slate-900 dark:text-white">
          Authentication Required
        </h2>
        <p className="text-xs text-slate-600 dark:text-slate-400 mt-1.5 leading-relaxed">
          This module is part of the restricted MoPNG Sovereign Spare Parts Mesh. Please sign in with your authorized CPSE credentials to proceed.
        </p>
        <div className="mt-6 flex flex-col gap-2">
          <Link
            href={`/login?redirect=${encodeURIComponent(pathname)}`}
            className="w-full py-2.5 px-4 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-xs rounded-lg transition-colors shadow-xs flex items-center justify-center gap-2"
          >
            <KeyRound className="w-4 h-4" />
            <span>Sign In to Access</span>
          </Link>
          <Link
            href="/"
            className="w-full py-2 px-4 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 font-medium text-xs rounded-lg transition-colors"
          >
            Return to Public Portal
          </Link>
        </div>
      </div>
    );
  }

  // Check role authorization if specified
  if (allowedRoles && allowedRoles.length > 0) {
    const isAuthorized = allowedRoles.includes(user.role) || user.role === 'SUPER_ADMIN';

    if (!isAuthorized) {
      return (
        <div className="max-w-xl mx-auto my-8 p-6 bg-white dark:bg-slate-900 border border-rose-200 dark:border-rose-900/60 rounded-xl shadow-xs">
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 rounded-xl bg-rose-100 dark:bg-rose-950/60 flex items-center justify-center text-rose-600 dark:text-rose-400 shrink-0">
              <ShieldAlert className="w-6 h-6" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <h2 className="text-base font-bold text-slate-900 dark:text-white">
                  Access Clearance Restricted (403)
                </h2>
                <span className="px-1.5 py-0.5 text-[10px] font-mono font-semibold uppercase bg-rose-100 text-rose-800 dark:bg-rose-900/50 dark:text-rose-300 rounded border border-rose-300 dark:border-rose-800">
                  Segregation of Duties
                </span>
              </div>

              <div className="mt-3 p-3 bg-slate-50 dark:bg-slate-800/80 rounded-lg border border-slate-200 dark:border-slate-700/60 text-xs space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="text-slate-500 dark:text-slate-400">Authenticated Personnel:</span>
                  <span className="font-semibold text-slate-900 dark:text-white">{user.full_name}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-500 dark:text-slate-400">Assigned Domain:</span>
                  <span className="font-mono text-slate-700 dark:text-slate-300">{user.cpse} ({user.depot_id})</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-500 dark:text-slate-400">Your Current Role:</span>
                  <span className="font-mono font-semibold text-rose-600 dark:text-rose-400">{user.role.replace('_', ' ')}</span>
                </div>
              </div>

              <p className="text-xs text-slate-600 dark:text-slate-400 mt-3 leading-relaxed">
                In accordance with Ministry of Petroleum & Natural Gas Sovereign Security and Statutory Audit protocols, this operational capability is restricted strictly to:
              </p>

              <div className="mt-2 flex flex-wrap gap-1.5">
                {allowedRoles.map((role) => (
                  <span
                    key={role}
                    className="px-2 py-1 text-[11px] font-mono font-semibold bg-slate-100 dark:bg-slate-800 text-slate-800 dark:text-slate-200 rounded border border-slate-300 dark:border-slate-700"
                  >
                    {role.replace('_', ' ')}
                  </span>
                ))}
              </div>

              <div className="mt-6 pt-4 border-t border-slate-100 dark:border-slate-800 flex flex-wrap items-center gap-3">
                <Link
                  href="/dashboard"
                  className="py-2 px-4 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-xs rounded-lg transition-colors shadow-xs flex items-center gap-2"
                >
                  <ArrowLeft className="w-3.5 h-3.5" />
                  <span>Go to My Authorized Workspace</span>
                </Link>
                <Link
                  href="/login"
                  className="py-2 px-4 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 font-medium text-xs rounded-lg transition-colors flex items-center gap-1.5"
                >
                  <KeyRound className="w-3.5 h-3.5" />
                  <span>Switch Account</span>
                </Link>
              </div>
            </div>
          </div>
        </div>
      );
    }
  }

  return <>{children}</>;
}
