'use client';

import React, { useState, useEffect, useRef, useTransition } from 'react';
import { useRouter } from 'next/navigation';
import { useTheme } from './ThemeProvider';
import { api } from '@/lib/api';
import { exportToCSV } from '@/lib/exportUtils';
import {
  Search,
  LayoutDashboard,
  Layers,
  Package,
  Upload,
  Truck,
  ShieldCheck,
  UserCheck,
  Building2,
  FileSpreadsheet,
  QrCode,
  ArrowRight,
  Sparkles,
  Command,
  X,
} from 'lucide-react';

interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
  onOpen?: () => void;
}

const CPSE_OPTIONS = [
  { id: 'OIL', name: 'Oil India Limited (OIL)' },
  { id: 'IOCL', name: 'Indian Oil Corporation (IOCL)' },
  { id: 'ONGC', name: 'Oil & Natural Gas Corp (ONGC)' },
  { id: 'BPCL', name: 'Bharat Petroleum (BPCL)' },
  { id: 'HPCL', name: 'Hindustan Petroleum (HPCL)' },
  { id: 'GAIL', name: 'GAIL (India) Limited' },
  { id: 'NRL', name: 'Numaligarh Refinery (NRL)' },
];

export function CommandPalette({ isOpen, onClose, onOpen }: CommandPaletteProps) {
  const router = useRouter();
  const { cpse, setCpse } = useTheme();
  const [query, setQuery] = useState('');
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [exportMessage, setExportMessage] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 50);
      setQuery('');
      setSearchResults([]);
      setExportMessage(null);
    }
  }, [isOpen]);

  // Global keyboard shortcut
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        if (isOpen) {
          onClose();
        } else {
          onOpen?.();
        }
      } else if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose, onOpen]);

  // Live Backend Search for items/SKUs
  useEffect(() => {
    if (!query.trim() || query.length < 2) {
      setSearchResults([]);
      setIsSearching(false);
      return;
    }

    const timer = setTimeout(async () => {
      setIsSearching(true);
      try {
        const res = await api.getInventory({ limit: 50 });
        const items = Array.isArray(res?.items) ? res.items : Array.isArray(res) ? res : [];
        const q = query.toLowerCase();
        const matches = items.filter(
          (it: any) =>
            it.sku_code?.toLowerCase().includes(q) ||
            it.description?.toLowerCase().includes(q) ||
            it.standard?.toLowerCase().includes(q) ||
            it.metallurgy?.toLowerCase().includes(q) ||
            it.item_type?.toLowerCase().includes(q)
        );
        setSearchResults(matches);
      } catch {
        setSearchResults([]);
      } finally {
        setIsSearching(false);
      }
    }, 250);

    return () => clearTimeout(timer);
  }, [query]);

  const handleNavigate = (path: string) => {
    onClose();
    router.push(path);
  };

  const handleSwitchCpse = (newCpse: string) => {
    setCpse(newCpse);
    onClose();
  };

  const handleExportAudit = async () => {
    try {
      setExportMessage('Exporting sovereign audit ledger...');
      const res = await api.getAuditLogs({ limit: 1000 });
      const logs = Array.isArray(res?.items) ? res.items : Array.isArray(res) ? res : [];
      exportToCSV(logs, `cag_cryptographic_audit_${new Date().toISOString().slice(0, 10)}.csv`);
      setExportMessage('CAG Audit CSV downloaded successfully.');
      setTimeout(() => {
        onClose();
      }, 1200);
    } catch {
      setExportMessage('Failed to download audit logs.');
    }
  };

  if (!isOpen) return null;

  const navLinks = [
    { title: 'Command Center', icon: LayoutDashboard, path: '/dashboard', shortcut: 'G D' },
    { title: 'Surplus Discovery (ML Compatibility)', icon: Layers, path: '/discover', shortcut: 'G S' },
    { title: 'Stock Ledger (Live Inventory)', icon: Package, path: '/inventory', shortcut: 'G I' },
    { title: 'MTC Intake & OCR Inspection', icon: Upload, path: '/upload', shortcut: 'G U' },
    { title: 'Consignments & Gate Passes', icon: Truck, path: '/requests', shortcut: 'G C' },
    { title: 'Sovereign Audit Ledger (Merkle Root)', icon: ShieldCheck, path: '/audit', shortcut: 'G A' },
    { title: 'User Approvals (Admin)', icon: UserCheck, path: '/admin/users', shortcut: 'G P' },
  ].filter(
    (item) => !query.trim() || item.title.toLowerCase().includes(query.toLowerCase())
  );

  const matchedCpse = CPSE_OPTIONS.filter(
    (c) =>
      query.trim() &&
      (c.id.toLowerCase().includes(query.toLowerCase()) ||
        c.name.toLowerCase().includes(query.toLowerCase()))
  );

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-20 px-4 bg-black/50 backdrop-blur-xs animate-in fade-in duration-100">
      <div
        className="w-full max-w-xl bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-xl shadow-2xl overflow-hidden flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Search Input Bar */}
        <div className="flex items-center gap-3 px-4 py-3 border-b border-zinc-100 dark:border-zinc-800">
          <Search size={16} className="text-zinc-400 shrink-0" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Type a command, search parts, SKU, or CPSE..."
            className="flex-1 bg-transparent text-sm text-zinc-900 dark:text-zinc-100 placeholder:text-zinc-400 outline-hidden font-sans"
          />
          {query && (
            <button
              onClick={() => setQuery('')}
              className="text-xs text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-200"
            >
              Clear
            </button>
          )}
          <kbd className="hidden sm:inline-flex items-center gap-0.5 px-1.5 py-0.5 text-[10px] font-mono text-zinc-400 bg-zinc-100 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded">
            ESC
          </kbd>
        </div>

        {exportMessage && (
          <div className="px-4 py-2 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 text-xs font-mono border-b border-emerald-500/20">
            {exportMessage}
          </div>
        )}

        {/* Action Results Container */}
        <div className="max-h-[60vh] overflow-y-auto p-2 divide-y divide-zinc-100 dark:divide-zinc-800/60">
          {/* Live Inventory Results */}
          {searchResults.length > 0 && (
            <div className="py-2">
              <div className="px-2 pb-1 text-[10px] font-mono font-semibold uppercase tracking-wider text-zinc-400">
                Matching Live Parts ({searchResults.length})
              </div>
              {searchResults.map((item) => (
                <button
                  key={item.sku_code}
                  onClick={() => handleNavigate(`/inventory?search=${encodeURIComponent(item.sku_code)}`)}
                  className="w-full flex items-center justify-between px-3 py-2 rounded-lg text-left text-xs hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors group"
                >
                  <div className="min-w-0 pr-2">
                    <span className="font-mono font-semibold text-zinc-900 dark:text-zinc-100">
                      {item.sku_code}
                    </span>
                    <span className="text-zinc-400 ml-2 truncate">· {item.description}</span>
                  </div>
                  <span className="text-[10px] font-mono text-zinc-400 uppercase group-hover:text-zinc-900 dark:group-hover:text-zinc-100 shrink-0">
                    {item.cpse} →
                  </span>
                </button>
              ))}
            </div>
          )}

          {/* CPSE Context Switcher */}
          {(query.toLowerCase().includes('cpse') || matchedCpse.length > 0) && (
            <div className="py-2">
              <div className="px-2 pb-1 text-[10px] font-mono font-semibold uppercase tracking-wider text-zinc-400">
                Switch CPSE Tenant Context
              </div>
              {(matchedCpse.length > 0 ? matchedCpse : CPSE_OPTIONS).map((c) => (
                <button
                  key={c.id}
                  onClick={() => handleSwitchCpse(c.id)}
                  className="w-full flex items-center justify-between px-3 py-1.5 rounded-lg text-left text-xs hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors"
                >
                  <div className="flex items-center gap-2">
                    <Building2 size={13} className="text-zinc-400" />
                    <span className="text-zinc-800 dark:text-zinc-200">{c.name}</span>
                  </div>
                  {cpse === c.id ? (
                    <span className="text-[10px] font-mono text-emerald-600 dark:text-emerald-400 font-semibold">
                      ACTIVE
                    </span>
                  ) : (
                    <span className="text-[10px] font-mono text-zinc-400">Select</span>
                  )}
                </button>
              ))}
            </div>
          )}

          {/* Quick Actions */}
          {(!query.trim() || query.toLowerCase().includes('export') || query.toLowerCase().includes('audit') || query.toLowerCase().includes('cag')) && (
            <div className="py-2">
              <div className="px-2 pb-1 text-[10px] font-mono font-semibold uppercase tracking-wider text-zinc-400">
                Quick Actions
              </div>
              <button
                onClick={handleExportAudit}
                className="w-full flex items-center justify-between px-3 py-2 rounded-lg text-left text-xs hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors"
              >
                <div className="flex items-center gap-2.5">
                  <FileSpreadsheet size={14} className="text-zinc-500" />
                  <span className="text-zinc-800 dark:text-zinc-200">
                    Export CAG Cryptographic Audit Ledger (CSV)
                  </span>
                </div>
                <span className="text-[10px] font-mono text-zinc-400">RFC-4180</span>
              </button>
              <button
                onClick={() => handleNavigate('/requests')}
                className="w-full flex items-center justify-between px-3 py-2 rounded-lg text-left text-xs hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors"
              >
                <div className="flex items-center gap-2.5">
                  <QrCode size={14} className="text-zinc-500" />
                  <span className="text-zinc-800 dark:text-zinc-200">
                    Verify CISF Gate Pass & QR Barcode
                  </span>
                </div>
                <span className="text-[10px] font-mono text-zinc-400">Gate Pass</span>
              </button>
            </div>
          )}

          {/* Navigation Section */}
          {navLinks.length > 0 && (
            <div className="py-2">
              <div className="px-2 pb-1 text-[10px] font-mono font-semibold uppercase tracking-wider text-zinc-400">
                Navigation
              </div>
              {navLinks.map((item) => {
                const Icon = item.icon;
                return (
                  <button
                    key={item.path}
                    onClick={() => handleNavigate(item.path)}
                    className="w-full flex items-center justify-between px-3 py-2 rounded-lg text-left text-xs hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors"
                  >
                    <div className="flex items-center gap-2.5">
                      <Icon size={14} className="text-zinc-400" />
                      <span className="text-zinc-800 dark:text-zinc-200">{item.title}</span>
                    </div>
                    <ArrowRight size={12} className="text-zinc-400" />
                  </button>
                );
              })}
            </div>
          )}

          {navLinks.length === 0 && searchResults.length === 0 && matchedCpse.length === 0 && (
            <div className="py-8 text-center text-xs text-zinc-400">
              No matching commands or parts for &quot;{query}&quot;
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-4 py-2 border-t border-zinc-100 dark:border-zinc-800 bg-zinc-50/50 dark:bg-zinc-900/50 flex items-center justify-between text-[11px] font-mono text-zinc-400">
          <div className="flex items-center gap-3">
            <span>Navigation: Click or Enter</span>
            <span>·</span>
            <span>Current Node: <strong className="text-zinc-700 dark:text-zinc-300">{cpse}</strong></span>
          </div>
          <span>Samanvay-AI Command Hub</span>
        </div>
      </div>
    </div>
  );
}
