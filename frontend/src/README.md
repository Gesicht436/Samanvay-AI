# Frontend Source Code (`frontend/src`)

## 1. Overview
The `src` directory contains the application code for the Samanvay-AI Web Portal. It is built using **Next.js 16 (App Router)**, **React 19**, **TypeScript**, and **Tailwind CSS**.

---

## 2. Directory Architecture

```
frontend/src/
|-- app/                         # Next.js App Router routes and pages
|   |-- audits/                  # Sovereign audit trail and compliance ledger
|   |-- dashboard/               # Procurement KPIs and surplus inventory discovery radar
|   |-- deduplication/           # Material deduplication studio & scanned MTC viewer
|   |-- hitl/                    # Human-in-the-Loop batch triage review queue
|   |-- transfers/               # Inter-CPSE material requisitions & CISF gate pass hub
|   |-- globals.css              # Global styles, Tailwind base directives, typography
|   |-- layout.tsx               # Root application layout incorporating TopNav
|   `-- page.tsx                 # Root redirection to /dashboard
|-- components/                  # Reusable UI component library
|   |-- TopNav.tsx               # Amazon-style global navigation bar and depot switcher
|   `-- ui/                      # Base primitive UI elements (buttons, badges, modals)
|-- lib/                         # Shared libraries, utilities, and API services
|   |-- api.ts                   # Centralized HTTP API client with backend integration
|   |-- exportUtils.ts           # RFC 4180 compliant Excel CSV export utility
|   |-- mockData.ts              # Resilient fallback fixtures for offline operation
|   `-- types.ts                 # TypeScript type definitions and interfaces
`-- README.md                    # This file
```

---

## 3. Design System and Visual Standards

Samanvay-AI follows the visual identity of **Amazon Business** and the **AWS Management Console**:

### Color Palette
- Primary Header Background: `#131921` (Amazon Deep Navy).
- Sub-Navigation Ribbon: `#232f3e` (Navy Secondary).
- Search Button & Action Accent: `#febd69` with hover `#f3a847` (Amazon Gold).
- Card Background: `#ffffff` (Pure White).
- Card Border: `#d5d9d9` (Subtle Amazon Gray Border).
- Page Background: `#f8fafc` (Light Slate).
- Primary Typography: `#0f1111` (High-contrast Charcoal Black).
- Secondary Typography: `#565959` (Muted Gray).

### Status and Equivalence Badges
- Tier-1 Identical: Green badge (`bg-emerald-50 text-emerald-800 border-emerald-300`).
- Tier-2 Substitute / Upgrade: Blue badge (`bg-blue-50 text-blue-800 border-blue-300`).
- Tier-3 Incompatible: Red badge (`bg-red-50 text-red-800 border-red-300`).
- Exact Spec Match: Green pill (`bg-green-100 text-green-800`).
- Valid Spec Upgrade: Amber pill (`bg-amber-100 text-amber-800`).
- Spec Mismatch: Red pill (`bg-rose-100 text-rose-800`).

---

## 4. State Management and API Resilience

To ensure that the application works seamlessly during hackathon presentations, network interruptions, or backend restarts:
1. Live Backend Integration: `lib/api.ts` makes asynchronous HTTP calls to the FastAPI backend running at `http://localhost:8000`.
2. Automatic Graceful Fallback: If the backend service is offline or unreachable, API client calls catch network exceptions and automatically return realistic fixtures from `lib/mockData.ts`.
3. Client-Side State: Components utilize standard React 19 hooks (`useState`, `useEffect`, `useCallback`, `useMemo`) for fast, reactive UI filtering without extra external state libraries.
