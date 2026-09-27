"use client";
import React from 'react';
import { useTheme } from './ThemeProvider';
import { Sun, Moon } from 'lucide-react';

export function ThemeToggle({ collapsed = false }: { collapsed?: boolean }) {
  const { theme, toggleTheme } = useTheme();

  return (
    <button
      onClick={toggleTheme}
      className={`flex items-center gap-2 p-1.5 rounded-md text-xs font-medium text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100 hover:bg-zinc-100 dark:hover:bg-zinc-850 transition-colors ${
        collapsed ? 'justify-center w-full' : ''
      }`}
      aria-label="Toggle theme"
      title={theme === 'light' ? 'Switch to Dark Mode' : 'Switch to Light Mode'}
    >
      {theme === 'light' ? (
        <Moon size={14} className="shrink-0 text-zinc-500" />
      ) : (
        <Sun size={14} className="shrink-0 text-amber-400" />
      )}
      {!collapsed && (
        <span className="truncate">{theme === 'light' ? 'Dark' : 'Light'}</span>
      )}
    </button>
  );
}
