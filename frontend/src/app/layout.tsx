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
                <span className="font-bold text-sm tracking-wide text-slate-800 dark:text-slate-100">
                  MINISTRY OF PETROLEUM & NATURAL GAS
                </span>
                <span className="px-2 py-0.5 bg-rose-100 dark:bg-rose-950/60 text-rose-800 dark:text-rose-300 text-xs font-mono font-semibold rounded border border-rose-200 dark:border-rose-900">
                  RESTRICTED
                </span>
                <div className="hidden md:flex items-center gap-2 px-2.5 py-0.5 bg-emerald-50 dark:bg-emerald-950/50 border border-emerald-200 dark:border-emerald-800/60 rounded-full">
                  <span className="relative flex h-2 w-2">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                  </span>
                  <span className="text-[11px] font-mono font-medium text-emerald-700 dark:text-emerald-400">
                    P2P MESH ONLINE (5 NODES)
                  </span>
                </div>
              </div>
              <div className="flex items-center gap-4">
                <span className="text-xs font-mono text-slate-500 bg-slate-100 dark:bg-slate-800 px-2 py-1 rounded">
                  Node: SOVEREIGN-01
                </span>
                <ThemeToggle />
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
