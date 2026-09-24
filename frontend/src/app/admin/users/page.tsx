'use client';

import React, { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { User } from '@/lib/types';
import { Check, X, ShieldAlert, ShieldCheck } from 'lucide-react';
import { useAuth } from '@/context/AuthContext';
import { ProtectedRoute } from '@/components/ProtectedRoute';

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

  if (loading) return <div className="p-8 font-mono text-sm">Loading users...</div>;

  return (
    <ProtectedRoute allowedRoles={['SUPER_ADMIN']}>
      <div className="p-8 max-w-6xl mx-auto space-y-6">
      <div className="flex items-center gap-3">
        <ShieldCheck className="w-8 h-8 text-emerald-600" />
        <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
          Sovereign Identity Management
        </h1>
      </div>
      <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden">
        <table className="w-full text-left text-sm">
          <thead className="bg-slate-50 dark:bg-slate-800/50 border-b border-slate-200 dark:border-slate-700">
            <tr>
              <th className="px-6 py-4 font-semibold text-slate-700 dark:text-slate-300">User</th>
              <th className="px-6 py-4 font-semibold text-slate-700 dark:text-slate-300">Role / CPSE</th>
              <th className="px-6 py-4 font-semibold text-slate-700 dark:text-slate-300">Status</th>
              <th className="px-6 py-4 font-semibold text-slate-700 dark:text-slate-300 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
            {users.map((u) => (
              <tr key={u.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/30 transition-colors">
                <td className="px-6 py-4">
                  <div className="font-medium text-slate-900 dark:text-white">{u.full_name}</div>
                  <div className="text-xs text-slate-500 font-mono">@{u.username}</div>
                </td>
                <td className="px-6 py-4">
                  <div className="font-semibold text-slate-700 dark:text-slate-300 text-xs">
                    {u.role.replace('_', ' ')}
                  </div>
                  <div className="text-xs text-slate-500">{u.cpse} · {u.depot_id}</div>
                </td>
                <td className="px-6 py-4">
                  {u.is_approved ? (
                    <span className="px-2.5 py-1 text-[10px] uppercase font-bold bg-emerald-100 text-emerald-800 dark:bg-emerald-900/50 dark:text-emerald-300 rounded border border-emerald-300 dark:border-emerald-700">
                      Approved
                    </span>
                  ) : (
                    <span className="px-2.5 py-1 text-[10px] uppercase font-bold bg-amber-100 text-amber-800 dark:bg-amber-900/50 dark:text-amber-300 rounded border border-amber-300 dark:border-amber-700">
                      Pending
                    </span>
                  )}
                </td>
                <td className="px-6 py-4 text-right">
                  {!u.is_approved && (
                    <div className="flex items-center justify-end gap-2">
                      <button
                        onClick={() => handleApprove(u.id)}
                        className="p-1.5 bg-emerald-100 hover:bg-emerald-200 text-emerald-700 rounded transition-colors"
                        title="Approve User"
                      >
                        <Check className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleReject(u.id)}
                        className="p-1.5 bg-rose-100 hover:bg-rose-200 text-rose-700 rounded transition-colors"
                        title="Reject & Delete"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {users.length === 0 && (
          <div className="p-8 text-center text-slate-500">No users found.</div>
        )}
      </div>
      </div>
    </ProtectedRoute>
  );
}
