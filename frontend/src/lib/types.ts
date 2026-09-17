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
