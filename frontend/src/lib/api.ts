import { User, SeedUser, CsrfTokenResponse } from './types';

function resolveApiBaseUrl(): string {
  if (typeof window !== 'undefined') {
    // In browser: use relative /api/v1 so Next.js proxies it seamlessly across any domain or tunnel
    const configured = process.env.NEXT_PUBLIC_API_BASE_URL || process.env.NEXT_PUBLIC_API_URL;
    if (!configured || configured.includes('localhost:8000') || configured.includes('127.0.0.1:8000')) {
      return '/api/v1';
    }
    return configured.endsWith('/api/v1') ? configured : `${configured.replace(/\/+$/, '')}/api/v1`;
  }
  // Server-side (SSR / Server Actions / Docker container)
  const serverBackend =
    process.env.INTERNAL_BACKEND_URL ||
    process.env.NEXT_PUBLIC_API_BASE_URL ||
    process.env.NEXT_PUBLIC_API_URL ||
    'http://samanvay-ai-backend:8000';
  return serverBackend.endsWith('/api/v1') ? serverBackend : `${serverBackend.replace(/\/+$/, '')}/api/v1`;
}

const API_BASE_URL = resolveApiBaseUrl();

// ── AUTH-006 session-cookie foundation (Phase 1) ─────────────────────────────
// Authentication state lives in the server-side session (HttpOnly cookie).
// This module keeps the session-bound CSRF synchronizer token in memory ONLY.
// It is never written to localStorage/sessionStorage, never logged, and never
// persisted. No JWT/Bearer handling exists anywhere in this module.
let sessionCsrfToken: string | null = null;

export function setSessionCsrfToken(token: string | null): void {
  sessionCsrfToken = token;
}

export function clearSessionCsrfToken(): void {
  sessionCsrfToken = null;
}

// Mid-session 401 notification. AuthProvider registers a handler so a stale
// in-memory identity (and its CSRF token) is cleared whenever the server
// rejects the session with 401 on any request except the login attempt
// itself, whose 401 is a credential error owned by the login flow. The
// callback-registration pattern keeps this module free of a circular import
// of the AuthContext. Handlers must be idempotent; they perform no
// navigation, so concurrent 401 responses cannot create redirect loops.
let unauthorizedHandler: (() => void) | null = null;

export function setUnauthorizedHandler(handler: (() => void) | null): void {
  unauthorizedHandler = handler;
}

function isUnsafeMethod(method?: string): boolean {
  const m = (method || 'GET').toUpperCase();
  return m === 'POST' || m === 'PUT' || m === 'PATCH' || m === 'DELETE';
}

export class ApiError extends Error {
  status: number;
  constructor(status: number, detail: string) {
    super(`API Error ${status}: ${detail}`);
    this.name = 'ApiError';
    this.status = status;
  }
}

export function isAuthenticationFailure(err: unknown): boolean {
  return err instanceof ApiError && err.status === 401;
}

async function fetchAPI<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const isFormData = typeof FormData !== 'undefined' && options.body instanceof FormData;
  const headers: Record<string, string> = {};
  if (!isFormData) {
    headers['Content-Type'] = 'application/json';
  }

  // Unsafe requests carry the in-memory CSRF token when a session holds one.
  // The login request has no token yet and is sent without it.
  const method = (options.method || 'GET').toUpperCase();
  if (isUnsafeMethod(method) && sessionCsrfToken) {
    headers['X-CSRF-Token'] = sessionCsrfToken;
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    credentials: 'include',
    headers: {
      ...headers,
      ...(options.headers as Record<string, string>),
    },
  });

  // Empty success responses (e.g. 204 from POST /auth/logout) carry no body.
  if (response.status === 204) {
    return undefined as T;
  }

  if (!response.ok) {
    let errorDetail: string = response.statusText;
    try {
      const errJson = await response.json();
      const rawDetail = errJson.detail || errorDetail;
      errorDetail = typeof rawDetail === 'string' ? rawDetail : JSON.stringify(rawDetail);
    } catch {
      // Ignore text parse failure
    }
    // Mid-session 401: notify the registered handler (AuthProvider) so the
    // stale in-memory identity and CSRF token are cleared. The login
    // request's own 401 is a credential error and never triggers it.
    // Network failures never reach this branch, and 403 CSRF/Origin
    // failures deliberately do not sign the user out.
    if (response.status === 401 && endpoint !== '/auth/login' && unauthorizedHandler) {
      try {
        unauthorizedHandler();
      } catch {
        // A handler failure must never mask the original API error.
      }
    }
    throw new ApiError(response.status, errorDetail);
  }

  return response.json();
}

export const api = {
  // Inventory & Stock Ledger
  getInventory: (params?: { cpse?: string; depot?: string; status?: string; category?: string; item_type?: string; skip?: number; limit?: number }) => {
    const query = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([k, v]) => {
        if (v !== undefined && v !== null && v !== '' && v !== 'ALL') {
          query.append(k, String(v));
        }
      });
    }
    const qs = query.toString();
    return fetchAPI<any>(`/inventory${qs ? `?${qs}` : ''}`);
  },
  getInventoryStats: () => fetchAPI<any>('/inventory/stats'),
  getInventoryItem: (skuCode: string) => fetchAPI<any>(`/inventory/${skuCode}`),
  getSurplusRadar: () => fetchAPI<any[]>('/inventory/surplus'),
  getHitlQueue: () => fetchAPI<any[]>('/inventory/hitl-queue'),
  updateItemStatus: (skuCode: string, payload: { status: string; reason?: string; officer?: string }) =>
    fetchAPI<any>(`/inventory/${skuCode}/status`, {
      method: 'PUT',
      body: JSON.stringify(payload),
    }),
  createInventoryItem: (data: any) =>
    fetchAPI<any>('/inventory', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  // Requisitions & Consignments
  getRequests: (params?: string | { cpse?: string; depot?: string }) => {
    if (typeof params === 'string') {
      return fetchAPI<any[]>(`/requisition${params && params !== 'ALL' ? `?cpse=${params}` : ''}`);
    }
    const query = new URLSearchParams();
    if (params?.cpse && params.cpse !== 'ALL') query.append('cpse', params.cpse);
    if (params?.depot && params.depot !== 'ALL') query.append('depot', params.depot);
    const qs = query.toString();
    return fetchAPI<any[]>(`/requisition${qs ? `?${qs}` : ''}`);
  },
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
  getAuditLogs: (params?: { category?: string; cpse?: string; skip?: number; limit?: number }) => {
    const query = new URLSearchParams();
    if (params) {
      if (params.category && params.category !== 'ALL') query.append('category', params.category);
      if (params.cpse && params.cpse !== 'ALL') query.append('cpse', params.cpse);
      if (params.skip !== undefined) query.append('skip', String(params.skip));
      if (params.limit !== undefined) query.append('limit', String(params.limit));
    }
    const qs = query.toString();
    return fetchAPI<any>(`/audit${qs ? `?${qs}` : ''}`);
  },
  verifyAuditChain: () => fetchAPI<any>('/audit/verify', { method: 'POST' }),
  getAuditEntry: (logId: string) => fetchAPI<any>(`/audit/${logId}`),

  // Pre-Purchase Radar & Graph
  getTopology: () => fetchAPI<any>('/graph/topology'),
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
  searchMatches: (payload: {
    query_text?: string;
    item_type?: string;
    size_nb_mm?: number;
    pressure_class?: number;
    pressure_rating_bar?: number;
    pressure_rating_psi?: number;
    schedule?: string;
    metallurgy?: string;
    weldability_class?: string;
    sour_service?: boolean;
    facing_end?: string;
    attachment?: string;
    mfg_method?: string;
    standard?: string;
    indian_standard?: string;
    oil_std_spec?: string;
    severe_cyclic?: boolean;
    trim_no?: number;
    port_bore?: string;
    piggable?: boolean;
    fire_safe_required?: boolean;
    min_local_content_pct?: number;
    properties?: Record<string, any>;
  }) =>
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

  // Sovereign Authentication & Access Control (AUTH-006 session-cookie contract).
  // The server owns the session: login sets the HttpOnly cookie and returns the
  // user profile (no access_token). Identity is established via /auth/me and
  // unsafe requests are CSRF-verified with the memory-only token.
  login: (payload: { username: string; password: string }) =>
    fetchAPI<User>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  getCsrfToken: async () => {
    const data = await fetchAPI<CsrfTokenResponse>('/auth/csrf');
    setSessionCsrfToken(data.csrf_token);
    return data;
  },
  logout: () =>
    fetchAPI<void>('/auth/logout', {
      method: 'POST',
    }),
  getMe: () => fetchAPI<User>('/auth/me'),
  getSeedUsers: () => fetchAPI<{ users: SeedUser[] }>('/auth/seed-users'),

  getUsers: () => fetchAPI<User[]>('/auth/users'),
  approveUser: (userId: number) => fetchAPI<User>(`/auth/users/${userId}/approve`, { method: 'POST' }),
  rejectUser: (userId: number) => fetchAPI<{ status: string }>(`/auth/users/${userId}/reject`, { method: 'POST' }),
};
