import type { Metadata } from "next";
import "./globals.css";
import { ThemeProvider } from "@/components/ThemeProvider";
import { Sidebar } from "@/components/Sidebar";
import { ThemeToggle } from "@/components/ThemeToggle";

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
    <html lang="en" suppressHydrationWarning>
      <body className="antialiased flex h-screen overflow-hidden">
        <ThemeProvider>
          <Sidebar />
          <div className="flex-1 flex flex-col min-w-0">
            <header className="h-14 border-b border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 flex items-center justify-between px-6 shrink-0 no-print">
              <div className="flex items-center gap-2">
                <span className="font-semibold text-sm tracking-wide">MINISTRY OF PETROLEUM & NATURAL GAS</span>
                <span className="px-2 py-0.5 bg-rose-100 text-rose-800 text-xs font-mono rounded">RESTRICTED</span>
              </div>
              <div className="flex items-center gap-4">
                <span className="text-sm font-mono text-slate-500">Node: SOVEREIGN-01</span>
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
