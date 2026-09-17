"use client";
import React from 'react';
import { Card } from '@/components/ui';
import Link from 'next/link';
import { ArrowRight, CheckCircle2, XCircle } from 'lucide-react';

export default function RequestsPage() {
  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold font-mono">Requisition Hub</h1>
      
      <div className="grid grid-cols-2 gap-6">
        <div>
          <h2 className="text-lg font-semibold mb-4 text-slate-700">Inbound Requests (To Supply)</h2>
          <Card className="p-0 overflow-hidden border-l-4 border-l-amber-500">
            <div className="p-4 bg-slate-50 border-b flex justify-between items-center">
              <span className="font-mono text-sm font-bold">REQ-99201</span>
              <span className="text-xs text-slate-500">2 hours ago</span>
            </div>
            <div className="p-4">
              <p className="font-semibold mb-1">From: ONGC Uran Plant</p>
              <p className="text-sm text-slate-600 mb-4">Requesting 2x CS A105 Flanges (Emergency Breakdown)</p>
              <div className="flex gap-2">
                <button className="flex-1 py-1.5 bg-emerald-600 text-white rounded text-sm font-semibold flex items-center justify-center gap-1 hover:bg-emerald-700">
                  <CheckCircle2 size={16}/> Confirm Supply
                </button>
                <button className="px-3 py-1.5 border rounded text-sm text-rose-600 hover:bg-rose-50 flex items-center justify-center gap-1">
                  <XCircle size={16}/> Decline
                </button>
              </div>
            </div>
          </Card>
        </div>

        <div>
          <h2 className="text-lg font-semibold mb-4 text-slate-700">Active Consignments</h2>
          <Card className="hover:shadow-md transition-shadow cursor-pointer p-0" >
            <Link href="/requests/REQ-55102" className="block p-4">
              <div className="flex justify-between items-center mb-2">
                <span className="font-mono font-bold">REQ-55102</span>
                <span className="px-2 py-0.5 text-xs bg-blue-100 text-blue-800 rounded font-semibold">IN TRANSIT</span>
              </div>
              <p className="text-sm font-semibold">To: HPCL Visakh</p>
              <p className="text-xs text-slate-500 mb-3">1x Gas Turbine Rotor</p>
              <div className="w-full bg-slate-200 h-1.5 rounded-full overflow-hidden">
                <div className="bg-blue-500 h-full w-2/3"></div>
              </div>
              <div className="flex justify-between mt-1 text-[10px] text-slate-400 font-mono">
                <span>Dispatched</span>
                <span>Expected Tomorrow</span>
              </div>
            </Link>
          </Card>
        </div>
      </div>
    </div>
  );
}
