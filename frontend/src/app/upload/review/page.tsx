"use client";
import React, { useState } from 'react';
import { Card } from '@/components/ui';
import { Check, X, AlertTriangle } from 'lucide-react';
import { useRouter } from 'next/navigation';

export default function ReviewPage() {
  const router = useRouter();
  const [status, setStatus] = useState('IN_STORAGE');

  return (
    <div className="flex h-full gap-6">
      {/* Left Pane - Document Preview */}
      <Card className="w-1/2 flex flex-col p-0 overflow-hidden">
        <div className="p-4 border-b border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900">
          <h3 className="font-mono font-semibold">MTC-2023-894.pdf</h3>
        </div>
        <div className="flex-1 p-8 bg-gray-300 dark:bg-gray-800 flex items-center justify-center">
          <span className="text-gray-500 font-mono">[PDF VIEWER RENDER]</span>
        </div>
      </Card>

      {/* Right Pane - Extraction & Verification */}
      <Card className="w-1/2 flex flex-col overflow-y-auto">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-bold">Extraction Review</h2>
          <span className="px-2 py-1 bg-emerald-100 text-emerald-800 text-xs font-semibold rounded font-mono">
            CONFIDENCE: 98.4%
          </span>
        </div>

        <div className="space-y-6 flex-1">
          <div>
            <h4 className="text-sm font-semibold text-slate-500 uppercase mb-2">Material Specs</h4>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-xs text-slate-500">Standard</label>
                <input type="text" defaultValue="ASTM A105" className="w-full p-2 border rounded text-sm font-mono mt-1" />
              </div>
              <div>
                <label className="text-xs text-slate-500">Type</label>
                <input type="text" defaultValue="Carbon Steel Flange" className="w-full p-2 border rounded text-sm font-mono mt-1" />
              </div>
            </div>
          </div>

          <div>
            <h4 className="text-sm font-semibold text-slate-500 uppercase mb-2 flex justify-between items-center">
              Chemistry Validation
              <span className="text-emerald-600 text-xs flex items-center gap-1"><Check size={14}/> ASME B16.5 PASS</span>
            </h4>
            <table className="w-full text-sm compact-table border">
              <thead className="bg-slate-50 dark:bg-slate-800 border-b">
                <tr>
                  <th className="text-left">Element</th>
                  <th className="text-right">Value (%)</th>
                  <th className="text-right">Required (%)</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td className="font-mono">Carbon (C)</td>
                  <td className="text-right font-mono">0.24</td>
                  <td className="text-right font-mono text-slate-500">≤ 0.35</td>
                </tr>
                <tr>
                  <td className="font-mono">Manganese (Mn)</td>
                  <td className="text-right font-mono">0.95</td>
                  <td className="text-right font-mono text-slate-500">0.60-1.05</td>
                </tr>
              </tbody>
            </table>
          </div>
          
          <div>
            <h4 className="text-sm font-semibold text-slate-500 uppercase mb-2">Initial Status</h4>
            <select 
              value={status}
              onChange={e => setStatus(e.target.value)}
              className="w-full p-2 border rounded text-sm font-mono"
            >
              <option value="IN_STORAGE">IN_STORAGE (Reserved)</option>
              <option value="IDLE_SURPLUS">IDLE_SURPLUS (Broadcast)</option>
              <option value="TO_BE_CONSUMED">TO_BE_CONSUMED</option>
            </select>
          </div>
        </div>

        <div className="pt-6 border-t mt-6 flex justify-end gap-3 sticky bottom-0 bg-white dark:bg-slate-800">
          <button className="px-4 py-2 border rounded font-semibold text-slate-600">Reject</button>
          <button 
            onClick={() => router.push('/inventory')}
            className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded font-semibold flex items-center gap-2"
          >
            <Check size={16} /> Commit to Ledger
          </button>
        </div>
      </Card>
    </div>
  );
}
