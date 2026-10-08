'use client';

import React from 'react';
import Link from 'next/link';
import { UserPlus, ArrowRight } from 'lucide-react';

// AUTH-006 Phase 2 / Task 16A: the legacy public self-registration flow is
// retired. POST /auth/signup does not exist on the backend, and public
// registration is not part of the current session-cookie authentication
// architecture. This route exists only as an intentional informational state
// so existing navigation references to /signup resolve honestly instead of
// rendering a dead form. Account provisioning remains a backend-only,
// authenticated administrative capability; no client-side registration is
// offered in any build.

export default function SignupPage() {
  return (
    <div className="max-w-2xl mx-auto py-10 px-4">
      <div className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-xl p-6 sm:p-8 shadow-xs text-center">
        <div className="w-12 h-12 mx-auto mb-4 rounded-xl bg-zinc-100 dark:bg-zinc-800 flex items-center justify-center">
          <UserPlus className="w-6 h-6 text-zinc-500" />
        </div>
        <h1 className="text-lg font-bold text-zinc-900 dark:text-white">
          Registration Unavailable
        </h1>
        <p className="text-xs text-zinc-500 dark:text-zinc-400 mt-2 leading-relaxed">
          Public self-registration is disabled. Accounts are created only
          through the authorized administrative provisioning process. Please
          sign in with your assigned CPSE credentials.
        </p>
        <div className="mt-6 flex items-center justify-center gap-3">
          <Link
            href="/login"
            className="py-2.5 px-5 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-xs rounded-lg transition-colors flex items-center gap-2"
          >
            <span>Sign In</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
          <Link
            href="/"
            className="py-2.5 px-5 bg-zinc-100 dark:bg-zinc-800 hover:bg-zinc-200 dark:hover:bg-zinc-700 text-zinc-700 dark:text-zinc-300 font-semibold text-xs rounded-lg transition-colors"
          >
            Return to Public Portal
          </Link>
        </div>
      </div>
    </div>
  );
}
