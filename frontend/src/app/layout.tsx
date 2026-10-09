import "./globals.css";
import Link from "next/link";

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body><header className="app-header"><Link href="/" className="brand">SAMANVAY <span>/ AI</span></Link><nav aria-label="Main navigation"><Link href="/dashboard">Dashboard</Link><Link href="/deduplication">Match materials</Link><Link href="/ingest">Document intake</Link><Link href="/hitl">Review queue</Link></nav></header>{children}</body></html>;
}
