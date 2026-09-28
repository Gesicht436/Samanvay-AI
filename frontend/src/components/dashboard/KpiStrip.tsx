import React from 'react';
import { Package, Radio, Building2, CheckCircle2, AlertTriangle, ShieldAlert } from 'lucide-react';
import { KpiCard, Skeleton } from '@/components/ui';

interface KpiStripProps {
  stats: {
    total_items?: number;
    total_surplus?: number;
    total_hitl?: number;
    total_requisitions?: number;
    capital_unlocked_cr?: number;
  } | null;
  auditVerified: boolean | null;
  loading: boolean;
}

export function KpiStrip({ stats, auditVerified, loading }: KpiStripProps) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
      <KpiCard
        title="Total Mesh Items"
        value={loading ? <Skeleton className="h-7 w-20" /> : (stats?.total_items?.toLocaleString() ?? '—')}
        subtext="Live PostgreSQL Catalog"
        icon={Package}
      />
      <KpiCard
        title="Active Surplus Spares"
        value={loading ? <Skeleton className="h-7 w-20" /> : (stats?.total_surplus?.toLocaleString() ?? '—')}
        subtext="Ready for Inter-CPSE Loan"
        icon={Radio}
        delta={stats?.total_surplus ? `${stats.total_surplus} available` : undefined}
        deltaType="positive"
      />
      <KpiCard
        title="Capital Unlocked"
        value={
          loading ? (
            <Skeleton className="h-7 w-24" />
          ) : stats?.capital_unlocked_cr !== undefined ? (
            `₹${stats.capital_unlocked_cr.toFixed(1)} Cr`
          ) : (
            '—'
          )
        }
        subtext="Idle Inventory Mobilized"
        icon={Building2}
        delta="Sovereign mesh"
        deltaType="positive"
      />
      <KpiCard
        title="HITL Review Queue"
        value={
          loading ? (
            <Skeleton className="h-7 w-16" />
          ) : (
            stats?.total_hitl?.toString() ?? '0'
          )
        }
        subtext="Flagged for Engineering Review"
        icon={ShieldAlert}
        delta={stats?.total_hitl ? `${stats.total_hitl} pending` : 'Clean'}
        deltaType={stats?.total_hitl && stats.total_hitl > 0 ? 'warning' : 'positive'}
      />
      <KpiCard
        title="Merkle Audit Ledger"
        value={
          loading ? (
            <Skeleton className="h-7 w-24" />
          ) : auditVerified ? (
            'SHA-256 Valid'
          ) : auditVerified === false ? (
            'Tamper Detected'
          ) : (
            'Verifying...'
          )
        }
        subtext="Tamper-Evident Chain"
        icon={auditVerified === false ? AlertTriangle : CheckCircle2}
        delta={auditVerified ? '100% Sealed' : undefined}
        deltaType={auditVerified ? 'positive' : 'negative'}
      />
    </div>
  );
}
