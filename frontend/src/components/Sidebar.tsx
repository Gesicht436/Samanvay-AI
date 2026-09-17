"use client";

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useTheme } from './ThemeProvider';
import { CPSE_DEPOTS } from '@/lib/constants';
import { Upload, Package, Search, Mail, ShieldAlert } from 'lucide-react';

export function Sidebar() {
  const pathname = usePathname();
  const { cpse, setCpse } = useTheme();

  const links = [
    { name: 'Upload', href: '/upload', icon: Upload },
    { name: 'Inventory', href: '/inventory', icon: Package },
    { name: 'Discover', href: '/discover', icon: Search },
    { name: 'Requests', href: '/requests', icon: Mail },
    { name: 'Audit', href: '/audit', icon: ShieldAlert },
  ];

  return (
    <div className="w-64 h-full bg-slate-900 text-slate-100 flex flex-col no-print">
      <div className="p-4 border-b border-slate-700">
        <h1 className="text-xl font-bold mb-4 tracking-tight">Samanvay-AI</h1>
        <select 
          value={cpse} 
          onChange={(e) => setCpse(e.target.value)}
          className="w-full bg-slate-800 border border-slate-600 rounded p-2 text-sm"
        >
          {CPSE_DEPOTS.map(d => (
            <option key={d.id} value={d.id}>{d.name}</option>
          ))}
        </select>
      </div>
      
      <nav className="flex-1 p-4 space-y-2">
        {links.map((link) => {
          const Icon = link.icon;
          const isActive = pathname.startsWith(link.href);
          return (
            <Link key={link.name} href={link.href}
              className={`flex items-center gap-3 p-2 rounded transition-colors ${
                isActive ? 'bg-emerald-600 text-white' : 'hover:bg-slate-800'
              }`}
            >
              <Icon size={20} />
              <span className="font-medium">{link.name}</span>
            </Link>
          );
        })}
      </nav>
      
      <div className="p-4 text-xs text-slate-500 font-mono">
        MoPNG Sovereign Node
      </div>
    </div>
  );
}
