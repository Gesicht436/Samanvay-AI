'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import {
  Shield,
  UserPlus,
  Building2,
  Lock,
  Mail,
  User,
  AlertCircle,
  CheckCircle2,
  ArrowRight,
  Briefcase,
  MapPin,
} from 'lucide-react';

const CPSE_DEPOTS: Record<string, { name: string; depots: Array<{ id: string; name: string }> }> = {
  OIL: {
    name: 'Oil India Limited',
    depots: [
      { id: 'DEPOT-OIL-DLJ', name: 'Duliajan Field HQ (Assam)' },
      { id: 'DEPOT-OIL-MRN', name: 'Moran Petroleum Depot (Assam)' },
      { id: 'DEPOT-OIL-RAJ', name: 'Rajasthan Project (Jaisalmer)' },
    ],
  },
  IOCL: {
    name: 'Indian Oil Corporation',
    depots: [
      { id: 'DEPOT-IOCL-PNP', name: 'Panipat Refinery (Haryana)' },
      { id: 'DEPOT-IOCL-GHY', name: 'Guwahati Refinery (Noonmati)' },
      { id: 'DEPOT-IOCL-KOL', name: 'Haldia Refinery (West Bengal)' },
      { id: 'DEPOT-IOCL-MTH', name: 'Mathura Refinery (Uttar Pradesh)' },
    ],
  },
  ONGC: {
    name: 'Oil & Natural Gas Corporation',
    depots: [
      { id: 'DEPOT-ONGC-ANK', name: 'Ankleshwar Asset (Gujarat)' },
      { id: 'DEPOT-ONGC-NZR', name: 'Nazira Asset (Assam)' },
      { id: 'DEPOT-ONGC-MUM', name: 'Mumbai Offshore Base (Maharashtra)' },
    ],
  },
  BPCL: {
    name: 'Bharat Petroleum',
    depots: [
      { id: 'DEPOT-BPCL-MUM', name: 'Mumbai Refinery (Mahul)' },
      { id: 'DEPOT-BPCL-KOC', name: 'Kochi Refinery (Ambalamugal)' },
    ],
  },
  HPCL: {
    name: 'Hindustan Petroleum',
    depots: [
      { id: 'DEPOT-HPCL-MUM', name: 'Mumbai Refinery (Chembur)' },
      { id: 'DEPOT-HPCL-VSK', name: 'Visakh Refinery (Andhra Pradesh)' },
    ],
  },
  GAIL: {
    name: 'GAIL (India) Limited',
    depots: [
      { id: 'DEPOT-GAIL-PAT', name: 'Pata Petrochemical Complex (UP)' },
      { id: 'DEPOT-GAIL-VIJ', name: 'Vijaipur Compressor Station (MP)' },
    ],
  },
  NRL: {
    name: 'Numaligarh Refinery Limited',
    depots: [
      { id: 'DEPOT-NRL-NMR', name: 'Numaligarh Refinery (Golaghat, Assam)' },
    ],
  },
};

const ROLES = [
  {
    id: 'SITE_ENGINEER',
    name: 'Site Maintenance & Plant Engineer',
    desc: 'Surplus spare discovery, 21-gate safety veto verification, and loan requisitions.',
  },
  {
    id: 'MATERIALS_MANAGER',
    name: 'Materials Manager / Stores In-Charge',
    desc: 'Stock ledger surplus mobilization, idle countdown tracking, and loan authorization.',
  },
  {
    id: 'TECHNICAL_AUTHORITY',
    name: 'QA-QC Technical Authority / Metallurgist',
    desc: 'HITL 80%–94% tolerance arbitration, ASTM ladle chemistry, and CE weldability.',
  },
  {
    id: 'CISF_SECURITY',
    name: 'CISF Perimeter Security Inspector',
    desc: 'Air-gapped QR digital gate pass scanning and physical consignment stamping.',
  },
  {
    id: 'VIGILANCE_AUDITOR',
    name: 'Chief Vigilance Officer / Statutory Auditor',
    desc: 'SHA-256 Merkle audit trail verification and CAG reporting.',
  },
];

export default function SignupPage() {
  const router = useRouter();
  const { signup } = useAuth();

  const [cpse, setCpse] = useState<string>('OIL');
  const [depotId, setDepotId] = useState<string>('DEPOT-OIL-DLJ');
  const [role, setRole] = useState<string>('SITE_ENGINEER');
  const [fullName, setFullName] = useState<string>('');
  const [email, setEmail] = useState<string>('');
  const [username, setUsername] = useState<string>('');
  const [password, setPassword] = useState<string>('');
  const [confirmPassword, setConfirmPassword] = useState<string>('');

  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState<boolean>(false);

  const handleCpseChange = (newCpse: string) => {
    setCpse(newCpse);
    const available = CPSE_DEPOTS[newCpse]?.depots;
    if (available && available.length > 0) {
      setDepotId(available[0].id);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);

    if (password !== confirmPassword) {
      setError('Passwords do not match. Please verify.');
      return;
    }

    if (password.length < 6) {
      setError('Password must be at least 6 characters.');
      return;
    }

    setSubmitting(true);
    try {
      const newUser = await signup({
        username: username.trim(),
        password,
        full_name: fullName.trim(),
        email: email.trim(),
        role,
        cpse,
        depot_id: depotId,
      });

      setSuccess(`Account registered successfully! Welcome, ${newUser.full_name}.`);
      setTimeout(() => {
        router.push('/dashboard');
      }, 700);
    } catch (err: any) {
      setError(err.message || 'Registration failed. Please check your inputs.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto py-10 px-4">
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-6 sm:p-8 shadow-xs">
        {/* Header */}
        <div className="flex items-center gap-3.5 pb-6 border-b border-slate-100 dark:border-slate-800">
          <div className="w-12 h-12 rounded-xl bg-emerald-600 flex items-center justify-center font-bold text-white shadow-xs">
            <UserPlus className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-slate-900 dark:text-white">
              CPSE Personnel Registration
            </h1>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              Enroll into the Ministry of Petroleum & Natural Gas Sovereign Mutual Aid Mesh
            </p>
          </div>
        </div>

        {error && (
          <div className="mt-5 p-3.5 bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800 rounded-lg flex items-start gap-2.5 text-xs text-rose-800 dark:text-rose-200">
            <AlertCircle className="w-4 h-4 text-rose-600 dark:text-rose-400 shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        {success && (
          <div className="mt-5 p-3.5 bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 rounded-lg flex items-start gap-2.5 text-xs text-emerald-800 dark:text-emerald-200">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 dark:text-emerald-400 shrink-0 mt-0.5" />
            <span>{success}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="mt-6 space-y-5">
          {/* Organization & Depot */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                CPSE Organization
              </label>
              <div className="relative">
                <select
                  value={cpse}
                  onChange={(e) => handleCpseChange(e.target.value)}
                  className="w-full px-3 py-2 text-xs bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-lg text-slate-900 dark:text-white focus:ring-2 focus:ring-emerald-500"
                >
                  {Object.keys(CPSE_DEPOTS).map((code) => (
                    <option key={code} value={code}>
                      {code} &mdash; {CPSE_DEPOTS[code].name}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                Assigned Depot / Refinery
              </label>
              <select
                value={depotId}
                onChange={(e) => setDepotId(e.target.value)}
                className="w-full px-3 py-2 text-xs bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-lg text-slate-900 dark:text-white focus:ring-2 focus:ring-emerald-500"
              >
                {CPSE_DEPOTS[cpse]?.depots.map((dep) => (
                  <option key={dep.id} value={dep.id}>
                    {dep.name}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Functional Role */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
              Designated Functional Role
            </label>
            <select
              value={role}
              onChange={(e) => setRole(e.target.value)}
              className="w-full px-3 py-2 text-xs bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-lg text-slate-900 dark:text-white focus:ring-2 focus:ring-emerald-500"
            >
              {ROLES.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.name}
                </option>
              ))}
            </select>
            <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-1 font-mono">
              {ROLES.find((r) => r.id === role)?.desc}
            </p>
          </div>

          {/* Personal Info */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                Full Name & Rank
              </label>
              <input
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="e.g. Er. Pranjal Saikia"
                required
                className="w-full px-3 py-2 text-xs bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-lg text-slate-900 dark:text-white focus:ring-2 focus:ring-emerald-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                Official CPSE Email
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="e.g. pranjal.saikia@nrl.co.in"
                required
                className="w-full px-3 py-2 text-xs bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-lg text-slate-900 dark:text-white focus:ring-2 focus:ring-emerald-500"
              />
            </div>
          </div>

          {/* Credentials */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                Unique Username
              </label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="e.g. engineer_nrl"
                required
                className="w-full px-3 py-2 text-xs bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-lg text-slate-900 dark:text-white focus:ring-2 focus:ring-emerald-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                Password
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Min 6 characters"
                required
                className="w-full px-3 py-2 text-xs bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-lg text-slate-900 dark:text-white focus:ring-2 focus:ring-emerald-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                Confirm Password
              </label>
              <input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="Repeat password"
                required
                className="w-full px-3 py-2 text-xs bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-lg text-slate-900 dark:text-white focus:ring-2 focus:ring-emerald-500"
              />
            </div>
          </div>

          {/* Submit */}
          <button
            type="submit"
            disabled={submitting}
            className="w-full py-2.5 px-4 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-xs rounded-lg transition-colors shadow-xs flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
          >
            {submitting ? (
              <span>Registering Personnel in Sovereign Registry...</span>
            ) : (
              <>
                <UserPlus className="w-4 h-4" />
                <span>Complete Registration & Launch Workspace</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        </form>

        <div className="mt-6 pt-4 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-xs text-slate-500 dark:text-slate-400">
          <span>Already registered?</span>
          <Link
            href="/login"
            className="text-emerald-600 dark:text-emerald-400 font-semibold hover:underline"
          >
            Sign In with Existing Credentials &rarr;
          </Link>
        </div>
      </div>
    </div>
  );
}
