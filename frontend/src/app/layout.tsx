import "./globals.css";
import { Sidebar } from "@/components/Sidebar";
import { ThemeProvider } from "@/components/ThemeProvider";

export const metadata = {
  title: "Samanvay-AI | Sovereign Spare Material Harmonization Portal",
  description: "Cross-CPSE Spare Material Harmonization, Inward Bill OCR Intake, & Transparent Transfer Indenting Platform",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="min-h-screen flex flex-col antialiased bg-[var(--bg-primary)] text-[var(--text-primary)]">
        <ThemeProvider>
          <div className="flex min-h-screen">
            {/* Minimalist Collapsible/Responsive Left Sidebar */}
            <Sidebar />

            {/* Main Application Content Area */}
            <div className="flex-1 flex flex-col min-w-0">
              <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-7xl w-full mx-auto">
                {children}
              </main>

              {/* Minimalist Clean Footer */}
              <footer className="border-t border-[var(--border-subtle)] bg-[var(--bg-secondary)] py-3 px-6 text-xs text-[var(--text-muted)] no-print">
                <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-[var(--accent-primary)]"></span>
                    <span>Samanvay-AI Sovereign Platform • Ministry of Petroleum & Natural Gas (MoPNG)</span>
                  </div>
                  <div className="text-[11px] space-x-2">
                    <span>ASME B16.5 / B16.34</span>
                    <span>•</span>
                    <span>NACE MR0175</span>
                    <span>•</span>
                    <span>API 600 / 682</span>
                    <span>•</span>
                    <span>CVC Compliant</span>
                  </div>
                </div>
              </footer>
            </div>
          </div>
        </ThemeProvider>
      </body>
    </html>
  );
}
