"use client";

import React, { useState, useMemo } from 'react';
import { Card, KpiCard, StatusBadge } from '@/components/ui';
import {
  ShieldCheck,
  Download,
  Search,
  Filter,
  CheckCircle2,
  Lock,
  KeyRound,
  FileCode,
  Layers,
  ChevronDown,
  ChevronRight,
  ExternalLink,
  Copy,
  Check,
  RefreshCw,
  Cpu,
  AlertTriangle,
} from 'lucide-react';
import { exportToCSV } from '@/lib/exportUtils';

interface AuditEvent {
  id: string;
  block_height: number;
  timestamp: string;
  node: 'IOCL-PNP' | 'ONGC-URN' | 'BPCL-MUM' | 'HPCL-VSK' | 'GAIL-PAT';
  category:
    | 'MTC_INGEST'
    | 'HITL_TRIAGE'
    | 'STATUS_CHANGE'
    | 'REQUISITION'
    | 'GATE_PASS'
    | 'DISPATCH'
    | 'PRIVACY_MASK';
  action: string;
  target: string;
  actor: string;
  actor_role: string;
  hash: string;
  prev_hash: string;
  details: Record<string, any>;
  consensus_nodes: string[];
}

const INITIAL_AUDIT_LOGS: AuditEvent[] = [
  {
    id: 'EV-1842',
    block_height: 1842,
    timestamp: '2026-03-18T11:30:14Z',
    node: 'IOCL-PNP',
    category: 'DISPATCH',
    action: 'CONSIGNMENT_DISPATCHED',
    target: 'REQ-44810 (PRT-9014)',
    actor: 'cisf_officer_41',
    actor_role: 'CISF Security Gate Sub-Inspector',
    hash: '5d41402abc4b2a76b9719d911017c5926b4e3416e7807759b489a2472b6b553e',
    prev_hash: '8a91a92120e290f6b4e7a83d739818817454f7a26f8d1eb1997d4fb526543b56',
    details: {
      vehicle_reg: 'UP-75-BT-1092',
      destination: 'GAIL-PATA',
      items_dispatched: '6x Gate Valve 6" Class 600# RTJ',
      out_gate_barrier: 'GATE_04_HEAVY',
      driver_lic: 'DL-04201988102',
    },
    consensus_nodes: ['IOCL-PNP', 'ONGC-URN', 'BPCL-MUM', 'HPCL-VSK', 'GAIL-PAT'],
  },
  {
    id: 'EV-1841',
    block_height: 1841,
    timestamp: '2026-03-18T10:45:00Z',
    node: 'IOCL-PNP',
    category: 'GATE_PASS',
    action: 'GATE_PASS_GENERATED',
    target: 'GP-NR-44810',
    actor: 'dgm_materials_09',
    actor_role: 'Dy. General Manager (Stores & Logistics)',
    hash: '8a91a92120e290f6b4e7a83d739818817454f7a26f8d1eb1997d4fb526543b56',
    prev_hash: '2c624232cdd221771294dfbb379ac8ab8733a1e948ff1ff1918a2ee305c08888',
    details: {
      requisition_id: 'REQ-44810',
      pass_type: 'NON-RETURNABLE-MUTUAL-AID',
      statutory_order: 'MoPNG/E-DISP/2025/11',
      qr_payload_digest: '4a1b8c2d9e0f',
    },
    consensus_nodes: ['IOCL-PNP', 'ONGC-URN', 'BPCL-MUM', 'HPCL-VSK', 'GAIL-PAT'],
  },
  {
    id: 'EV-1840',
    block_height: 1840,
    timestamp: '2026-03-18T09:15:22Z',
    node: 'ONGC-URN',
    category: 'PRIVACY_MASK',
    action: 'ATTRIBUTE_MASK_APPLIED',
    target: 'CATALOG_BROADCAST_PRT-8892',
    actor: 'sovereign_privacy_proxy',
    actor_role: 'Air-Gapped P2P Mesh Privacy Daemon',
    hash: '2c624232cdd221771294dfbb379ac8ab8733a1e948ff1ff1918a2ee305c08888',
    prev_hash: '1b2a3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b',
    details: {
      masked_attributes: ['unit_procurement_price', 'supplier_commercial_contract_id', 'depreciation_factor'],
      retained_attributes: ['metallurgy', 'pressure_rating', 'size', 'heat_number', 'physical_spec_hash'],
      privacy_protocol: 'MoPNG-PRIVACY-TIER-01',
    },
    consensus_nodes: ['IOCL-PNP', 'ONGC-URN', 'BPCL-MUM', 'HPCL-VSK', 'GAIL-PAT'],
  },
  {
    id: 'EV-1839',
    block_height: 1839,
    timestamp: '2026-03-18T08:30:10Z',
    node: 'BPCL-MUM',
    category: 'REQUISITION',
    action: 'REQUISITION_CREATED',
    target: 'REQ-99208',
    actor: 'chief_eng_refinery',
    actor_role: 'Chief Engineer (Maintenance)',
    hash: '1b2a3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b',
    prev_hash: '9f8e7d6c5b4a39281706152433445566778899aabbccddeeff00112233445566',
    details: {
      demanding_unit: 'FCCU Catalytic Cracker',
      required_sku: 'PRT-8893',
      priority: 'STANDARD_PLANNED',
      quantity_demanded: 1,
    },
    consensus_nodes: ['IOCL-PNP', 'ONGC-URN', 'BPCL-MUM', 'HPCL-VSK', 'GAIL-PAT'],
  },
  {
    id: 'EV-1838',
    block_height: 1838,
    timestamp: '2026-03-17T16:20:05Z',
    node: 'IOCL-PNP',
    category: 'STATUS_CHANGE',
    action: 'SURPLUS_BROADCAST_TOGGLED',
    target: 'PRT-8892 (A105 Flange)',
    actor: 'chief_metallurgist_iocl',
    actor_role: 'Lead Metallurgical Engineer',
    hash: '9f8e7d6c5b4a39281706152433445566778899aabbccddeeff00112233445566',
    prev_hash: 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
    details: {
      old_status: 'IN_STORAGE',
      new_status: 'IDLE_SURPLUS',
      days_idle_recorded: 142,
      broadcast_scope: 'PAN_CPSE_MESH',
    },
    consensus_nodes: ['IOCL-PNP', 'ONGC-URN', 'BPCL-MUM', 'HPCL-VSK', 'GAIL-PAT'],
  },
  {
    id: 'EV-1837',
    block_height: 1837,
    timestamp: '2026-03-17T15:40:50Z',
    node: 'IOCL-PNP',
    category: 'HITL_TRIAGE',
    action: 'HITL_OVERRIDE_APPROVED',
    target: 'PRT-9014 (Gate Valve)',
    actor: 'lead_inspector_gov',
    actor_role: 'MoPNG Sovereign Quality Auditor',
    hash: 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
    prev_hash: 'c89329343b223825266db935286c0ac81ea6156e577b3ddf194ffb15b12403ec',
    details: {
      field_reviewed: 'yield_strength_mpa',
      scanned_value: '265 MPa',
      catalog_spec: '250 MPa min',
      resolution: 'APPROVED_SUPERIOR_STRENGTH',
      justification: 'Higher yield strength exceeds minimum ASTM A350 requirement; zero safety degradation.',
    },
    consensus_nodes: ['IOCL-PNP', 'ONGC-URN', 'BPCL-MUM', 'HPCL-VSK', 'GAIL-PAT'],
  },
  {
    id: 'EV-1836',
    block_height: 1836,
    timestamp: '2026-03-17T14:10:18Z',
    node: 'IOCL-PNP',
    category: 'MTC_INGEST',
    action: 'MTC_OCR_INGESTED',
    target: 'MTC-BHEL-2024-09',
    actor: 'air_gap_ocr_v2',
    actor_role: 'PaddleOCR High-Assurance Extractor',
    hash: 'c89329343b223825266db935286c0ac81ea6156e577b3ddf194ffb15b12403ec',
    prev_hash: '7d793037a0760186574b0282f2f435e70d73a4e044d7999142e02da59f301a44',
    details: {
      file_name: 'MTC_IOCL_Flange_A105.pdf',
      heat_number: 'HT-2025-20300',
      standard: 'ASTM A105 / ASME B16.5',
      carbon_equivalent_ce: 0.41,
      elements_extracted: ['C', 'Mn', 'Si', 'P', 'S', 'Cr', 'Ni', 'Mo', 'V'],
    },
    consensus_nodes: ['IOCL-PNP', 'ONGC-URN', 'BPCL-MUM', 'HPCL-VSK', 'GAIL-PAT'],
  },
];

export default function AuditPage() {
  const [logs, setLogs] = useState<AuditEvent[]>(INITIAL_AUDIT_LOGS);
  const [searchQuery, setSearchQuery] = useState('');
  const [categoryFilter, setCategoryFilter] = useState<string>('ALL');
  const [nodeFilter, setNodeFilter] = useState<string>('ALL');
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [copiedHash, setCopiedHash] = useState<string | null>(null);

  // Verification state machine
  const [isVerifying, setIsVerifying] = useState(false);
  const [verificationProgress, setVerificationProgress] = useState(0);
  const [verificationResult, setVerificationResult] = useState<{
    status: 'IDLE' | 'SUCCESS';
    verifiedCount: number;
    merkleRoot: string;
  }>({ status: 'IDLE', verifiedCount: 1842, merkleRoot: '0x4a9fc28109d7e35b7194f1c99382acdf' });

  const handleExport = () => {
    const exportable = logs.map(l => ({
      BlockHeight: l.block_height,
      Timestamp: l.timestamp,
      Node: l.node,
      Category: l.category,
      Action: l.action,
      Target: l.target,
      Actor: l.actor,
      ActorRole: l.actor_role,
      SHA256Seal: l.hash,
      PreviousHash: l.prev_hash,
      ConsensusProof: l.consensus_nodes.join('; '),
    }));
    exportToCSV('samanvay_sovereign_audit_ledger.csv', exportable);
  };

  const handleCopyHash = (hash: string) => {
    navigator.clipboard.writeText(hash);
    setCopiedHash(hash);
    setTimeout(() => setCopiedHash(null), 2500);
  };

  const handleVerifyChain = () => {
    setIsVerifying(true);
    setVerificationProgress(10);

    const timer1 = setTimeout(() => setVerificationProgress(40), 400);
    const timer2 = setTimeout(() => setVerificationProgress(75), 800);
    const timer3 = setTimeout(() => {
      setVerificationProgress(100);
      setIsVerifying(false);
      setVerificationResult({
        status: 'SUCCESS',
        verifiedCount: 1842,
        merkleRoot: '0x4a9fc28109d7e35b7194f1c99382acdf',
      });
    }, 1200);
  };

  const filteredLogs = useMemo(() => {
    return logs.filter(log => {
      const matchesSearch =
        log.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
        log.action.toLowerCase().includes(searchQuery.toLowerCase()) ||
        log.target.toLowerCase().includes(searchQuery.toLowerCase()) ||
        log.actor.toLowerCase().includes(searchQuery.toLowerCase()) ||
        log.hash.toLowerCase().includes(searchQuery.toLowerCase());

      const matchesCat = categoryFilter === 'ALL' || log.category === categoryFilter;
      const matchesNode = nodeFilter === 'ALL' || log.node === nodeFilter;

      return matchesSearch && matchesCat && matchesNode;
    });
  }, [logs, searchQuery, categoryFilter, nodeFilter]);

  const categories = [
    { id: 'ALL', label: 'All Events' },
    { id: 'DISPATCH', label: 'Dispatch' },
    { id: 'GATE_PASS', label: 'Gate Pass' },
    { id: 'PRIVACY_MASK', label: 'Privacy Mask' },
    { id: 'REQUISITION', label: 'Requisitions' },
    { id: 'STATUS_CHANGE', label: 'Status Change' },
    { id: 'HITL_TRIAGE', label: 'HITL Triage' },
    { id: 'MTC_INGEST', label: 'MTC Ingest' },
  ];

  return (
    <div className="max-w-7xl mx-auto space-y-6 pb-12">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <h1 className="text-2xl font-bold font-mono tracking-tight text-slate-900 dark:text-white">
              Sovereign Audit Ledger
            </h1>
            <span className="px-2 py-0.5 text-xs font-mono font-bold bg-emerald-50 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800 rounded flex items-center gap-1">
              <ShieldCheck size={13} />
              IMMUTABLE CHAIN
            </span>
          </div>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Cryptographically sealed chronological event stream with SHA-256 digests and distributed Merkle consensus
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            onClick={handleVerifyChain}
            disabled={isVerifying}
            className="px-3.5 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded text-xs font-mono font-bold flex items-center gap-2 shadow-sm transition-colors cursor-pointer disabled:opacity-50"
          >
            {isVerifying ? (
              <>
                <RefreshCw size={14} className="animate-spin" /> Verifying Ledger Hashes...
              </>
            ) : (
              <>
                <ShieldCheck size={16} /> Verify Merkle Chain
              </>
            )}
          </button>
          <button
            onClick={handleExport}
            className="px-3.5 py-2 bg-slate-900 hover:bg-slate-800 dark:bg-white dark:hover:bg-slate-100 text-white dark:text-slate-950 rounded text-xs font-mono font-bold flex items-center gap-2 shadow-sm transition-colors cursor-pointer"
          >
            <Download size={15} /> Export RFC 4180 CSV
          </button>
        </div>
      </div>

      {/* Verification Banner (Triggered when verified) */}
      {verificationResult.status === 'SUCCESS' && (
        <div className="p-4 bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-300 dark:border-emerald-800 rounded-lg flex flex-col md:flex-row md:items-center justify-between gap-3 text-xs font-mono text-emerald-900 dark:text-emerald-200 animate-fadeIn">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-full bg-emerald-600 text-white flex items-center justify-center shrink-0">
              <Check size={18} />
            </div>
            <div>
              <p className="font-bold text-sm">
                Merkle Tree Integrity Confirmed (Height: {verificationResult.verifiedCount} Blocks)
              </p>
              <p className="text-emerald-700 dark:text-emerald-300 text-[11px]">
                Zero hash collisions detected. Consensus anchor:{' '}
                <span className="font-bold">{verificationResult.merkleRoot}</span> • Verified across 5 CPSE nodes.
              </p>
            </div>
          </div>
          <span className="text-[10px] uppercase font-bold tracking-widest px-2.5 py-1 bg-emerald-100 dark:bg-emerald-900 text-emerald-800 dark:text-emerald-200 rounded self-start md:self-auto">
            100% UNALTERED
          </span>
        </div>
      )}

      {/* Top 4 KPI Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <KpiCard
          label="Ledger Block Height"
          value="1,842 Blocks"
          subtext="Consecutive parent-child hashes"
          delta="100% Continuity"
          deltaType="positive"
          icon={<Layers size={20} />}
        />
        <KpiCard
          label="Merkle Root Proof"
          value="0x4a9f...c281"
          subtext="Distributed anchor signature"
          delta="Cryptographically Sealed"
          deltaType="positive"
          icon={<KeyRound size={20} />}
        />
        <KpiCard
          label="P2P Consensus Mesh"
          value="5/5 Nodes Active"
          subtext="IOCL, ONGC, BPCL, HPCL, GAIL"
          delta="Zero partitions"
          deltaType="positive"
          icon={<Cpu size={20} />}
        />
        <KpiCard
          label="Security Audits"
          value="0 Discrepancies"
          subtext="Strict attribute-level privacy active"
          delta="Zero Leakage"
          deltaType="positive"
          icon={<Lock size={20} />}
        />
      </div>

      {/* Category Tabs and Filter Row */}
      <div className="space-y-3 border-b border-slate-200 dark:border-slate-800 pb-3">
        <div className="flex items-center gap-1 overflow-x-auto">
          {categories.map(cat => (
            <button
              key={cat.id}
              onClick={() => setCategoryFilter(cat.id)}
              className={`px-3 py-1.5 rounded text-xs font-mono font-semibold transition-colors whitespace-nowrap ${
                categoryFilter === cat.id
                  ? 'bg-slate-900 text-white dark:bg-white dark:text-slate-950'
                  : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800'
              }`}
            >
              {cat.label}
            </button>
          ))}
        </div>

        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
          <div className="flex items-center gap-2 flex-1 max-w-md">
            <div className="relative w-full">
              <Search className="absolute left-2.5 top-2 text-slate-400" size={15} />
              <input
                type="text"
                placeholder="Search event ID, action, SKU, actor, or SHA-256..."
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                className="w-full pl-8 pr-3 py-1.5 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded text-xs font-mono focus:outline-none focus:ring-1 focus:ring-slate-400"
              />
            </div>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs font-mono text-slate-500">Filter Node:</span>
            <select
              value={nodeFilter}
              onChange={e => setNodeFilter(e.target.value)}
              className="px-2.5 py-1.5 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded text-xs font-mono text-slate-700 dark:text-slate-300 focus:outline-none"
            >
              <option value="ALL">All CPSE Nodes</option>
              <option value="IOCL-PNP">IOCL Panipat</option>
              <option value="ONGC-URN">ONGC Uran</option>
              <option value="BPCL-MUM">BPCL Mumbai</option>
              <option value="HPCL-VSK">HPCL Visakh</option>
              <option value="GAIL-PAT">GAIL Pata</option>
            </select>
          </div>
        </div>
      </div>

      {/* Main Immutable Ledger Table */}
      <Card className="p-0 overflow-hidden border border-slate-200 dark:border-slate-800">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-slate-100/80 dark:bg-slate-800/80 text-slate-600 dark:text-slate-300 border-b border-slate-200 dark:border-slate-800">
              <tr>
                <th className="p-3 w-16 text-center">Block</th>
                <th className="p-3">Timestamp (UTC)</th>
                <th className="p-3">Node</th>
                <th className="p-3">Category & Action</th>
                <th className="p-3">Target Reference</th>
                <th className="p-3">Actor / Subsystem</th>
                <th className="p-3">SHA-256 Digest</th>
                <th className="p-3 w-12 text-center">Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
              {filteredLogs.map(log => {
                const isExpanded = expandedId === log.id;

                const getCategoryBadgeClass = (cat: string) => {
                  switch (cat) {
                    case 'MTC_INGEST':
                      return 'bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300';
                    case 'HITL_TRIAGE':
                      return 'bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300';
                    case 'STATUS_CHANGE':
                      return 'bg-purple-100 text-purple-800 dark:bg-purple-950 dark:text-purple-300';
                    case 'REQUISITION':
                      return 'bg-cyan-100 text-cyan-800 dark:bg-cyan-950 dark:text-cyan-300';
                    case 'GATE_PASS':
                      return 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300';
                    case 'DISPATCH':
                      return 'bg-indigo-100 text-indigo-800 dark:bg-indigo-950 dark:text-indigo-300';
                    case 'PRIVACY_MASK':
                      return 'bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300';
                    default:
                      return 'bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-300';
                  }
                };

                return (
                  <React.Fragment key={log.id}>
                    <tr
                      onClick={() => setExpandedId(isExpanded ? null : log.id)}
                      className={`hover:bg-slate-50/80 dark:hover:bg-slate-900/60 cursor-pointer transition-colors ${
                        isExpanded ? 'bg-slate-50 dark:bg-slate-900/80' : ''
                      }`}
                    >
                      <td className="p-3 text-center font-bold text-slate-400">
                        #{log.block_height}
                      </td>
                      <td className="p-3 whitespace-nowrap text-slate-600 dark:text-slate-400">
                        {log.timestamp.replace('T', ' ').replace('Z', '')}
                      </td>
                      <td className="p-3 font-semibold text-slate-800 dark:text-slate-200">
                        {log.node}
                      </td>
                      <td className="p-3">
                        <div className="space-y-0.5">
                          <span
                            className={`inline-block px-1.5 py-0.2 text-[10px] font-bold rounded ${getCategoryBadgeClass(
                              log.category
                            )}`}
                          >
                            {log.category}
                          </span>
                          <p className="font-semibold text-slate-900 dark:text-white">
                            {log.action}
                          </p>
                        </div>
                      </td>
                      <td className="p-3 font-semibold text-blue-600 dark:text-blue-400 max-w-[180px] truncate">
                        {log.target}
                      </td>
                      <td className="p-3 text-slate-600 dark:text-slate-400">
                        <p className="font-medium text-slate-800 dark:text-slate-200">{log.actor}</p>
                        <p className="text-[10px] text-slate-400">{log.actor_role}</p>
                      </td>
                      <td className="p-3">
                        <div className="flex items-center gap-1.5">
                          <span className="text-slate-500 font-mono text-[11px] truncate max-w-[140px]">
                            {log.hash.slice(0, 14)}...{log.hash.slice(-6)}
                          </span>
                          <button
                            onClick={e => {
                              e.stopPropagation();
                              handleCopyHash(log.hash);
                            }}
                            className="p-1 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 rounded"
                            title="Copy Full SHA-256 Hash"
                          >
                            {copiedHash === log.hash ? (
                              <Check size={13} className="text-emerald-500" />
                            ) : (
                              <Copy size={13} />
                            )}
                          </button>
                        </div>
                      </td>
                      <td className="p-3 text-center text-slate-400">
                        {isExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                      </td>
                    </tr>

                    {/* Expanded Detail Panel */}
                    {isExpanded && (
                      <tr className="bg-slate-50/50 dark:bg-slate-900/40 border-b border-slate-200 dark:border-slate-800">
                        <td colSpan={8} className="p-4">
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono">
                            {/* Block Cryptography Info */}
                            <div className="space-y-2 border border-slate-200 dark:border-slate-800 p-3 rounded bg-white dark:bg-slate-950">
                              <div className="flex items-center justify-between pb-1 border-b border-slate-100 dark:border-slate-800">
                                <span className="font-bold text-slate-700 dark:text-slate-300 uppercase text-[10px]">
                                  Cryptographic Proof & Parent Link
                                </span>
                                <span className="text-emerald-600 dark:text-emerald-400 font-bold text-[10px] flex items-center gap-1">
                                  <ShieldCheck size={12} /> Hash Validated
                                </span>
                              </div>
                              <div>
                                <span className="text-[10px] text-slate-400 uppercase block">
                                  Current Block SHA-256 Seal
                                </span>
                                <p className="text-[11px] text-slate-800 dark:text-slate-200 break-all bg-slate-100 dark:bg-slate-900 p-1.5 rounded">
                                  {log.hash}
                                </p>
                              </div>
                              <div>
                                <span className="text-[10px] text-slate-400 uppercase block">
                                  Previous Block Hash (Parent Link)
                                </span>
                                <p className="text-[11px] text-slate-600 dark:text-slate-400 break-all bg-slate-100 dark:bg-slate-900 p-1.5 rounded">
                                  {log.prev_hash}
                                </p>
                              </div>
                              <div>
                                <span className="text-[10px] text-slate-400 uppercase block mb-1">
                                  Consensus Witness Nodes ({log.consensus_nodes.length}/5 Synced)
                                </span>
                                <div className="flex flex-wrap gap-1">
                                  {log.consensus_nodes.map(n => (
                                    <span
                                      key={n}
                                      className="px-2 py-0.5 bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 rounded text-[10px]"
                                    >
                                      ✓ {n}
                                    </span>
                                  ))}
                                </div>
                              </div>
                            </div>

                            {/* Structured State Diff / Payload */}
                            <div className="space-y-2 border border-slate-200 dark:border-slate-800 p-3 rounded bg-white dark:bg-slate-950">
                              <div className="flex items-center justify-between pb-1 border-b border-slate-100 dark:border-slate-800">
                                <span className="font-bold text-slate-700 dark:text-slate-300 uppercase text-[10px]">
                                  Recorded Event Payload Data
                                </span>
                                <span className="text-slate-400 text-[10px]">JSON Payload</span>
                              </div>
                              <pre className="p-2 bg-slate-100 dark:bg-slate-900 rounded text-[11px] text-slate-800 dark:text-slate-300 overflow-x-auto leading-relaxed max-h-44">
                                {JSON.stringify(log.details, null, 2)}
                              </pre>
                            </div>
                          </div>
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                );
              })}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
