# Shared UI Components (`frontend/src/components`)

## 1. Overview
The `components` directory contains reusable React components shared across multiple pages in the Samanvay-AI web portal.

---

## 2. Directory Structure

```
frontend/src/components/
|-- ui/                          # Base primitive UI elements (buttons, badges, modals)
|   `-- README.md                # Primitive component documentation
|-- TopNav.tsx                   # Amazon-style global navigation header and depot switcher
`-- README.md                    # This file
```

---

## 3. Component Reference: `TopNav.tsx`

`TopNav.tsx` establishes the consistent top header for the entire web portal, modeled directly on **Amazon Business**:

### Visual Structure
```
+---------------------------------------------------------------------------------------------+
| Samanvay-AI | Deliver to Depot:    | [ All Categories v ] [ Search procurement... ] [ Q ]   |
| (BharatCodex| Panipat Refinery, IOCL                                                        |
+---------------------------------------------------------------------------------------------+
| All | Dashboard | Deduplication & MTC | HITL Triage Queue | Transfers & Gate Pass | Audits  |
+---------------------------------------------------------------------------------------------+
```

### Key Features
1. Brand Identity: Displays the sovereign MoPNG emblem and project title.
2. Active Depot Switcher: A prominent dropdown allowing plant managers to switch their active operating facility (e.g. Panipat Refinery, Hazira Gas Plant, Kochi Refinery, Mathura Refinery, Uran Plant).
3. Global Procurement Search: A wide search bar with a category selector (Flanges, Valves, Pipes, Gaskets, Motors, Seals) and golden search button (`#febd69`).
4. Sub-Navigation Ribbon: Dark navy sub-bar (`#232f3e`) providing direct access to the 5 primary routes with visual active route indicators.
5. Mobile Responsive Menu: Collapses into an accessible slide-out mobile drawer on small screens.

---

## 4. Coding Conventions for UI Components
- Strict Typing: Every component defines a TypeScript interface for its props.
- Client State: Components that use browser events, state, or hooks declare `'use client'`.
- Styling: Styled purely with Tailwind CSS utility classes; avoid inline styles.
