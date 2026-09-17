"use client";
import React, { use } from 'react';
import { Card, Timeline } from '@/components/ui';
import { Printer, Truck } from 'lucide-react';

export default function ConsignmentTrackingPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);

  const events = [
    { date: '2023-10-25 09:00', title: 'Requisition Created', desc: 'HPCL requested part' },
    { date: '2023-10-25 11:30', title: 'Supply Confirmed', desc: 'IOCL approved release' },
    { date: '2023-10-26 14:00', title: 'Gate Pass Generated', desc: 'CISF clearance pending' },
  ];

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex items-center justify-between no-print">
        <h1 className="text-2xl font-bold font-mono">Consignment {id}</h1>
        <button 
          onClick={() => window.print()}
          className="px-4 py-2 bg-slate-900 text-white rounded flex items-center gap-2 hover:bg-slate-800"
        >
          <Printer size={18} /> Print CISF Gate Pass
        </button>
      </div>

      <div className="grid grid-cols-3 gap-6">
        <div className="col-span-2 space-y-6">
          {/* Printable Gate Pass Section */}
          <Card className="print-only border-black bg-white text-black p-8 shadow-none border-2">
            <div className="text-center border-b-2 border-black pb-4 mb-6">
              <h1 className="text-2xl font-bold uppercase tracking-widest">GATE PASS (NON-RETURNABLE)</h1>
              <p className="font-mono mt-2">Ministry of Petroleum & Natural Gas - Samanvay Network</p>
            </div>
            
            <div className="grid grid-cols-2 gap-8 font-mono text-sm mb-8">
              <div>
                <p className="text-gray-500 text-xs">DISPATCHING NODE</p>
                <p className="font-bold text-lg">IOCL Panipat</p>
              </div>
              <div>
                <p className="text-gray-500 text-xs">RECEIVING NODE</p>
                <p className="font-bold text-lg">HPCL Visakh</p>
              </div>
            </div>

            <table className="w-full mb-8 border-collapse border border-black">
              <thead>
                <tr className="border-b border-black text-left">
                  <th className="p-2 border-r border-black">Sl No.</th>
                  <th className="p-2 border-r border-black">Material Description</th>
                  <th className="p-2">Qty</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td className="p-2 border-r border-black text-center">1</td>
                  <td className="p-2 border-r border-black">Gas Turbine Rotor (PRT-5512)</td>
                  <td className="p-2 text-center">1 EA</td>
                </tr>
              </tbody>
            </table>

            <div className="flex justify-between items-end mt-16 pt-8 border-t border-dashed border-gray-400">
              <div className="text-center">
                <div className="w-32 h-16 border-b border-black mb-2"></div>
                <span className="text-xs font-bold uppercase">Authorized Signatory</span>
              </div>
              <div className="w-24 h-24 bg-gray-200 flex items-center justify-center border border-black">
                <span className="text-xs text-center text-gray-500">[SVG QR<br/>CODE]</span>
              </div>
            </div>
          </Card>

          <Card className="no-print">
            <h3 className="font-bold mb-4 flex items-center gap-2"><Truck size={18}/> Live Tracking</h3>
            <Timeline events={events} />
            <div className="mt-8 pt-4 border-t flex justify-end">
              <button className="px-4 py-2 bg-blue-600 text-white rounded font-bold">Mark as Dispatched</button>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
