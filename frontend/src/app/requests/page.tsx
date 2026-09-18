"use client";

import React, { useState, useMemo } from 'react';
import Link from 'next/link';
import { Card, KpiCard, StatusBadge } from '@/components/ui';
import {
  Truck,
  Inbox,
  Clock,
  ShieldCheck,
  Search,
  Filter,
  CheckCircle2,
  XCircle,
  ArrowRight,
  AlertTriangle,
  FileText,
  MapPin,
  ExternalLink,
  ChevronRight,
  PackageCheck,
  Sparkles,
  Building2,
} from 'lucide-react';
import { CPSE_DEPOTS } from '@/lib/constants';

interface InboundRequest {
  id: string;
  requester_cpse: 'ONGC' | 'BPCL' | 'HPCL' | 'GAIL';
  requester_facility: string;
  requester_officer: string;
  urgency: 'EMERGENCY' | 'STANDARD';
  sla_hours_remaining: number;
  part_name: string;
  sku_code: string;
  category: string;
  metallurgy: string;
  pressure_class: string;
  size: string;
  quantity: number;
  unit: string;
  available_stock: number;
  compatibility_score: number;
  distance_km: number;
  transit_hours: number;
  submitted_time: string;
  status: 'PENDING_CONFIRMATION' | 'APPROVED' | 'DECLINED';
  gate_pass_id?: string;
}

interface ConsignmentItem {
  id: string;
  direction: 'OUTBOUND' | 'INBOUND';
  source_cpse: string;
  destination_cpse: string;
  destination_facility: string;
  material_title: string;
  sku_code: string;
  quantity: number;
  unit: string;
  urgency: 'EMERGENCY' | 'STANDARD';
  status: 'DRAFT' | 'APPROVED' | 'GATE_PASS_ISSUED' | 'DISPATCHED' | 'IN_TRANSIT' | 'DELIVERED';
  progress_pct: number;
  carrier_name: string;
  vehicle_reg: string;
  current_location: string;
  dispatched_at: string;
  eta: string;
}

const INITIAL_INBOUND: InboundRequest[] = [
  {
    id: 'REQ-99201',
    requester_cpse: 'ONGC',
    requester_facility: 'ONGC Uran Gas Processing Complex, MH',
    requester_officer: 'S. K. Verma, Chief Maintenance Supt.',
    urgency: 'EMERGENCY',
    sla_hours_remaining: 3.5,
    part_name: 'Weld Neck Flange 4" Class 300 RF SCH 40',
    sku_code: 'PRT-8892',
    category: 'FLANGE',
    metallurgy: 'ASTM A105 (Heat HT-2025-20300)',
    pressure_class: '300#',
    size: '100 mm (4")',
    quantity: 2,
    unit: 'EA',
    available_stock: 12,
    compatibility_score: 99.4,
    distance_km: 1380,
    transit_hours: 28,
    submitted_time: '2 hours ago',
    status: 'PENDING_CONFIRMATION',
  },
  {
    id: 'REQ-99208',
    requester_cpse: 'BPCL',
    requester_facility: 'BPCL Mumbai Refinery, Mahul',
    requester_officer: 'R. Ramachandran, Materials Manager',
    urgency: 'STANDARD',
    sla_hours_remaining: 24,
    part_name: 'Globe Valve 2" Class 150 RF Bolted Bonnet',
    sku_code: 'PRT-8893',
    category: 'VALVE',
    metallurgy: 'ASTM A182 F316 (Heat HT-SS-9912)',
    pressure_class: '150#',
    size: '50 mm (2")',
    quantity: 1,
    unit: 'EA',
    available_stock: 4,
    compatibility_score: 100.0,
    distance_km: 1410,
    transit_hours: 30,
    submitted_time: '5 hours ago',
    status: 'PENDING_CONFIRMATION',
  },
];

const INITIAL_CONSIGNMENTS: ConsignmentItem[] = [
  {
    id: 'REQ-55102',
    direction: 'OUTBOUND',
    source_cpse: 'IOCL Panipat Depot',
    destination_cpse: 'HPCL',
    destination_facility: 'HPCL Visakh Refinery (VRMP Unit)',
    material_title: 'Gas Turbine Rotor Assy (PRT-5512)',
    sku_code: 'PRT-5512',
    quantity: 1,
    unit: 'EA',
    urgency: 'EMERGENCY',
    status: 'IN_TRANSIT',
    progress_pct: 68,
    carrier_name: 'CONCOR Special Multi-Axle Heavy Logistics',
    vehicle_reg: 'HR-06-EA-8841',
    current_location: 'NH-16 near Rajahmundry Waypoint',
    dispatched_at: '2026-03-17 14:00 IST',
    eta: 'Tomorrow, 06:30 IST',
  },
  {
    id: 'REQ-44810',
    direction: 'OUTBOUND',
    source_cpse: 'IOCL Panipat Depot',
    destination_cpse: 'GAIL',
    destination_facility: 'GAIL Pata Petrochemical Complex',
    material_title: 'Gate Valve 6" Class 600# RTJ Cryo (A350 LF2)',
    sku_code: 'PRT-9014',
    quantity: 6,
    unit: 'EA',
    urgency: 'STANDARD',
    status: 'DISPATCHED',
    progress_pct: 25,
    carrier_name: 'VRL Logistics Heavy Freight Fleet',
    vehicle_reg: 'UP-75-BT-1092',
    current_location: 'Yamuna Expressway Mile 84 (Mathura)',
    dispatched_at: '2026-03-18 11:30 IST',
    eta: 'Tonight, 22:00 IST',
  },
  {
    id: 'REQ-33190',
    direction: 'INBOUND',
    source_cpse: 'BPCL Mumbai Refinery',
    destination_cpse: 'IOCL',
    destination_facility: 'IOCL Panipat Refinery Depot',
    material_title: 'Seamless Pipe 6" SCH 80 BE API 5L PSL 2',
    sku_code: 'PRT-7721',
    quantity: 48,
    unit: 'MTR',
    urgency: 'STANDARD',
    status: 'DELIVERED',
    progress_pct: 100,
    carrier_name: 'Container Corporation of India Rail Freight',
    vehicle_reg: 'CONCOR-CR-4409',
    current_location: 'IOCL Panipat Rail Siding In-Gate',
    dispatched_at: '2026-03-14 08:00 IST',
    eta: 'Delivered & Staged',
  },
];

export default function RequestsPage() {
  const [activeTab, setActiveTab] = useState<'ALL' | 'INBOUND' | 'CONSIGNMENTS' | 'FULFILLED'>('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [urgencyFilter, setUrgencyFilter] = useState<'ALL' | 'EMERGENCY' | 'STANDARD'>('ALL');
  const [inboundList, setInboundList] = useState<InboundRequest[]>(INITIAL_INBOUND);
  const [consignments, setConsignments] = useState<ConsignmentItem[]>(INITIAL_CONSIGNMENTS);
  const [actionNotice, setActionNotice] = useState<string | null>(null);

  const handleConfirmSupply = (reqId: string) => {
    setInboundList(prev =>
      prev.map(item => {
        if (item.id === reqId) {
          const passId = `GP-NR-${item.id.replace('REQ-', '')}`;
          return { ...item, status: 'APPROVED', gate_pass_id: passId };
        }
        return item;
      })
    );

    const target = inboundList.find(i => i.id === reqId);
    if (target) {
      const newConsignment: ConsignmentItem = {
        id: target.id,
        direction: 'OUTBOUND',
        source_cpse: 'IOCL Panipat Depot',
        destination_cpse: target.requester_cpse,
        destination_facility: target.requester_facility,
        material_title: `${target.part_name} (${target.sku_code})`,
        sku_code: target.sku_code,
        quantity: target.quantity,
        unit: target.unit,
        urgency: target.urgency,
        status: 'GATE_PASS_ISSUED',
        progress_pct: 15,
        carrier_name: 'MoPNG Rapid Inter-Depot Transit Carrier',
        vehicle_reg: 'DL-01-AX-9912 (Assigned)',
        current_location: 'IOCL Panipat Out-Gate Inspection Bay',
        dispatched_at: 'Pending CISF Gate Scan',
        eta: `Estimated +${target.transit_hours} hrs`,
      };
      setConsignments(prev => [newConsignment, ...prev]);
      setActionNotice(`Supply confirmed for ${reqId}. CISF Gate Pass GP-NR-${target.id.replace('REQ-', '')} issued and cryptographic seal anchored to Sovereign Ledger.`);
      setTimeout(() => setActionNotice(null), 8000);
    }
  };

  const handleDecline = (reqId: string) => {
    setInboundList(prev =>
      prev.map(item => (item.id === reqId ? { ...item, status: 'DECLINED' } : item))
    );
    setActionNotice(`Requisition ${reqId} marked as Declined. Reason: Critical local inventory reserve limit.`);
    setTimeout(() => setActionNotice(null), 6000);
  };

  const filteredInbound = useMemo(() => {
    return inboundList.filter(item => {
      const matchesSearch =
        item.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
        item.part_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        item.requester_cpse.toLowerCase().includes(searchQuery.toLowerCase());
      const matchesUrgency = urgencyFilter === 'ALL' || item.urgency === urgencyFilter;
      return matchesSearch && matchesUrgency;
    });
  }, [inboundList, searchQuery, urgencyFilter]);

  const filteredConsignments = useMemo(() => {
    return consignments.filter(item => {
      const matchesSearch =
        item.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
        item.material_title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        item.destination_facility.toLowerCase().includes(searchQuery.toLowerCase());
      const matchesUrgency = urgencyFilter === 'ALL' || item.urgency === urgencyFilter;
      if (activeTab === 'CONSIGNMENTS') {
        return matchesSearch && matchesUrgency && item.status !== 'DELIVERED';
      }
      if (activeTab === 'FULFILLED') {
        return matchesSearch && matchesUrgency && item.status === 'DELIVERED';
      }
      return matchesSearch && matchesUrgency;
    });
  }, [consignments, searchQuery, urgencyFilter, activeTab]);

  const pendingCount = inboundList.filter(i => i.status === 'PENDING_CONFIRMATION').length;
  const activeConsignmentsCount = consignments.filter(c => c.status !== 'DELIVERED').length;

  return (
    <div className="max-w-7xl mx-auto space-y-6 pb-12">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <h1 className="text-2xl font-bold font-mono tracking-tight text-slate-900 dark:text-white">
              Requisition Hub & Consignments
            </h1>
            <span className="px-2 py-0.5 text-xs font-mono font-semibold bg-blue-50 dark:bg-blue-950/60 text-blue-700 dark:text-blue-300 border border-blue-200 dark:border-blue-900 rounded">
              Depot: IOCL Panipat
            </span>
          </div>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Cross-CPSE inter-depot requisitioning, CISF gate pass generation, and real-time transit tracking
          </p>
        </div>
      </div>

      {/* Action Notice Alert */}
      {actionNotice && (
        <div className="p-4 bg-emerald-50 dark:bg-emerald-950/50 border border-emerald-300 dark:border-emerald-800 text-emerald-800 dark:text-emerald-200 rounded-lg flex items-center justify-between animate-fadeIn text-sm">
          <div className="flex items-center gap-2">
            <CheckCircle2 size={18} className="text-emerald-600 shrink-0" />
            <span>{actionNotice}</span>
          </div>
          <button
            onClick={() => setActionNotice(null)}
            className="text-xs font-bold uppercase hover:underline ml-4"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Top 4 KPI Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <KpiCard
          label="Active In-Transit"
          value={`${activeConsignmentsCount} Consignments`}
          subtext="2 multi-axle • 1 rail container"
          delta="100% on-schedule"
          deltaType="positive"
          icon={<Truck size={20} />}
        />
        <KpiCard
          label="Inbound Action Req."
          value={`${pendingCount} Pending`}
          subtext="1 Emergency breakdown SLA"
          delta="Avg SLA 4.2h"
          deltaType="warning"
          icon={<Inbox size={20} />}
        />
        <KpiCard
          label="Avg Dispatch SLA"
          value="4.8 Hours"
          subtext="From req approval to out-gate"
          delta="32% faster than target"
          deltaType="positive"
          icon={<Clock size={20} />}
        />
        <KpiCard
          label="CISF Passes Cleared"
          value="142 Passes"
          subtext="100% SHA-256 sealed & verified"
          delta="Zero gate discrepancies"
          deltaType="positive"
          icon={<ShieldCheck size={20} />}
        />
      </div>

      {/* Filter and Tab Navigation Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 border-b border-slate-200 dark:border-slate-800 pb-3">
        <div className="flex items-center gap-1 overflow-x-auto">
          <button
            onClick={() => setActiveTab('ALL')}
            className={`px-3 py-1.5 rounded text-xs font-mono font-semibold transition-colors flex items-center gap-2 whitespace-nowrap ${
              activeTab === 'ALL'
                ? 'bg-slate-900 text-white dark:bg-white dark:text-slate-950'
                : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800'
            }`}
          >
            All Movements
            <span className="px-1.5 py-0.2 text-[10px] rounded-full bg-slate-200 dark:bg-slate-700 text-slate-800 dark:text-slate-200">
              {inboundList.length + consignments.length}
            </span>
          </button>
          <button
            onClick={() => setActiveTab('INBOUND')}
            className={`px-3 py-1.5 rounded text-xs font-mono font-semibold transition-colors flex items-center gap-2 whitespace-nowrap ${
              activeTab === 'INBOUND'
                ? 'bg-slate-900 text-white dark:bg-white dark:text-slate-950'
                : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800'
            }`}
          >
            Inbound Requisitions
            {pendingCount > 0 && (
              <span className="px-1.5 py-0.2 text-[10px] rounded-full bg-amber-500 text-white font-bold animate-pulse">
                {pendingCount}
              </span>
            )}
          </button>
          <button
            onClick={() => setActiveTab('CONSIGNMENTS')}
            className={`px-3 py-1.5 rounded text-xs font-mono font-semibold transition-colors flex items-center gap-2 whitespace-nowrap ${
              activeTab === 'CONSIGNMENTS'
                ? 'bg-slate-900 text-white dark:bg-white dark:text-slate-950'
                : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800'
            }`}
          >
            Active Consignments
            <span className="px-1.5 py-0.2 text-[10px] rounded-full bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-300">
              {activeConsignmentsCount}
            </span>
          </button>
          <button
            onClick={() => setActiveTab('FULFILLED')}
            className={`px-3 py-1.5 rounded text-xs font-mono font-semibold transition-colors flex items-center gap-2 whitespace-nowrap ${
              activeTab === 'FULFILLED'
                ? 'bg-slate-900 text-white dark:bg-white dark:text-slate-950'
                : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800'
            }`}
          >
            Fulfilled & Archive
          </button>
        </div>

        {/* Search & Urgency Filter */}
        <div className="flex items-center gap-2">
          <div className="relative">
            <Search className="absolute left-2.5 top-2 text-slate-400" size={15} />
            <input
              type="text"
              placeholder="Search REQ-ID, SKU, plant..."
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              className="pl-8 pr-3 py-1.5 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded text-xs focus:outline-none focus:ring-1 focus:ring-slate-400 w-52 md:w-64 font-mono"
            />
          </div>
          <select
            value={urgencyFilter}
            onChange={e => setUrgencyFilter(e.target.value as any)}
            className="px-2.5 py-1.5 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded text-xs font-medium text-slate-700 dark:text-slate-300 focus:outline-none"
          >
            <option value="ALL">All Urgency</option>
            <option value="EMERGENCY">Emergency Only</option>
            <option value="STANDARD">Standard Only</option>
          </select>
        </div>
      </div>

      {/* Main Content Layout */}
      {(activeTab === 'ALL' || activeTab === 'INBOUND') && (
        <section className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Inbox size={18} className="text-amber-500" />
              <h2 className="font-mono text-sm font-bold uppercase tracking-wider text-slate-800 dark:text-slate-200">
                Inbound Requisitions To Supply (Action Required)
              </h2>
            </div>
            <span className="text-xs text-slate-500">
              {filteredInbound.length} requests awaiting depot verification
            </span>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {filteredInbound.map(req => {
              const isEmergency = req.urgency === 'EMERGENCY';
              const isApproved = req.status === 'APPROVED';
              const isDeclined = req.status === 'DECLINED';

              return (
                <Card
                  key={req.id}
                  className={`p-0 overflow-hidden border-2 transition-all ${
                    isEmergency
                      ? 'border-amber-500/80 bg-amber-50/10 dark:bg-amber-950/10'
                      : 'border-slate-200 dark:border-slate-800'
                  }`}
                >
                  {/* Card Header */}
                  <div className="p-3.5 bg-slate-50 dark:bg-slate-900/90 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="font-mono font-bold text-sm text-slate-900 dark:text-white">
                        {req.id}
                      </span>
                      {isEmergency ? (
                        <span className="flex items-center gap-1 px-2 py-0.5 text-[11px] font-mono font-bold bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300 border border-rose-200 dark:border-rose-900 rounded">
                          <span className="w-1.5 h-1.5 rounded-full bg-rose-600 animate-ping"></span>
                          EMERGENCY BREAKDOWN
                        </span>
                      ) : (
                        <span className="px-2 py-0.5 text-[11px] font-mono bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 rounded">
                          STANDARD
                        </span>
                      )}
                    </div>
                    <span className="text-xs font-mono text-slate-500 dark:text-slate-400">
                      {req.submitted_time}
                    </span>
                  </div>

                  {/* Card Body */}
                  <div className="p-4 space-y-3">
                    <div className="flex items-start justify-between gap-4">
                      <div>
                        <div className="flex items-center gap-1.5 text-xs text-slate-500 dark:text-slate-400">
                          <Building2 size={13} />
                          <span>Requester:</span>
                          <strong className="text-slate-800 dark:text-slate-200 font-mono">
                            {req.requester_cpse}
                          </strong>
                        </div>
                        <p className="text-sm font-semibold text-slate-900 dark:text-white mt-0.5">
                          {req.requester_facility}
                        </p>
                        <p className="text-xs text-slate-500 mt-0.5">
                          Contact: {req.requester_officer}
                        </p>
                      </div>

                      <div className="text-right shrink-0">
                        <span className="text-[10px] font-mono uppercase text-slate-400 block">
                          SLA Remaining
                        </span>
                        <span
                          className={`font-mono font-bold text-sm ${
                            req.sla_hours_remaining < 4
                              ? 'text-rose-600 dark:text-rose-400'
                              : 'text-amber-600 dark:text-amber-400'
                          }`}
                        >
                          {req.sla_hours_remaining} hrs
                        </span>
                      </div>
                    </div>

                    {/* Material Spec Strip */}
                    <div className="p-3 bg-slate-100/70 dark:bg-slate-900/60 rounded border border-slate-200/80 dark:border-slate-800 space-y-1.5">
                      <div className="flex items-center justify-between">
                        <span className="font-mono text-xs font-bold text-slate-900 dark:text-slate-100">
                          {req.part_name}
                        </span>
                        <span className="px-2 py-0.5 bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300 text-[10px] font-mono font-semibold rounded">
                          {req.compatibility_score}% Spec Match
                        </span>
                      </div>
                      <div className="grid grid-cols-3 gap-2 text-[11px] font-mono text-slate-600 dark:text-slate-400">
                        <div>
                          <span className="text-slate-400 block text-[10px]">Metallurgy</span>
                          {req.metallurgy}
                        </div>
                        <div>
                          <span className="text-slate-400 block text-[10px]">Pressure / Size</span>
                          {req.pressure_class} • {req.size}
                        </div>
                        <div>
                          <span className="text-slate-400 block text-[10px]">Requisition Qty</span>
                          <strong className="text-slate-800 dark:text-slate-200">
                            {req.quantity} {req.unit}
                          </strong>
                        </div>
                      </div>
                    </div>

                    {/* Stock Impact & Route Preview */}
                    <div className="flex items-center justify-between text-xs font-mono text-slate-600 dark:text-slate-400 pt-1">
                      <div className="flex items-center gap-1.5">
                        <MapPin size={13} className="text-slate-400" />
                        <span>
                          {req.distance_km} km ({req.transit_hours} hrs est. transit)
                        </span>
                      </div>
                      <div>
                        Stock Impact:{' '}
                        <span className="text-slate-800 dark:text-slate-200 font-semibold">
                          {req.available_stock} EA → {req.available_stock - req.quantity} EA
                        </span>
                      </div>
                    </div>

                    {/* Action Bar */}
                    <div className="pt-2 border-t border-slate-200 dark:border-slate-800">
                      {isApproved ? (
                        <div className="flex items-center justify-between bg-emerald-50 dark:bg-emerald-950/40 p-2 rounded border border-emerald-200 dark:border-emerald-800">
                          <div className="flex items-center gap-2 text-xs font-mono text-emerald-800 dark:text-emerald-300 font-semibold">
                            <CheckCircle2 size={16} />
                            <span>Supply Confirmed • Gate Pass {req.gate_pass_id} Issued</span>
                          </div>
                          <Link
                            href={`/requests/${req.id}`}
                            className="text-xs font-mono font-bold text-emerald-700 hover:text-emerald-900 dark:text-emerald-400 dark:hover:text-emerald-200 flex items-center gap-1"
                          >
                            View Pass <ArrowRight size={13} />
                          </Link>
                        </div>
                      ) : isDeclined ? (
                        <div className="p-2 bg-rose-50 dark:bg-rose-950/40 text-rose-700 dark:text-rose-400 text-xs font-mono rounded flex items-center gap-2">
                          <XCircle size={15} />
                          <span>Requisition Declined (Depot Reserve Protected)</span>
                        </div>
                      ) : (
                        <div className="flex gap-2">
                          <button
                            onClick={() => handleConfirmSupply(req.id)}
                            className="flex-1 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded text-xs font-mono font-bold flex items-center justify-center gap-1.5 transition-colors"
                          >
                            <CheckCircle2 size={15} /> Confirm Supply & Issue CISF Pass
                          </button>
                          <button
                            onClick={() => handleDecline(req.id)}
                            className="px-3 py-2 border border-slate-300 dark:border-slate-700 text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/40 rounded text-xs font-mono font-semibold transition-colors flex items-center gap-1"
                          >
                            <XCircle size={15} /> Decline
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                </Card>
              );
            })}
          </div>
        </section>
      )}

      {/* Active & Historic Consignments Section */}
      {(activeTab === 'ALL' || activeTab === 'CONSIGNMENTS' || activeTab === 'FULFILLED') && (
        <section className="space-y-4 pt-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Truck size={18} className="text-blue-500" />
              <h2 className="font-mono text-sm font-bold uppercase tracking-wider text-slate-800 dark:text-slate-200">
                Active & Tracked Consignments
              </h2>
            </div>
            <span className="text-xs text-slate-500">
              Live transit telemetry with milestone verification
            </span>
          </div>

          <div className="space-y-3">
            {filteredConsignments.map(con => {
              const isDelivered = con.status === 'DELIVERED';
              const isInTransit = con.status === 'IN_TRANSIT';

              return (
                <Card
                  key={con.id}
                  className="p-4 hover:border-slate-400 dark:hover:border-slate-700 transition-all cursor-pointer group"
                >
                  <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
                    {/* Left: Identifier & Destination */}
                    <div className="space-y-1 lg:w-1/3">
                      <div className="flex items-center gap-2">
                        <Link
                          href={`/requests/${con.id}`}
                          className="font-mono font-bold text-sm text-blue-600 dark:text-blue-400 hover:underline flex items-center gap-1"
                        >
                          {con.id}
                          <ExternalLink size={12} />
                        </Link>
                        <span
                          className={`px-2 py-0.5 text-[10px] font-mono font-semibold rounded ${
                            con.direction === 'OUTBOUND'
                              ? 'bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300'
                              : 'bg-purple-100 text-purple-800 dark:bg-purple-950 dark:text-purple-300'
                          }`}
                        >
                          {con.direction}
                        </span>
                        {con.urgency === 'EMERGENCY' && (
                          <span className="px-1.5 py-0.5 text-[10px] font-mono font-bold bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300 rounded">
                            EMERGENCY
                          </span>
                        )}
                      </div>
                      <p className="text-sm font-semibold text-slate-900 dark:text-slate-100">
                        {con.material_title}
                      </p>
                      <p className="text-xs text-slate-500 font-mono">
                        Destination: <span className="text-slate-700 dark:text-slate-300 font-semibold">{con.destination_facility}</span>
                      </p>
                    </div>

                    {/* Middle: Progress Stepper & Milestone */}
                    <div className="space-y-2 lg:w-1/3">
                      <div className="flex items-center justify-between text-xs font-mono">
                        <span className="text-slate-500">Route Milestone</span>
                        <span className="font-bold text-slate-800 dark:text-slate-200">
                          {con.progress_pct}% Completed
                        </span>
                      </div>
                      <div className="w-full bg-slate-200 dark:bg-slate-800 h-2 rounded-full overflow-hidden">
                        <div
                          className={`h-full rounded-full transition-all ${
                            isDelivered
                              ? 'bg-emerald-500'
                              : isInTransit
                              ? 'bg-blue-600'
                              : 'bg-amber-500'
                          }`}
                          style={{ width: `${con.progress_pct}%` }}
                        />
                      </div>
                      <div className="flex items-center justify-between text-[11px] font-mono text-slate-500 dark:text-slate-400">
                        <span>Veh: {con.vehicle_reg}</span>
                        <span className="truncate max-w-[200px] text-right">{con.current_location}</span>
                      </div>
                    </div>

                    {/* Right: Status & Actions */}
                    <div className="flex items-center justify-between lg:justify-end gap-4 lg:w-1/4">
                      <div className="text-right">
                        <span className="text-[10px] font-mono uppercase text-slate-400 block">
                          Estimated Arrival
                        </span>
                        <span className="font-mono text-xs font-semibold text-slate-900 dark:text-slate-100">
                          {con.eta}
                        </span>
                      </div>

                      <Link
                        href={`/requests/${con.id}`}
                        className="px-3 py-1.5 bg-slate-900 hover:bg-slate-800 dark:bg-white dark:hover:bg-slate-100 text-white dark:text-slate-900 rounded text-xs font-mono font-semibold flex items-center gap-1.5 transition-colors shrink-0"
                      >
                        <span>Pass & Telemetry</span>
                        <ChevronRight size={14} />
                      </Link>
                    </div>
                  </div>
                </Card>
              );
            })}
          </div>
        </section>
      )}
    </div>
  );
}
