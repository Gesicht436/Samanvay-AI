"use client";
import React, { useState } from 'react';
import { Card, StatusBadge } from '@/components/ui';

export default function InventoryPage() {
  const [activeTab, setActiveTab] = useState('ALL');

  const tabs = [
    { id: 'ALL', label: 'All Inventory Stock' },
    { id: 'SURPLUS', label: 'Broadcasted Surplus' },
    { id: 'HITL', label: 'HITL Triage Queue' },
    { id: 'ARCHIVED', label: 'Consumed / Archived' },
  ];

  return (
    <div className="flex flex-col h-full space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold font-mono">Plant Stock Ledger</h1>
      </div>

      <div className="flex gap-4 border-b border-slate-200 dark:border-slate-800">
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-2 text-sm font-semibold border-b-2 transition-colors ${
              activeTab === tab.id 
                ? 'border-emerald-500 text-emerald-600 dark:text-emerald-400' 
                : 'border-transparent text-slate-500 hover:text-slate-800 dark:hover:text-slate-300'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <Card className="flex-1 overflow-hidden flex flex-col p-0">
        {activeTab === 'HITL' ? (
          <div className="p-6 flex flex-col items-center">
            <h3 className="text-lg font-bold mb-4">Borderline Matches (80-94%)</h3>
            <p className="text-sm text-slate-500 mb-8">Review algorithmic predictions requiring human sign-off.</p>
            {/* Diff UI */}
            <div className="flex gap-8 w-full max-w-4xl mb-12">
              <div className="flex-1 border rounded p-4">
                <h4 className="font-bold text-slate-700">Physical Part</h4>
                <pre className="mt-4 text-xs font-mono text-slate-600">Material: CS A105\nRating: 300#</pre>
              </div>
              <div className="flex-1 border rounded p-4 border-amber-300 bg-amber-50">
                <h4 className="font-bold text-amber-800">Extracted MTC</h4>
                <pre className="mt-4 text-xs font-mono text-amber-700">Material: CS A105N\nRating: 300#</pre>
              </div>
            </div>
            
            <div className="mt-auto flex gap-4 w-full justify-center">
              <button className="px-6 py-2 border rounded font-bold text-rose-600 border-rose-200 hover:bg-rose-50">Reject Prediction</button>
              <button className="px-6 py-2 bg-emerald-600 text-white rounded font-bold hover:bg-emerald-700">Approve & Merge</button>
            </div>
          </div>
        ) : (
          <div className="overflow-auto">
            <table className="w-full text-left compact-table border-collapse">
              <thead className="bg-slate-100 dark:bg-slate-800 sticky top-0">
                <tr>
                  <th>Part ID</th>
                  <th>Description</th>
                  <th>Quantity</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
                <tr className="hover:bg-slate-50 dark:hover:bg-slate-800/50">
                  <td className="font-mono text-xs">PRT-8892</td>
                  <td>ASTM A105 WN Flange 4" 300#</td>
                  <td className="font-mono">12 EA</td>
                  <td><span className="px-2 py-0.5 text-xs bg-emerald-100 text-emerald-800 rounded">IDLE_SURPLUS</span></td>
                </tr>
                <tr className="hover:bg-slate-50 dark:hover:bg-slate-800/50">
                  <td className="font-mono text-xs">PRT-8893</td>
                  <td>SS316 Globe Valve 2"</td>
                  <td className="font-mono">4 EA</td>
                  <td><span className="px-2 py-0.5 text-xs bg-slate-100 text-slate-800 rounded">IN_STORAGE</span></td>
                </tr>
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}
