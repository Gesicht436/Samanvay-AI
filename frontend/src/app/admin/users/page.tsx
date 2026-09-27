'use client';

import React, { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { User } from '@/lib/types';
import { Check, X, ShieldAlert, ShieldCheck, RefreshCw } from 'lucide-react';
import { useAuth } from '@/context/AuthContext';
import { ProtectedRoute } from '@/components/ProtectedRoute';
import { Skeleton } from '@/components/ui';

export default function AdminUsersPage() {
  const { user } = useAuth();
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      const data = await api.getUsers();
      setUsers(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (userId: number) => {
    try {
      await api.approveUser(userId);
      fetchUsers();
    } catch (err) {
      console.error(err);
    }
  };

  const handleReject = async (userId: number) => {
    try {
      await api.rejectUser(userId);
      fetchUsers();
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <ProtectedRoute allowedRoles={['SUPER_ADMIN']}>
      <div className="space-y-4 max-w-7xl mx-auto pb-10">
        {/* Header */}
        <div className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-lg p-4 transition-colors">
          <div className="flex items-center justify-between">
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-sm font-semibold text-zinc-900 dark:text-zinc-100 font-sans">
                  Sovereign Identity & User Authorizations
                </h1>
                <span className="px-1.5 py-0.2 text-[10px] font-mono text-zinc-500 bg-zinc-100 dark:bg-zinc-800 rounded border border-zinc-200 dark:border-zinc-750">
                  Admin Authority
                </span>
              </div>
              <p className="text-xs text-zinc-500 dark:text-zinc-400 font-mono mt-0.5">
                Review officer registrations and grant node-level permissions across CPSEs.
              </p>
            </div>

            <button
              onClick={fetchUsers}
              disabled={loading}
              className="p-1.5 bg-zinc-100 dark:bg-zinc-800 hover:bg-zinc-200 dark:hover:bg-zinc-750 text-zinc-700 dark:text-zinc-300 rounded-md transition-colors"
              title="Refresh users"
            >
              <RefreshCw size={13} className={loading ? 'animate-spin' : ''} />
            </button>
          </div>
        </div>

        {/* Users Table */}
        <div className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-lg overflow-hidden shadow-2xs">
          <div className="overflow-x-auto">
            <table className="w-full text-left compact-table border-collapse">
              <thead>
                <tr className="border-b border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-900/80">
                  <th>Officer Name</th>
                  <th>Role</th>
                  <th>CPSE & Depot</th>
                  <th>Status</th>
                  <th className="text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-100 dark:divide-zinc-800/80 text-xs font-mono">
                {loading ? (
                  Array.from({ length: 4 }).map((_, i) => (
                    <tr key={i} className="h-[38px]">
                      <td><Skeleton className="h-4 w-32" /></td>
                      <td><Skeleton className="h-4 w-28" /></td>
                      <td><Skeleton className="h-4 w-24" /></td>
                      <td><Skeleton className="h-4 w-16" /></td>
                      <td className="text-right"><Skeleton className="h-4 w-16 ml-auto" /></td>
                    </tr>
                  ))
                ) : users.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="py-10 text-center text-zinc-400 font-mono text-xs">
                      No user registrations found.
                    </td>
                  </tr>
                ) : (
                  users.map((u) => (
                    <tr key={u.id} className="hover:bg-zinc-50 dark:hover:bg-zinc-800/50 transition-colors">
                      <td className="py-2">
                        <div className="font-semibold text-zinc-900 dark:text-zinc-100 font-sans text-xs">
                          {u.full_name}
                        </div>
                        <div className="text-[10px] text-zinc-400 font-mono">@{u.username}</div>
                      </td>

                      <td className="text-zinc-700 dark:text-zinc-300">
                        {u.role.replace('_', ' ')}
                      </td>

                      <td className="text-zinc-600 dark:text-zinc-400">
                        {u.cpse} · {u.depot_id}
                      </td>

                      <td>
                        {u.is_approved ? (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 text-[10px] font-mono rounded-full bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
                            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                            <span>Approved</span>
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 text-[10px] font-mono rounded-full bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20">
                            <span className="w-1.5 h-1.5 rounded-full bg-amber-500" />
                            <span>Pending</span>
                          </span>
                        )}
                      </td>

                      <td className="text-right">
                        {!u.is_approved ? (
                          <div className="flex items-center justify-end gap-1.5">
                            <button
                              onClick={() => handleApprove(u.id)}
                              className="px-2 py-1 bg-zinc-900 hover:bg-zinc-800 text-white dark:bg-zinc-100 dark:hover:bg-zinc-200 dark:text-zinc-900 rounded text-[11px] font-medium transition-colors"
                              title="Approve User"
                            >
                              Approve
                            </button>
                            <button
                              onClick={() => handleReject(u.id)}
                              className="px-2 py-1 border border-zinc-200 dark:border-zinc-700 hover:bg-rose-500/10 hover:text-rose-600 rounded text-[11px] font-medium transition-colors"
                              title="Reject User"
                            >
                              Reject
                            </button>
                          </div>
                        ) : (
                          <span className="text-[11px] text-zinc-400">Active</span>
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </ProtectedRoute>
  );
}
