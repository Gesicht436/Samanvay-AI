'use client';

import React from 'react';
import Link from 'next/link';
import { useAuth } from '@/context/AuthContext';
import { User, LogIn, LogOut, Shield } from 'lucide-react';

export function UserHeaderBadge() {
  const { user, isAuthenticated, logout } = useAuth();

  if (!isAuthenticated || !user) {
    return (
      <Link
        href="/login"
        className="flex items-center gap-1.5 px-3 py-1 bg-emerald-600 hover:bg-emerald-700 text-white rounded text-xs font-medium transition-colors shadow-2xs"
      >
        <LogIn size={13} />
        <span>Sign In</span>
      </Link>
    );
  }

  return (
    <div className="flex items-center gap-2">
      <Link
        href="/login"
        className="flex items-center gap-2 px-2.5 py-1 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 rounded text-xs font-mono text-slate-700 dark:text-slate-200 transition-colors border border-slate-200 dark:border-slate-700"
        title="Click to switch persona"
      >
        <Shield size={12} className="text-emerald-600 dark:text-emerald-400" />
        <span className="font-semibold">{user.username}</span>
        <span className="text-[10px] px-1 py-0.2 bg-emerald-100 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-300 rounded font-sans">
          {user.cpse}
        </span>
      </Link>

      <button
        type="button"
        onClick={() => logout()}
        className="p-1 text-slate-400 hover:text-rose-600 dark:hover:text-rose-400 rounded hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors cursor-pointer"
        title="Sign Out"
      >
        <LogOut size={14} />
      </button>
    </div>
  );
}
