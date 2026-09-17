"use client";
import React from 'react';
import { Card } from '@/components/ui';
import { ShieldCheck, Download } from 'lucide-react';
import { exportToCSV } from '@/lib/exportUtils';

export default function AuditPage() {
  const dummyLogs = [
    { id: 'ev-001', time: '2023-10-26T14:02:11Z', node: 'IOCL-PNP', action: 'STATUS_CHANGE', target: 'PRT-8892', user: 'system_ocr', hash: 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855' },
    { id: 'ev-002', time: '2023-10-26T14:15:00Z', node: 'BPCL-MUM', action: 'REQUISITION_CREATED', target: 'REQ-55102', user: 'admin_usr1', hash: '8a91a92120e290f6b4e7a83d739818817454f7a26f8d1eb1997d4fb526543b56' },
  ];

  const handleExport = () => {
    exportToCSV('samanvay_audit_ledger.csv', dummyLogs);
  };

  return (
    <div className="flex flex-col h-full space-y-6 max-w-6xl mx-auto">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold font-mono">Sovereign Audit Ledger</h1>
          <p className="text-sm text-slate-500">Immutable chronological event stream with SHA-256 seals</p>
        </div>
        <div className="flex gap-3">
          <button className="px-4 py-2 border rounded font-semibold flex items-center gap-2 hover:bg-slate-50 dark:hover:bg-slate-800">
            <ShieldCheck size={18} className="text-emerald-500" /> Verify Hashes
          </button>
          <button onClick={handleExport} className="px-4 py-2 bg-slate-900 text-white rounded font-semibold flex items-center gap-2 hover:bg-slate-800">
            <Download size={18} /> Export RFC 4180 CSV
          </button>
        </div>
      </div>

      <Card className="flex-1 overflow-auto p-0">
        <table className="w-full text-left compact-table">
          <thead className="bg-slate-100 dark:bg-slate-800 sticky top-0">
            <tr>
              <th>Timestamp (UTC)</th>
              <th>Node</th>
              <th>Action</th>
              <th>Target</th>
              <th>Actor</th>
              <th>SHA-256 Seal</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200 dark:divide-slate-700">
            {dummyLogs.map(log => (
              <tr key={log.id} className="hover:bg-slate-50 dark:hover:bg-slate-900 font-mono text-xs">
                <td className="whitespace-nowrap">{log.time}</td>
                <td>{log.node}</td>
                <td><span className="px-2 py-0.5 bg-slate-200 dark:bg-slate-700 rounded font-bold">{log.action}</span></td>
                <td>{log.target}</td>
                <td>{log.user}</td>
                <td className="truncate max-w-[200px] text-slate-400">{log.hash}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  );
}
