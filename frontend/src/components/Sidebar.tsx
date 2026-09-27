'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useTheme } from './ThemeProvider';
import { useAuth } from '@/context/AuthContext';
import {
  LayoutDashboard,
  Layers,
  Package,
  Upload,
  Truck,
  ShieldCheck,
  UserCheck,
  PanelLeftClose,
  PanelLeftOpen,
  LogOut,
  User as UserIcon,
  X,
} from 'lucide-react';
import { ThemeToggle } from './ThemeToggle';

interface SidebarProps {
  collapsed?: boolean;
  onToggleCollapse?: () => void;
  isMobile?: boolean;
  onCloseMobile?: () => void;
}

export function Sidebar({
  collapsed: propCollapsed,
  onToggleCollapse,
  isMobile = false,
  onCloseMobile,
}: SidebarProps) {
  const pathname = usePathname();
  const { cpse } = useTheme();
  const { user, logout } = useAuth();
  const [internalCollapsed, setInternalCollapsed] = useState<boolean>(false);

  // Sync with local storage
  useEffect(() => {
    const saved = localStorage.getItem('samanvay_sidebar_collapsed');
    if (saved !== null) {
      setInternalCollapsed(saved === 'true');
    }
  }, []);

  const isCollapsed = isMobile ? false : (propCollapsed !== undefined ? propCollapsed : internalCollapsed);

  const toggleCollapse = () => {
    if (isMobile) return;
    const next = !isCollapsed;
    setInternalCollapsed(next);
    localStorage.setItem('samanvay_sidebar_collapsed', String(next));
    if (onToggleCollapse) onToggleCollapse();
  };

  // Keyboard shortcut: '[' to toggle sidebar collapse
  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      // Don't trigger when user is typing in input/textarea
      const target = e.target as HTMLElement;
      if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable) {
        return;
      }
      if (e.key === '[') {
        e.preventDefault();
        toggleCollapse();
      }
    };
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, [isCollapsed]);

  const role = user?.role || 'SITE_ENGINEER';

  const navItems = [
    { name: 'Command Center', href: '/dashboard', icon: LayoutDashboard },
    { name: 'Surplus Discovery', href: '/discover', icon: Layers },
    { name: 'Stock Ledger', href: '/inventory', icon: Package },
    { name: 'MTC Intake', href: '/upload', icon: Upload },
    { name: 'Consignments', href: '/requests', icon: Truck },
    { name: 'Audit Ledger', href: '/audit', icon: ShieldCheck },
  ];

  if (role === 'SUPER_ADMIN' || role === 'CPSE_ADMIN') {
    navItems.push({
      name: 'User Approvals',
      href: '/admin/users',
      icon: UserCheck,
    });
  }

  return (
    <aside
      className={`relative bg-white dark:bg-zinc-950 flex flex-col justify-between transition-all duration-200 ease-in-out shrink-0 select-none ${
        isMobile
          ? 'w-full h-full border-r-0'
          : `h-screen border-r border-zinc-200 dark:border-zinc-800 ${isCollapsed ? 'w-14' : 'w-60'}`
      }`}
    >
      {/* Header / Brand */}
      <div>
        <div className="h-12 border-b border-zinc-200 dark:border-zinc-800 flex items-center justify-between px-3.5">
          <Link
            href="/dashboard"
            onClick={() => {
              if (isMobile && onCloseMobile) onCloseMobile();
            }}
            className="flex items-center gap-2.5 min-w-0"
          >
            {/* Hexagonal Sovereign Emblem */}
            <div className="w-6 h-6 rounded-md bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900 flex items-center justify-center font-mono font-bold text-xs shrink-0 tracking-tighter shadow-xs">
              SV
            </div>
            {(!isCollapsed || isMobile) && (
              <div className="flex flex-col min-w-0">
                <span className="font-semibold text-xs tracking-tight text-zinc-900 dark:text-zinc-100 truncate">
                  SAMANVAY-AI
                </span>
                <span className="text-[9px] font-mono text-zinc-400 dark:text-zinc-500 uppercase tracking-widest truncate">
                  MoPNG Sovereign Mesh
                </span>
              </div>
            )}
          </Link>

          {isMobile ? (
            <button
              onClick={onCloseMobile}
              className="p-1.5 rounded-md text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-100 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors min-w-[36px] min-h-[36px] flex items-center justify-center"
              title="Close menu"
              aria-label="Close menu"
            >
              <X size={16} />
            </button>
          ) : (
            !isCollapsed && (
              <button
                onClick={toggleCollapse}
                className="p-1 rounded text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-200 hover:bg-zinc-100 dark:hover:bg-zinc-850 transition-colors"
                title="Collapse sidebar ([)"
              >
                <PanelLeftClose size={15} />
              </button>
            )
          )}
        </div>

        {/* Collapsed expand button (desktop only) */}
        {isCollapsed && !isMobile && (
          <div className="flex justify-center py-2 border-b border-zinc-100 dark:border-zinc-800/80">
            <button
              onClick={toggleCollapse}
              className="p-1.5 rounded text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-200 hover:bg-zinc-100 dark:hover:bg-zinc-850 transition-colors"
              title="Expand sidebar ([)"
            >
              <PanelLeftOpen size={15} />
            </button>
          </div>
        )}

        {/* Nav Links */}
        <nav className="p-2 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive =
              pathname === item.href ||
              (item.href !== '/dashboard' && pathname.startsWith(item.href));

            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => {
                  if (isMobile && onCloseMobile) onCloseMobile();
                }}
                title={isCollapsed && !isMobile ? item.name : undefined}
                className={`group flex items-center gap-2.5 rounded-md transition-colors ${
                  isMobile ? 'px-3 py-2.5 min-h-[40px] text-sm' : 'px-2.5 py-1.5 text-xs'
                } ${
                  isActive
                    ? 'bg-zinc-100 dark:bg-zinc-800 text-zinc-900 dark:text-zinc-50 font-medium'
                    : 'text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100 hover:bg-zinc-50 dark:hover:bg-zinc-850'
                } ${isCollapsed && !isMobile ? 'justify-center px-0' : ''}`}
              >
                <Icon
                  size={15}
                  className={`shrink-0 transition-colors ${
                    isActive
                      ? 'text-zinc-900 dark:text-zinc-100'
                      : 'text-zinc-400 dark:text-zinc-500 group-hover:text-zinc-700 dark:group-hover:text-zinc-300'
                  }`}
                />
                {(!isCollapsed || isMobile) && <span className="truncate">{item.name}</span>}
              </Link>
            );
          })}
        </nav>
      </div>

      {/* Footer / User Identity / Controls */}
      <div className="p-2 border-t border-zinc-200 dark:border-zinc-800 space-y-2">
        {/* User Card */}
        {user ? (
          <div
            className={`flex items-center gap-2 p-1.5 rounded-md bg-zinc-50 dark:bg-zinc-900 border border-zinc-100 dark:border-zinc-800/80 ${
              isCollapsed ? 'justify-center p-1' : ''
            }`}
          >
            <div className="w-6 h-6 rounded-full bg-zinc-200 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 flex items-center justify-center font-mono text-[10px] font-bold shrink-0">
              {user.username.slice(0, 2).toUpperCase()}
            </div>
            {!isCollapsed && (
              <div className="flex-1 min-w-0 pr-1">
                <p className="text-[11px] font-medium text-zinc-900 dark:text-zinc-100 truncate leading-tight">
                  {user.full_name || user.username}
                </p>
                <p className="text-[9px] font-mono text-zinc-400 dark:text-zinc-500 truncate">
                  {user.cpse} · {user.role.replace('_', ' ')}
                </p>
              </div>
            )}
            {!isCollapsed && (
              <button
                onClick={logout}
                className="p-1 rounded text-zinc-400 hover:text-rose-600 dark:hover:text-rose-400 transition-colors"
                title="Sign out"
              >
                <LogOut size={13} />
              </button>
            )}
          </div>
        ) : (
          <Link
            href="/login"
            className={`flex items-center gap-2 p-1.5 rounded-md border border-dashed border-zinc-300 dark:border-zinc-700 text-xs text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100 transition-colors ${
              isCollapsed ? 'justify-center' : ''
            }`}
            title="Sign in"
          >
            <UserIcon size={14} className="shrink-0 text-zinc-400" />
            {!isCollapsed && <span>Sign In</span>}
          </Link>
        )}

        {/* Theme Toggle & Node indicator */}
        <div
          className={`flex items-center ${
            isCollapsed ? 'flex-col gap-1 justify-center' : 'justify-between px-1'
          }`}
        >
          <ThemeToggle collapsed={isCollapsed} />
          {!isCollapsed && (
            <div className="flex items-center gap-1.5 text-[10px] font-mono text-zinc-400 dark:text-zinc-500">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 shrink-0" />
              <span>{cpse}</span>
            </div>
          )}
        </div>
      </div>
    </aside>
  );
}
