'use client';

import React, { useState, useEffect, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/context/AuthContext';
import {
  Shield,
  KeyRound,
  UserCheck,
  Building2,
  Lock,
  ArrowRight,
  AlertCircle,
  CheckCircle2,
  Cpu,
  Sparkles,
  Copy,
  Info,
  ChevronRight,
  ShieldAlert,
} from 'lucide-react';
import { SeedUser } from '@/lib/types';

const CPSE_TABS = [
  'ALL',
  'OIL',
  'IOCL',
  'ONGC',
  'BPCL',
  'HPCL',
  'GAIL',
  'NRL',
  'MOPNG',
  'ADMIN',
];

export default function LoginPage() {
  const router = useRouter();
  const { user, login, isAuthenticated, seedUsers, defaultSeedPassword } = useAuth();

  // AUTH-006 Phase 2: the 1-click persona hub, visible seed passwords, and
  // seeded-credential helpers are evaluation-only. Next.js statically replaces
  // process.env.NODE_ENV at build time, so the production bundle never
  // contains seed usernames, seed passwords, or one-click seed login paths.
  // No new environment variable is introduced; this reuses the framework's
  // existing build-mode mechanism.
  const isProductionBuild = process.env.NODE_ENV === 'production';
  const showEvaluationHub = !isProductionBuild;

  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [loggingInUsername, setLoggingInUsername] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [selectedCpseTab, setSelectedCpseTab] = useState<string>('ALL');
  const [copiedUser, setCopiedUser] = useState<string | null>(null);

  const handleLogin = async (e?: React.FormEvent, customUser?: string, customPass?: string) => {
    if (e) e.preventDefault();
    setError(null);
    setSuccessMsg(null);
    setIsSubmitting(true);

    const u = customUser !== undefined ? customUser : username;
    const p = customPass !== undefined ? customPass : password;

    if (!u.trim()) {
      setError('Please enter your CPSE username or ID.');
      setIsSubmitting(false);
      return;
    }

    try {
      setLoggingInUsername(u);
      const loggedUser = await login(u, p);
      setSuccessMsg(`Welcome, ${loggedUser.full_name} (${loggedUser.cpse || 'MoPNG'})`);
      const redirectUrl = typeof window !== 'undefined' ? new URLSearchParams(window.location.search).get('redirect') : null;
      setTimeout(() => {
        router.push(redirectUrl || '/dashboard');
      }, 400);
    } catch (err: any) {
      setError(err.message || 'Authentication failed. Please verify credentials.');
      setLoggingInUsername(null);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handlePersonaSelect = (seedUser: SeedUser) => {
    // Evaluation-only helper. This handler is reachable only when the
    // evaluation hub is rendered (non-production builds).
    setUsername(seedUser.username);
    setPassword(defaultSeedPassword);
    handleLogin(undefined, seedUser.username, defaultSeedPassword);
  };

  const handleCopyUsername = (uname: string, e: React.MouseEvent) => {
    e.stopPropagation();
    navigator.clipboard.writeText(uname);
    setCopiedUser(uname);
    setTimeout(() => setCopiedUser(null), 2000);
  };

  const filteredPersonas = useMemo(() => {
    if (selectedCpseTab === 'ALL') return seedUsers;
    if (selectedCpseTab === 'ADMIN') {
      return seedUsers.filter((u) => u.role === 'SUPER_ADMIN');
    }
    return seedUsers.filter((u) => u.cpse === selectedCpseTab);
  }, [seedUsers, selectedCpseTab]);

  const getRoleBadge = (role: string) => {
    switch (role) {
      case 'SITE_ENGINEER':
        return {
          label: 'Site Engineer',
          className: 'bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-500/20',
        };
      case 'MATERIALS_MANAGER':
        return {
          label: 'Materials Manager',
          className: 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/20',
        };
      case 'CISF_SECURITY':
        return {
          label: 'CISF Security',
          className: 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20',
        };
      case 'AUDITOR':
      case 'VIGILANCE_AUDITOR':
        return {
          label: 'Central Auditor',
          className: 'bg-purple-500/10 text-purple-600 dark:text-purple-400 border-purple-500/20',
        };
      case 'SUPER_ADMIN':
        return {
          label: 'Super Admin',
          className: 'bg-zinc-900 text-white dark:bg-zinc-100 dark:text-zinc-900 border-zinc-700',
        };
      default:
        return {
          label: role,
          className: 'bg-zinc-100 text-zinc-700 border-zinc-200',
        };
    }
  };

  return (
    <div className="max-w-7xl mx-auto py-6 px-4 space-y-6">
      {/* Top Banner */}
      <div className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-xl p-5 shadow-xs">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center gap-3.5">
            <div className="w-11 h-11 rounded-lg bg-emerald-600 flex items-center justify-center font-bold text-white shadow-xs">
              <Shield className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2 flex-wrap">
                <h1 className="text-base font-bold tracking-tight text-zinc-900 dark:text-white">
                  Samanvay-AI Sovereign Access Gateway
                </h1>
                <span className="px-2 py-0.5 text-[10px] font-mono font-semibold uppercase bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 rounded border border-emerald-500/20">
                  Multi-Tenant RBAC Active
                </span>
              </div>
              <p className="text-xs text-zinc-500 dark:text-zinc-400 mt-0.5 font-mono">
                Ministry of Petroleum & Natural Gas (MoPNG) · 7 CPSE Enterprise Mesh & Sovereign Identity
              </p>
            </div>
          </div>

          {user && (
            <div className="flex items-center gap-2.5 p-2 bg-emerald-500/10 border border-emerald-500/20 rounded-lg text-xs">
              <UserCheck className="w-4 h-4 text-emerald-600 dark:text-emerald-400 shrink-0" />
              <div>
                <p className="font-semibold text-emerald-800 dark:text-emerald-300">
                  Logged In: <span className="font-mono">{user.username}</span> ({user.cpse || 'Central'})
                </p>
                <p className="text-[10px] text-zinc-500 dark:text-zinc-400">
                  Role: {user.role} · {user.depot_id || 'Global'}
                </p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Main Grid: standard credentials first in production; the evaluation
          persona hub renders only in non-production builds. */}
      <div className={`grid grid-cols-1 gap-6 items-start ${showEvaluationHub ? 'lg:grid-cols-12' : 'lg:grid-cols-1 max-w-2xl mx-auto w-full'}`}>
        {showEvaluationHub && (
        <>
        {/* Left Column: 1-Click Evaluation Personas Hub (7 cols) */}
        <div className="lg:col-span-7 space-y-4">
          <div className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-xl p-5 shadow-xs">
            <div className="flex items-center justify-between gap-2 mb-3">
              <div className="flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-amber-500" />
                <h2 className="text-sm font-bold text-zinc-900 dark:text-white">
                  Judge & Evaluation Personas (1-Click Login)
                </h2>
              </div>
              <span className="text-[11px] font-mono text-zinc-400">
                Password: <code className="text-emerald-600 dark:text-emerald-400 font-semibold">{defaultSeedPassword}</code>
              </span>
            </div>

            <p className="text-xs text-zinc-500 dark:text-zinc-400 mb-4 leading-relaxed font-sans">
              Select any pre-configured persona across the 7 CPSEs (OIL, IOCL, ONGC, BPCL, HPCL, GAIL, NRL), Central MoPNG Vigilance Auditor, or Super Admin to test tenant isolation and segregation of duties.
            </p>

            {/* CPSE Tabs */}
            <div className="flex items-center gap-1.5 overflow-x-auto pb-2 scrollbar-none border-b border-zinc-100 dark:border-zinc-800 mb-4">
              {CPSE_TABS.map((tab) => (
                <button
                  key={tab}
                  onClick={() => setSelectedCpseTab(tab)}
                  className={`px-2.5 py-1 rounded text-xs font-mono font-medium shrink-0 transition-colors ${
                    selectedCpseTab === tab
                      ? 'bg-zinc-900 text-white dark:bg-zinc-100 dark:text-zinc-900 shadow-2xs'
                      : 'bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-400 hover:bg-zinc-200 dark:hover:bg-zinc-700'
                  }`}
                >
                  {tab}
                </button>
              ))}
            </div>

            {/* Persona Cards Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 max-h-[460px] overflow-y-auto pr-1">
              {filteredPersonas.map((persona) => {
                const badge = getRoleBadge(persona.role);
                const isCurrentLoggingIn = loggingInUsername === persona.username;

                return (
                  <div
                    key={persona.username}
                    onClick={() => handlePersonaSelect(persona)}
                    className="p-3 rounded-lg border border-zinc-200 dark:border-zinc-800 hover:border-zinc-400 dark:hover:border-zinc-600 bg-zinc-50/50 dark:bg-zinc-800/40 hover:bg-zinc-100/70 dark:hover:bg-zinc-800 transition-all cursor-pointer flex flex-col justify-between group"
                  >
                    <div>
                      <div className="flex items-center justify-between gap-1 mb-1.5">
                        <span className={`px-1.5 py-0.5 rounded text-[10px] font-mono border ${badge.className}`}>
                          {badge.label}
                        </span>
                        <div className="flex items-center gap-1">
                          <span className="text-[10px] font-mono font-bold text-zinc-700 dark:text-zinc-300">
                            {persona.cpse || 'CENTRAL'}
                          </span>
                          <button
                            onClick={(e) => handleCopyUsername(persona.username, e)}
                            className="p-1 text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-200 rounded"
                            title="Copy username"
                          >
                            <Copy size={11} />
                          </button>
                        </div>
                      </div>

                      <div className="font-semibold text-xs text-zinc-900 dark:text-zinc-100 truncate">
                        {persona.full_name}
                      </div>

                      <div className="text-[11px] font-mono text-zinc-500 dark:text-zinc-400 truncate mt-0.5">
                        @{persona.username}
                      </div>

                      <div className="text-[10px] text-zinc-400 truncate mt-1">
                        Depot: {persona.depot_id || 'Central Headquarters'}
                      </div>
                    </div>

                    <div className="mt-3 pt-2 border-t border-zinc-200/60 dark:border-zinc-750 flex items-center justify-between text-[11px]">
                      <span className="text-zinc-400 text-[10px] font-sans">
                        {copiedUser === persona.username ? 'Copied!' : 'Click to Login'}
                      </span>
                      <button
                        type="button"
                        disabled={isSubmitting}
                        className="px-2 py-0.5 bg-zinc-900 hover:bg-zinc-800 text-white dark:bg-zinc-100 dark:hover:bg-zinc-200 dark:text-zinc-900 rounded text-[10px] font-medium transition-colors flex items-center gap-1"
                      >
                        {isCurrentLoggingIn ? (
                          <span>Connecting...</span>
                        ) : (
                          <>
                            <span>1-Click</span>
                            <ChevronRight size={11} />
                          </>
                        )}
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Evaluation Workflow Guide Card */}
            <div className="mt-4 p-3 bg-zinc-100/80 dark:bg-zinc-800/60 border border-zinc-200 dark:border-zinc-750 rounded-lg text-xs space-y-1.5">
              <div className="flex items-center gap-1.5 font-semibold text-zinc-800 dark:text-zinc-200">
                <Info size={13} className="text-emerald-500" />
                <span>Recommended Evaluation Journey for Hackathon Judges:</span>
              </div>
              <ol className="list-decimal list-inside space-y-1 text-[11px] text-zinc-600 dark:text-zinc-400 font-mono">
                <li>
                  <strong className="text-zinc-800 dark:text-zinc-200">Step 1:</strong> Log in as <code className="text-blue-600 dark:text-blue-400">engineer_iocl</code> ➔ Discover ONGC valves & request 5 units.
                </li>
                <li>
                  <strong className="text-zinc-800 dark:text-zinc-200">Step 2:</strong> Notice that <code className="text-blue-600 dark:text-blue-400">engineer_iocl</code> cannot approve their own requisition (Segregation of Duties).
                </li>
                <li>
                  <strong className="text-zinc-800 dark:text-zinc-200">Step 3:</strong> Switch to <code className="text-amber-600 dark:text-amber-400">stores_ongc</code> (ONGC Materials Manager) ➔ Consignments tab ➔ Approve requisition.
                </li>
                <li>
                  <strong className="text-zinc-800 dark:text-zinc-200">Step 4:</strong> Switch to <code className="text-emerald-600 dark:text-emerald-400">cisf_ongc</code> (CISF Security Officer) ➔ Issue Non-Returnable Gate Pass with SHA-256 seal & SVG QR.
                </li>
                <li>
                  <strong className="text-zinc-800 dark:text-zinc-200">Step 5:</strong> Switch to <code className="text-purple-600 dark:text-purple-400">auditor_mopng</code> or <code className="text-zinc-800 dark:text-zinc-200">admin</code> ➔ Sovereign Audit Ledger to verify cryptographic hash chain.
                </li>
              </ol>
            </div>
          </div>
        </div>

        {/* Right Column: Standard Credentials Login Form (5 cols) */}
        <div className="lg:col-span-5 space-y-4">
          <div className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-xl p-5 shadow-xs">
            <div className="flex items-center gap-2 mb-4 pb-3 border-b border-zinc-100 dark:border-zinc-800">
              <KeyRound className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
              <h2 className="text-sm font-bold text-zinc-900 dark:text-white">
                Standard Credentials Login
              </h2>
            </div>

            {error && (
              <div className="mb-4 p-3 bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800 rounded-lg flex items-start gap-2.5 text-xs text-rose-800 dark:text-rose-200">
                <AlertCircle className="w-4 h-4 text-rose-600 dark:text-rose-400 shrink-0 mt-0.5" />
                <span>{error}</span>
              </div>
            )}

            {successMsg && (
              <div className="mb-4 p-3 bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 rounded-lg flex items-start gap-2.5 text-xs text-emerald-800 dark:text-emerald-200">
                <CheckCircle2 className="w-4 h-4 text-emerald-600 dark:text-emerald-400 shrink-0 mt-0.5" />
                <span>{successMsg}</span>
              </div>
            )}

            <form onSubmit={(e) => handleLogin(e)} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-zinc-700 dark:text-zinc-300 mb-1">
                  CPSE Username or Email
                </label>
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="e.g. engineer_oil, stores_ongc, or admin"
                  className="w-full px-3 py-2 text-xs bg-zinc-50 dark:bg-zinc-800/80 border border-zinc-300 dark:border-zinc-700 rounded-lg focus:outline-hidden focus:ring-2 focus:ring-emerald-500 text-zinc-900 dark:text-white font-mono"
                  disabled={isSubmitting}
                  required
                />
              </div>

              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="block text-xs font-semibold text-zinc-700 dark:text-zinc-300">
                    Password
                  </label>
                  <span className="text-[11px] text-zinc-400 font-mono">
                    Default: {defaultSeedPassword}
                  </span>
                </div>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter account password"
                  className="w-full px-3 py-2 text-xs bg-zinc-50 dark:bg-zinc-800/80 border border-zinc-300 dark:border-zinc-700 rounded-lg focus:outline-hidden focus:ring-2 focus:ring-emerald-500 text-zinc-900 dark:text-white"
                  disabled={isSubmitting}
                  required
                />
              </div>

              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full py-2.5 px-4 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-xs transition-colors flex items-center justify-center gap-2 shadow-xs disabled:opacity-50 cursor-pointer"
              >
                {isSubmitting ? (
                  <span>Authenticating Identity...</span>
                ) : (
                  <>
                    <Lock className="w-3.5 h-3.5" />
                    <span>Sign In to Sovereign Node</span>
                  </>
                )}
              </button>
            </form>

            <div className="mt-4 pt-3 border-t border-zinc-100 dark:border-zinc-800 text-center text-xs text-zinc-600 dark:text-zinc-400 flex items-center justify-between">
              <span>New CPSE Officer?</span>
              {showEvaluationHub && (
                <Link
                  href="/signup"
                  className="text-emerald-600 dark:text-emerald-400 font-semibold hover:underline flex items-center gap-1"
                >
                  <span>Register Account</span>
                  <ArrowRight className="w-3 h-3" />
                </Link>
              )}
            </div>

            <div className="mt-4 pt-3 border-t border-zinc-100 dark:border-zinc-800 space-y-2 text-[11px] text-zinc-500 dark:text-zinc-400">
              <p className="font-semibold text-zinc-700 dark:text-zinc-300">
                Tenant Isolation Guarantee:
              </p>
              <p className="leading-relaxed font-sans">
                Each CPSE officer is bounded to their authorized tenant and depot. Non-admin users cannot alter cross-tenant parameters. All requests, approvals, and gate passes are recorded in the SHA-256 audit ledger.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
