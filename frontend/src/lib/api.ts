const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api/v1';

async function fetchAPI<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const isFormData = typeof FormData !== 'undefined' && options.body instanceof FormData;
  const headers: Record<string, string> = {};
  if (!isFormData) {
    headers['Content-Type'] = 'application/json';
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers: {
      ...headers,
      ...(options.headers as Record<string, string>),
    },
  });

  if (!response.ok) {
    let errorDetail = response.statusText;
    try {
      const errJson = await response.json();
      errorDetail = errJson.detail || errorDetail;
    } catch {
      // Ignore text parse failure
    }
    throw new Error(`API Error ${response.status}: ${errorDetail}`);
  }

  return response.json();
}

export const api = {
  // Inventory & Stock Ledger
  getInventory: (params?: { cpse?: string; status?: string; item_type?: string }) => {
    const query = new URLSearchParams(params as Record<string, string>).toString();
    return fetchAPI<any>(`/inventory${query ? `?${query}` : ''}`);
  },
  getInventoryItem: (skuCode: string) => fetchAPI<any>(`/inventory/${skuCode}`),
  getSurplusRadar: () => fetchAPI<any[]>('/inventory/surplus'),
  getHitlQueue: () => fetchAPI<any[]>('/inventory/hitl-queue'),
  updateItemStatus: (skuCode: string, payload: { status: string; reason?: string; officer?: string }) =>
    fetchAPI<any>(`/inventory/${skuCode}/status`, {
      method: 'PUT',
      body: JSON.stringify(payload),
    }),

  // Requisitions & Consignments
  getRequests: (cpse?: string) =>
    fetchAPI<any[]>(`/requisition${cpse ? `?cpse=${cpse}` : ''}`),
  getRequestById: (reqId: string) => fetchAPI<any>(`/requisition/${reqId}`),
  postRequisition: (data: any, idempotencyKey?: string) =>
    fetchAPI<any>('/requisition', {
      method: 'POST',
      body: JSON.stringify(data),
      headers: idempotencyKey ? { 'Idempotency-Key': idempotencyKey } : {},
    }),
  approveRequisition: (reqId: string, payload: { approved_by: string }) =>
    fetchAPI<any>(`/requisition/${reqId}/approve`, {
      method: 'PUT',
      body: JSON.stringify(payload),
    }),
  rejectRequisition: (reqId: string, payload: { reason: string }) =>
    fetchAPI<any>(`/requisition/${reqId}/reject`, {
      method: 'PUT',
      body: JSON.stringify(payload),
    }),
  generateGatePass: (reqId: string, payload: any) =>
    fetchAPI<any>(`/requisition/${reqId}/gatepass`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  dispatchRequisition: (reqId: string) =>
    fetchAPI<any>(`/requisition/${reqId}/dispatch`, { method: 'PUT' }),
  deliverRequisition: (reqId: string) =>
    fetchAPI<any>(`/requisition/${reqId}/deliver`, { method: 'PUT' }),

  // Sovereign Audit Ledger
  getAuditLogs: (category?: string, cpse?: string) => {
    const query = new URLSearchParams();
    if (category) query.append('category', category);
    if (cpse) query.append('cpse', cpse);
    const qs = query.toString();
    return fetchAPI<any>(`/audit${qs ? `?${qs}` : ''}`);
  },
  verifyAuditChain: () => fetchAPI<any>('/audit/verify', { method: 'POST' }),
  getAuditEntry: (logId: string) => fetchAPI<any>(`/audit/${logId}`),

  // Pre-Purchase Radar & Graph
  discoverSurplus: (itemType?: string, maxDistanceKm?: number) => {
    const query = new URLSearchParams();
    if (itemType) query.append('item_type', itemType);
    if (maxDistanceKm) query.append('max_distance_km', maxDistanceKm.toString());
    const qs = query.toString();
    return fetchAPI<any>(`/graph/discover${qs ? `?${qs}` : ''}`);
  },
  getRouteLogistics: (sourceDepot: string, targetDepot: string) =>
    fetchAPI<any>(`/graph/logistics/${encodeURIComponent(sourceDepot)}/${encodeURIComponent(targetDepot)}`),

  // Matching & Compatibility Core
  searchMatches: (payload: { query_text: string; item_type?: string; properties?: any }) =>
    fetchAPI<any>('/match/search', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  runBenchmark: () => fetchAPI<any>('/match/benchmark'),

  // Document & Catalog Ingestion
  uploadDocument: (formData: FormData) =>
    fetchAPI<any>('/ingest/document', {
      method: 'POST',
      body: formData,
    }),
  uploadCatalog: (formData: FormData) =>
    fetchAPI<any>('/ingest/catalog', {
      method: 'POST',
      body: formData,
    }),
  listDocuments: (skip: number = 0, limit: number = 20) =>
    fetchAPI<any>(`/ingest/documents?skip=${skip}&limit=${limit}`),
  getDocumentById: (docId: number) => fetchAPI<any>(`/ingest/documents/${docId}`),
};
