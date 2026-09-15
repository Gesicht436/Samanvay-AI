# Primitive UI Components (`frontend/src/components/ui`)

## 1. Overview
The `components/ui` directory is designated for reusable, low-level design primitives such as buttons, status badges, cards, input fields, and modal dialogs.

These components encapsulate the visual styling tokens of the Amazon Business and AWS Console design system, ensuring consistent borders, typography, hover states, and focus outlines across the application.

---

## 2. Standard Design Primitives

### 1. Status Badges & Equivalence Pills
- Tier-1 Identical:
  `px-2.5 py-1 text-xs font-semibold rounded-full bg-emerald-50 text-emerald-800 border border-emerald-300`
- Tier-2 Substitute:
  `px-2.5 py-1 text-xs font-semibold rounded-full bg-blue-50 text-blue-800 border border-blue-300`
- Tier-3 Incompatible:
  `px-2.5 py-1 text-xs font-semibold rounded-full bg-red-50 text-red-800 border border-red-300`
- Parameter Exact Match:
  `px-2 py-0.5 text-xs font-medium rounded bg-green-100 text-green-800`
- Parameter Safe Upgrade:
  `px-2 py-0.5 text-xs font-medium rounded bg-amber-100 text-amber-800`
- Parameter Mismatch:
  `px-2 py-0.5 text-xs font-medium rounded bg-rose-100 text-rose-800`

### 2. Standard Action Buttons
- Primary Gold Button (Amazon CTA):
  `bg-[#febd69] hover:bg-[#f3a847] text-[#0f1111] font-medium px-4 py-2 rounded-md shadow-sm border border-[#a88734]`
- Secondary White Button:
  `bg-white hover:bg-slate-50 text-slate-700 font-medium px-4 py-2 rounded-md border border-slate-300 shadow-sm`
- Danger Red Button:
  `bg-red-600 hover:bg-red-700 text-white font-medium px-4 py-2 rounded-md shadow-sm`

### 3. Data Tables
- Table Container:
  `bg-white border border-[#d5d9d9] rounded-lg overflow-hidden shadow-sm`
- Table Header:
  `bg-slate-50 border-b border-slate-200 text-xs font-semibold text-slate-600 uppercase tracking-wider`
- Table Row:
  `border-b border-slate-100 hover:bg-slate-50/80 transition-colors`

---

## 3. Accessibility Standards
1. Focus States: All interactive buttons and inputs include visible focus rings (`focus:ring-2 focus:ring-amber-500 focus:outline-none`).
2. Color Contrast: Text combinations meet WCAG AA standards (contrast ratio >= 4.5:1 against light backgrounds).
3. Semantics: Native HTML elements (`<button>`, `<table>`, `<input>`) are used directly rather than non-semantic `<div>` clickables.
