export interface CPSEDepot {
  id: string;
  name: string;
  cpse: 'IOCL' | 'BPCL' | 'HPCL' | 'ONGC' | 'GAIL';
  city: string;
  state: string;
  coords: { x: number; y: number }; // normalized SVG map coordinates [0..100]
  itemsCount: number;
  unlockedValueCr: number;
}

export const CPSE_DEPOTS: CPSEDepot[] = [
  { id: 'depot-1', name: 'IOCL Panipat Refinery', cpse: 'IOCL', city: 'Panipat', state: 'Haryana', coords: { x: 38, y: 25 }, itemsCount: 412, unlockedValueCr: 14.2 },
  { id: 'depot-2', name: 'BPCL Mumbai Refinery', cpse: 'BPCL', city: 'Mumbai', state: 'Maharashtra', coords: { x: 25, y: 58 }, itemsCount: 328, unlockedValueCr: 11.5 },
  { id: 'depot-3', name: 'HPCL Visakh Refinery', cpse: 'HPCL', city: 'Visakhapatnam', state: 'Andhra Pradesh', coords: { x: 68, y: 62 }, itemsCount: 285, unlockedValueCr: 9.8 },
  { id: 'depot-4', name: 'ONGC Uran Gas Terminal', cpse: 'ONGC', city: 'Uran', state: 'Maharashtra', coords: { x: 27, y: 60 }, itemsCount: 198, unlockedValueCr: 7.4 },
  { id: 'depot-5', name: 'GAIL Pata Petrochemical', cpse: 'GAIL', city: 'Auraiya', state: 'Uttar Pradesh', coords: { x: 48, y: 35 }, itemsCount: 197, unlockedValueCr: 5.7 },
];

export const STATUS_COLORS: Record<string, string> = {
  'TO_BE_CONSUMED': 'bg-blue-100 text-blue-800',
  'IN_STORAGE': 'bg-slate-100 text-slate-800',
  'IDLE_SURPLUS': 'bg-emerald-100 text-emerald-800',
  'ARCHIVED': 'bg-gray-100 text-gray-800',
};

export const TIER_LABELS: Record<number, string> = {
  1: 'Exact Match',
  2: 'Alternative Acceptable',
  3: 'Not Recommended',
};
