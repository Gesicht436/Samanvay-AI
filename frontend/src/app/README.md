# Next.js App Router Pages (`frontend/src/app`)

## 1. Overview
The `app` directory uses the **Next.js App Router** file-system routing convention. Every directory containing a `page.tsx` file defines a public URL route in the application.

---

## 2. Route Directory Map

| Directory Path | URL Route | Page Name | Primary Responsibility |
|---|---|---|---|
| `app/page.tsx` | `/` | Root Redirect | Redirects the user directly to the primary `/dashboard` view. |
| `app/dashboard/` | `/dashboard` | Procurement Dashboard | Working capital metrics, surplus discovery radar, and cross-CPSE filters. |
| `app/deduplication/` | `/deduplication` | Deduplication Studio | Real-time specification extraction, ASME safety tolerance breakdown, and scanned MTC viewer. |
| `app/hitl/` | `/hitl` | HITL Triage Queue | Side-by-side human review cards for borderline matches and Tier-2 upgrades. |
| `app/transfers/` | `/transfers` | Transfer Requisitions | Inter-CPSE material requisitions, GIS logistics routing, and printable CISF gate passes. |
| `app/audits/` | `/audits` | Sovereign Audit Ledger | Chronological compliance event stream with cryptographic SHA-256 digital seals. |

---

## 3. Key Files Explained

### 1. `layout.tsx` (Root Layout)
- Defines the HTML document skeleton (`<html>`, `<body>`).
- Imports `globals.css` for Tailwind CSS utilities and custom scrollbar rules.
- Embeds the global Amazon-style navigation header (`TopNav.tsx`), ensuring consistent branding and depot navigation across every page.

### 2. `page.tsx` (Root Page)
- A lightweight entrypoint that uses the Next.js `redirect("/dashboard")` method to present the procurement dashboard by default.

### 3. `globals.css` (Global Stylesheet)
- Tailwind CSS directives (`@tailwind base;`, `@tailwind components;`, `@tailwind utilities;`).
- Custom scrollbar styling and print media rules for high-resolution printing of CISF Material Gate Passes without headers or footers.

---

## 4. Client vs. Server Components
All major application pages in this portal declare `'use client'` at the top of the file:
- Rationale: Pages require interactive state (e.g. text inputs, category filters, modal dialogs, tab switching, and asynchronous button triggers).
- Next.js compiles these as interactive Client Components while preserving static pre-rendering at build time (`next build`).
