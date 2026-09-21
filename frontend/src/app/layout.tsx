import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import { ThemeProvider } from "@/components/ThemeProvider";
import { Sidebar } from "@/components/Sidebar";
import { ThemeToggle } from "@/components/ThemeToggle";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-sans",
  display: "swap",
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Samanvay-AI | MoPNG Sovereign Node",
  description: "Cross-CPSE spare parts discovery & compatibility platform",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${inter.variable} ${jetbrainsMono.variable}`} suppressHydrationWarning>
      <body className="antialiased flex h-screen overflow-hidden font-sans">
        <ThemeProvider>
          <Sidebar />
          <div className="flex-1 flex flex-col min-w-0">
            <header className="h-14 border-b border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 flex items-center justify-between px-6 shrink-0 no-print">
              <div className="flex items-center gap-3">
                <span className="font-semibold text-sm tracking-wide text-slate-900 dark:text-slate-100">
                  MINISTRY OF PETROLEUM & NATURAL GAS
                </span>
                <span className="text-xs text-slate-400">|</span>
                <span className="text-xs font-mono text-slate-600 dark:text-slate-300">
                  Inter-CPSE Spare Parts & Material Sharing System
                </span>
              </div>
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-2 px-2.5 py-1 bg-slate-100 dark:bg-slate-800 rounded text-xs font-mono text-slate-700 dark:text-slate-300">
                  <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
                  <span>Backend Gateway: Connected</span>
                </div>
              </div>
            </header>
            <main className="flex-1 overflow-auto bg-slate-50 dark:bg-slate-950 p-6 print:p-0 print:bg-white">
              {children}
            </main>
          </div>
        </ThemeProvider>
      </body>
    </html>
  );
}
