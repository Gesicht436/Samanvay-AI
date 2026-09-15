import "./globals.css";
import TopNav from "@/components/TopNav";

export const metadata = {
  title: "Samanvay | Material Code Harmonization",
  description: "Cross-CPSE Material Harmonization & Spare Parts Management",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-[#f4f6f8] text-[#0f1111] min-h-screen flex flex-col antialiased selection:bg-[#ffd814] selection:text-[#0f1111]">
        {/* Top Navigation */}
        <TopNav />

        {/* Main Content */}
        <main className="flex-1 max-w-[1600px] w-full mx-auto p-4 sm:p-6">
          {children}
        </main>

        {/* Minimal Functional Footer */}
        <footer className="bg-white border-t border-[#d5d9d9] py-4 text-xs text-[#565959] no-print">
          <div className="max-w-[1600px] mx-auto px-4 sm:px-6 flex flex-col sm:flex-row items-center justify-between gap-2">
            <div>
              Samanvay Material Management System • Ministry of Petroleum & Natural Gas (MoPNG)
            </div>
            <div className="flex items-center gap-4 text-[#565959]">
              <span>Standards: ASME B16.5, B16.34, B16.9, IS/IEC 60079, API 682, ISO 15</span>
              <span>•</span>
              <span>UNSPSC v26</span>
            </div>
          </div>
        </footer>
      </body>
    </html>
  );
}
