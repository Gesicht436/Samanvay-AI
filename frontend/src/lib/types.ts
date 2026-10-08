export interface PhysicalAttributes {
  weight_kg: number;
  dimensions_cm: string;
  condition: string;
}

export interface DynamicCompatibilityTier {
  tier: number;
  description: string;
}

export interface PropertyScorecard {
  property: string;
  score: number;
  details: string;
}

export interface InventoryItemResponse {
  id: string;
  name: string;
  description: string;
  status: string;
  quantity: number;
  attributes: PhysicalAttributes;
  compatibility_tier?: DynamicCompatibilityTier;
  scorecard?: PropertyScorecard[];
}

export interface RequisitionCreateRequest {
  item_id: string;
  quantity: number;
  reason: string;
}

export interface AuditLogEntry {
  id: string;
  action: string;
  timestamp: string;
  user_id: string;
  details: string;
}

export interface User {
  id: number;
  username: string;
  full_name: string;
  email?: string;
  role: string;
  cpse: string;
  depot_id: string;
  is_active: boolean;
  is_approved: boolean;
}

export interface SeedUser {
  username: string;
  full_name: string;
  role: string;
  cpse: string;
  depot_id: string;
  email: string;
  description: string;
}

// AUTH-006 session-cookie contract: the backend login endpoint sets the
// HttpOnly session cookie and returns the user profile directly. There is no
// access_token. Authenticated identity is represented by the User profile
// fetched from the server session (GET /auth/me).
export interface CsrfTokenResponse {
  csrf_token: string;
}


