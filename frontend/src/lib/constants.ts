export interface CPSEDepot {
  id: string;
  name: string;
  cpse: 'OIL' | 'NRL' | 'IOCL' | 'BPCL' | 'HPCL' | 'ONGC' | 'GAIL';
  city: string;
  state: string;
}

export const CPSE_DEPOTS: CPSEDepot[] = [
  { id: 'depot-oil-1', name: 'OIL Central Materials Warehouse, Duliajan', cpse: 'OIL', city: 'Duliajan', state: 'Assam' },
  { id: 'depot-oil-2', name: 'OIL Moran Supply Base, Charaideo', cpse: 'OIL', city: 'Moran', state: 'Assam' },
  { id: 'depot-nrl-1', name: 'NRL Numaligarh Refinery Yard', cpse: 'NRL', city: 'Golaghat', state: 'Assam' },
  { id: 'depot-ongc-naz', name: 'ONGC Assam Asset Base, Nazira', cpse: 'ONGC', city: 'Nazira', state: 'Assam' },
  { id: 'depot-oil-gau', name: 'OIL Guwahati Pipeline HQ', cpse: 'OIL', city: 'Guwahati', state: 'Assam' },
  { id: 'depot-1', name: 'IOCL Panipat Refinery', cpse: 'IOCL', city: 'Panipat', state: 'Haryana' },
  { id: 'depot-2', name: 'BPCL Mumbai Refinery', cpse: 'BPCL', city: 'Mumbai', state: 'Maharashtra' },
  { id: 'depot-3', name: 'HPCL Visakh Refinery', cpse: 'HPCL', city: 'Visakhapatnam', state: 'Andhra Pradesh' },
  { id: 'depot-4', name: 'ONGC Uran Gas Terminal', cpse: 'ONGC', city: 'Uran', state: 'Maharashtra' },
  { id: 'depot-5', name: 'GAIL Pata Petrochemical', cpse: 'GAIL', city: 'Auraiya', state: 'Uttar Pradesh' },
  { id: 'depot-oil-jod', name: 'OIL Jodhpur Heavy Oil Project Base', cpse: 'OIL', city: 'Jodhpur', state: 'Rajasthan' },
  { id: 'depot-oil-kak', name: 'OIL KG Basin Offshore Supply Depot', cpse: 'OIL', city: 'Kakinada', state: 'Andhra Pradesh' },
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
