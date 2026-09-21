"use client";
import React from 'react';
import { useTheme } from './ThemeProvider';
import { Sun, Moon } from 'lucide-react';

export function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();

  return (
    <button
      onClick={toggleTheme}
      className="flex items-center gap-2.5 px-3 py-2 w-full rounded-md text-xs font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-800 transition-colors"
      aria-label="Toggle theme"
      title="Toggle Light / Dark Mode"
    >
      {theme === 'light' ? (
        <>
          <Moon size={15} className="text-slate-600 dark:text-slate-300 shrink-0" />
          <span className="truncate">Dark Mode</span>
        </>
      ) : (
        <>
          <Sun size={15} className="text-amber-400 shrink-0" />
          <span className="truncate">Light Mode</span>
        </>
      )}
    </button>
  );
}
