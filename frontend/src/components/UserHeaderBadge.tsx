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
        className="flex items-center gap-1.5 px-2.5 py-1 bg-zinc-900 hover:bg-zinc-800 text-white dark:bg-zinc-100 dark:hover:bg-zinc-200 dark:text-zinc-900 rounded-md text-xs font-medium transition-colors shadow-2xs"
      >
        <LogIn size={12} />
        <span>Sign In</span>
      </Link>
    );
  }

  return (
    <div className="flex items-center gap-1.5">
      <Link
        href="/login"
        className="flex items-center gap-1.5 px-2 py-0.5 bg-zinc-100 dark:bg-zinc-800 hover:bg-zinc-200 dark:hover:bg-zinc-750 rounded-md text-xs font-mono text-zinc-700 dark:text-zinc-300 transition-colors border border-zinc-200 dark:border-zinc-700/80"
        title="Switch persona"
      >
        <Shield size={12} className="text-zinc-500" />
        <span className="font-medium">{user.username}</span>
        <span className="text-[9px] px-1 py-0.2 bg-zinc-200 dark:bg-zinc-700 text-zinc-700 dark:text-zinc-300 rounded font-sans">
          {user.cpse}
        </span>
      </Link>

      <button
        type="button"
        onClick={() => logout()}
        className="p-1 text-zinc-400 hover:text-rose-600 dark:hover:text-rose-400 rounded hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors cursor-pointer"
        title="Sign Out"
      >
        <LogOut size={13} />
      </button>
    </div>
  );
}
