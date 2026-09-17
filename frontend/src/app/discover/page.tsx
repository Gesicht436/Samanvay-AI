"use client";
import React, { useState, useEffect } from 'react';
import { Card, StatusBadge } from '@/components/ui';
import { Search, Filter, ShoppingCart } from 'lucide-react';

export default function DiscoverPage() {
  const [search, setSearch] = useState('');

  // Handle Ctrl+K shortcut
  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === 'k' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        document.getElementById('global-search')?.focus();
      }
    }
    document.addEventListener('keydown', down);
    return () => document.removeEventListener('keydown', down);
  }, []);

  return (
    <div className="flex flex-col h-full space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold font-mono">Cross-CPSE Surplus Discovery</h1>
      </div>

      <div className="relative">
        <Search className="absolute left-3 top-2.5 text-slate-400" size={20} />
        <input 
          id="global-search"
          type="text" 
          value={search}
          onChange={e => setSearch(e.target.value)}
          placeholder="Search parts... (Ctrl+K)" 
          className="w-full pl-10 pr-4 py-2 border rounded-lg bg-white dark:bg-slate-900 focus:ring-2 ring-emerald-500 outline-none"
        />
      </div>

      <div className="flex gap-6 flex-1 overflow-hidden">
        {/* Sidebar Filters */}
        <div className="w-64 bg-white dark:bg-slate-800 p-4 border rounded-lg shrink-0 overflow-y-auto space-y-6">
          <div className="flex items-center gap-2 font-bold text-slate-700 dark:text-slate-300">
            <Filter size={18} /> Filters
          </div>
          
          <div>
            <h4 className="text-sm font-semibold mb-2">CPSE Node</h4>
            <label className="flex items-center gap-2 text-sm"><input type="checkbox" /> ONGC</label>
            <label className="flex items-center gap-2 text-sm"><input type="checkbox" /> IOCL</label>
            <label className="flex items-center gap-2 text-sm"><input type="checkbox" /> BPCL</label>
          </div>
          
          <div>
            <h4 className="text-sm font-semibold mb-2">Metallurgy</h4>
            <label className="flex items-center gap-2 text-sm"><input type="checkbox" /> Carbon Steel</label>
            <label className="flex items-center gap-2 text-sm"><input type="checkbox" /> Stainless Steel</label>
          </div>
        </div>

        {/* Results */}
        <div className="flex-1 overflow-auto">
          <div className="space-y-4">
            {/* Result Item */}
            <Card className="flex items-center justify-between hover:border-emerald-500 transition-colors">
              <div>
                <div className="flex items-center gap-3 mb-1">
                  <h3 className="font-bold">Gate Valve 6" 150# API 600</h3>
                  <StatusBadge tier={1} />
                </div>
                <p className="text-sm text-slate-500">Material: A216 WCB | Location: IOCL Panipat (320km)</p>
                <div className="mt-2 flex gap-2">
                  <span className="px-2 py-0.5 bg-slate-100 text-xs font-mono rounded border">PRICE HIDDEN</span>
                  <span className="text-xs text-slate-400 mt-0.5">Attribute-level privacy enforced</span>
                </div>
              </div>
              <button className="px-4 py-2 bg-slate-900 text-white rounded font-medium flex items-center gap-2 hover:bg-slate-800">
                <ShoppingCart size={16} /> Compose Requisition
              </button>
            </Card>

            <Card className="flex items-center justify-between hover:border-amber-500 transition-colors">
              <div>
                <div className="flex items-center gap-3 mb-1">
                  <h3 className="font-bold">Gate Valve 6" 300# API 600</h3>
                  <StatusBadge tier={2} />
                </div>
                <p className="text-sm text-slate-500">Material: A216 WCB | Location: BPCL Mumbai (950km)</p>
                <p className="text-xs text-amber-600 mt-1">Note: Rating exceeds requirement (Acceptable Substitution)</p>
              </div>
              <button className="px-4 py-2 bg-slate-900 text-white rounded font-medium flex items-center gap-2 hover:bg-slate-800">
                <ShoppingCart size={16} /> Compose Requisition
              </button>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
