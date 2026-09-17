export const CPSE_DEPOTS = [
  { id: 'depot-1', name: 'IOCL Panipat Refinery' },
  { id: 'depot-2', name: 'BPCL Mumbai Refinery' },
  { id: 'depot-3', name: 'HPCL Visakh Refinery' },
  // 19 Depots logic goes here
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
