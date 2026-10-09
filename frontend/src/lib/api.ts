import type {
  DashboardSummary,
  HitlResolution,
  IngestResponse,
  IngestResult,
  MatchResult,
  ReviewQueueItem,
} from "./types";

const baseUrl =
  process.env.NEXT_PUBLIC_API_URL ??
  (typeof window === "undefined"
    ? "http://localhost:8000"
    : `${window.location.protocol}//${window.location.hostname}:8000`);

async function parseApiResponse<T>(response: Response, fallback: string): Promise<T> {
  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    throw new Error(payload?.detail ?? `${fallback} (${response.status})`);
  }
  return response.json();
}

export async function submitDocumentForOcr(file: File): Promise<IngestResult> {
  const form = new FormData();
  form.append("file", file);
  const response = await fetch(`${baseUrl}/v1/ingest/document`, {
    method: "POST",
    body: form,
    cache: "no-store",
  });
  return parseApiResponse(response, "Document processing failed");
}

export async function submitTextForParsing(rawText: string): Promise<IngestResult> {
  const response = await fetch(`${baseUrl}/v1/ingest/text`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ raw_text: rawText }),
    cache: "no-store",
  });
  return parseApiResponse(response, "Text parsing failed");
}

export async function matchDescription(
  raw_description: string,
  top_k = 5,
): Promise<MatchResult | null> {
  const response = await fetch(`${baseUrl}/v1/match`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ raw_description, top_k, rerank: true }),
    cache: "no-store",
  });
  return parseApiResponse(response, "Matching failed");
}

export async function getHitlQueue(): Promise<ReviewQueueItem[]> {
  const response = await fetch(`${baseUrl}/v1/match/hitl-queue`, { cache: "no-store" });
  const payload = await parseApiResponse<{ items: ReviewQueueItem[] }>(
    response,
    "Unable to load review queue",
  );
  return payload.items;
}

export async function resolveHitlItem(
  itemId: string,
  accepted: boolean,
  correctedCandidate?: string,
): Promise<HitlResolution> {
  const response = await fetch(`${baseUrl}/v1/match/hitl-resolve`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      item_id: itemId,
      accepted,
      corrected_candidate: correctedCandidate?.trim() || null,
    }),
    cache: "no-store",
  });
  return parseApiResponse(response, "Unable to save review decision");
}

export async function getHitlTrainingExamples(): Promise<HitlResolution["training_example"][]> {
  const response = await fetch(`${baseUrl}/v1/match/hitl-training-examples`, {
    cache: "no-store",
  });
  const payload = await parseApiResponse<{ items: HitlResolution["training_example"][] }>(
    response,
    "Unable to load feedback examples",
  );
  return payload.items;
}

export async function getDashboardSummary(): Promise<DashboardSummary> {
  const response = await fetch(`${baseUrl}/v1/dashboard/summary`, { cache: "no-store" });
  return parseApiResponse(response, "Unable to load dashboard");
}

export async function ingestDocument(file: File): Promise<IngestResponse> {
  const body = new FormData();
  body.append("file", file);
  const response = await fetch(`${baseUrl}/v1/ingest/document`, {
    method: "POST",
    body,
    cache: "no-store",
  });
  return parseApiResponse(response, "Document ingest failed");
}
