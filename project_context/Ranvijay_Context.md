# Central Web Portal & Procurement Dashboard Workflow

**Role:** Frontend Developer (Ranvijay)

**Primary Directory:** `frontend/`

**Target Environment:** Node.js 26, Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS, shadcn/ui, TanStack Query

---

### Objective & Architectural Role

Your mission is to build the user-facing enterprise web application for **Samanvay-AI (BharatCodex)**.

The backend processes complex OCR text, runs neural token classification, and queries graph relationships, but the hackathon judges will evaluate the product through the interface you build. Your role is to translate raw API data into an enterprise-grade procurement workspace tailored for Ministry (MoPNG) executives and CPSE procurement officers.

You own the presentation and user-interaction layer:

1. **Catalog Ingestion Studio:** Drag-and-drop file upload for messy SAP MM Excel/CSV extracts with instant ingestion status.

2. **Human-in-the-Loop (HITL) Triage Panel:** An interactive review screen where procurement managers review ambiguous semantic matches ($70\% - 90\%$ confidence) and either accept, reclassify, or reject them.

3. **Cross-CPSE Reconciliation View:** Visual comparison side-by-side (e.g., IOCL SKU vs. ONGC SKU) highlighting identical engineering parameters and idle spare inventory.

4. **Procurement Analytics Dashboard:** Real-time metrics displaying duplicate catalog reduction, freed working capital, and inter-CPSE transfer requests.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        NEXT.JS 16 WEB PORTAL                           │
│                                                                        │
│  ┌───────────────────────┐ ┌───────────────────┐ ┌──────────────────┐  │
│  │   DEDUPLICATION &     │ │   HITL TRIAGE     │ │   PROCUREMENT    │  │
│  │   INGESTION STUDIO    │ │   QUEUE PANEL     │ │   ANALYTICS      │  │
│  │ (CSV/Excel/MTC Drag)  │ │ (Accept / Reject) │ │ (Capital Freed)  │  │
│  └──────────┬────────────┘ └─────────┬─────────┘ └─────────┬────────┘  │
│             │                        │                     │           │
│             └────────────────────────┼─────────────────────┘           │
│                                      ▼                                 │
│                           API CLIENT / DATA HOOKS                      │
│                           (TanStack React Query)                       │
└──────────────────────────────────────┬─────────────────────────────────┘
                                       │
                              REST / JSON Calls
                                       │
                                       ▼
                     Mayank's Unified FastAPI Gateway                   
                      (`http://localhost:8000/api/v1`)

```

---

### Task 1: Project Setup & Component System Setup

Set up a clean, modern UI shell using standard production tooling:

* **Foundation:** Next.js 16 App Router with TypeScript and Tailwind CSS.

* **Design System:** Install and configure **shadcn/ui** components:

```bash
npx shadcn@latest add button card table badge dialog dropdown-menu progress tabs

```

* **Lucide Icons:** Use `lucide-react` for clean industrial and enterprise iconography (e.g., `Layers`, `AlertCircle`, `CheckCircle2`, `ArrowRightLeft`, `Building2`).
* **State & Data Fetching:** Use `@tanstack/react-query` to handle caching, loading spinners, and optimistic updates when approving matches.

---

### Task 2: Core Page Workflows

**1. Catalog Deduplication Studio (`src/app/deduplication/page.tsx`)**

* **Upload Zone:** Drag-and-drop box for messy inventory CSV/XLSX dumps or MTC certificate PDFs.

* **Batch Processing Progress Bar:** Displays real-time progress while the backend processes rows through PaddleOCR, NER, and vector matching.

* **Summary Stats Card:** Quick banner showing:
* Total Items Uploaded
* Exact Matches Found (Tier-1)

* Substitute Candidates Flagged (Tier-2)

* Items Requiring Human Review (HITL Queue)

**2. Human-in-the-Loop (HITL) Triage Panel (`src/app/hitl/page.tsx`)**

* This is your most critical demo page. When ML models are between $70\%$ and $90\%$ confident, enterprise workflows require human sign-off.

* **Side-by-Side Comparison Card:**
* **Left Side (Source CPSE Item):** Raw description (e.g., `IOCL: FLG WNRF 4IN 300# A105`), owner plant, unit cost, and extracted parameters.

* **Right Side (Suggested Match):** Matched canonical item or sister CPSE part (e.g., `ONGC: FLANGE WELD NECK 4" CL300 ASTM A105`) with its confidence score.

* **Parameter Verification Badges:** Green pill badges for matching invariants (e.g., `NB: 100mm ✓`, `Class: 300 ✓`, `Material: A105 ✓`).

* **Action Buttons:**
* **"Approve & Link":** Sends verification to backend, linking the SKU in Neo4j.

* **"Reclassify":** Opens a dropdown to select a different canonical UNSPSC code.

* **"Reject (Incompatible)":** Flags the pair as incompatible.

**3. Procurement Analytics Dashboard (`src/app/dashboard/page.tsx`)**

* Executive-level summary view using clean cards:
* **Working Capital Unlocked:** Calculated estimated savings from discovering identical idle spares instead of issuing fresh purchase tenders.
* **Cross-CPSE Spare Locator Table:** Displays where idle inventory is located across sister depots (e.g., ONGC Hazira Plant having 45 units of a flange IOCL Panipat is trying to procure).
* **Taxonomy Distribution:** Bar chart showing items categorized under UNSPSC segments.

---

### Task 3: Directory Deliverables & Structure

You will work strictly inside the `frontend/` directory:

```
frontend/
├── package.json
├── tsconfig.json
├── tailwind.config.ts
├── src/
│   ├── app/
│   │   ├── layout.tsx                # App shell, persistent sidebar & navigation
│   │   ├── page.tsx                  # Redirects to /dashboard
│   │   ├── dashboard/page.tsx        # Procurement analytics overview
│   │   ├── deduplication/page.tsx    # Batch file upload and deduplication studio
│   │   └── hitl/page.tsx             # Human-in-the-loop review queue
│   │
│   ├── components/
│   │   ├── ui/                       # shadcn/ui components (Button, Card, Table, Badge)
│   │   ├── AppSidebar.tsx            # Left navigation sidebar
│   │   ├── ItemComparisonCard.tsx    # Side-by-side reconciliation comparison widget
│   │   └── UploadZone.tsx            # Drag-and-drop file ingestion element
│   │
│   └── lib/
│       ├── api.ts                    # Axios / Fetch client calling Mayank's FastAPI routes
│       ├── types.ts                  # TypeScript interfaces matching backend Pydantic models
│       └── mockData.ts               # Fallback mock data for offline UI development

```

---

### Task 4: API Client Signatures (`src/lib/api.ts`)

Connect your frontend views directly to Mayank's FastAPI endpoints:

```typescript
// src/lib/types.ts
export interface ReconciledMatch {
  sourceSku: string;
  sourceDescription: string;
  sourceCpse: "IOCL" | "ONGC" | "BPCL";
  matchedCanonicalId: string;
  matchedDescription: string;
  confidenceScore: number;
  tier: "TIER_1_IDENTICAL" | "TIER_2_SUBSTITUTE" | "TIER_3_INCOMPATIBLE";
  parameters: {
    nominalBoreMm: number;
    pressureClass: number;
    metallurgy: string;
  };
}

// src/lib/api.ts
const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export async function uploadCatalogFile(file: File) {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${BASE_URL}/ingest/upload`, { method: "POST", body: formData });
  return res.json();
}

export async function fetchHitlQueue(): Promise<ReconciledMatch[]> {
  const res = await fetch(`${BASE_URL}/match/hitl-queue`);
  return res.json();
}

export async function resolveHitlMatch(skuId: string, action: "APPROVE" | "REJECT", canonicalId?: string) {
  const res = await fetch(`${BASE_URL}/match/hitl-resolve`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ skuId, action, canonicalId }),
  });
  return res.json();
}

```

---

### Anticipated Clarifying Questions & Your Direct Answers

* **Q: "What if the backend APIs aren't ready when I start building?"**
**A:** Do not wait for the backend. Use `src/lib/mockData.ts` populated with realistic JSON objects matching the TypeScript interfaces above. You can build, test, and style the entire Next.js UI using local mock data. Once Mayank's FastAPI routes are live, simply switch the data source in `src/lib/api.ts`.
* **Q: "Do I need to build a complex 3D or dynamic canvas graph visualizer?"**
**A:** No. Complex canvas-based interactive graph visualizers often cause rendering and styling bugs during live hackathon presentations. Prioritize clean, readable tabular views, side-by-side reconciliation cards, and badge comparisons first. If time permits near the end, you can add a simple flow diagram using `reactflow`.
* **Q: "How should the UI look to impress the judges?"**
**A:** Make it look like a serious enterprise tool: clean light/dark slate backgrounds, sharp borders, high-contrast badges (green for `Identical`, amber for `Substitute`, red for `Incompatible`), and clear typography. Avoid overly flashy transitions; speed, clarity, and scannability are what procurement judges value.
