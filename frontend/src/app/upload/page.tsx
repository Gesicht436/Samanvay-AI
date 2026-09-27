"use client";

import React, { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Card, Skeleton } from '@/components/ui';
import {
  Upload,
  FileText,
  AlertTriangle,
  CheckCircle2,
  Loader2,
  RefreshCw,
  Clock,
  ArrowRight,
} from 'lucide-react';
import { api } from '@/lib/api';
import { ProtectedRoute } from '@/components/ProtectedRoute';

export default function DocumentIntakePage() {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [statusMessage, setStatusMessage] = useState('');
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Ingested documents list
  const [recentDocs, setRecentDocs] = useState<any[]>([]);
  const [loadingDocs, setLoadingDocs] = useState<boolean>(true);

  const fetchRecentDocs = async () => {
    setLoadingDocs(true);
    try {
      const res = await api.listDocuments(0, 10);
      if (res && Array.isArray(res.documents)) {
        setRecentDocs(res.documents);
      } else if (Array.isArray(res)) {
        setRecentDocs(res);
      } else {
        setRecentDocs([]);
      }
    } catch {
      setRecentDocs([]);
    } finally {
      setLoadingDocs(false);
    }
  };

  useEffect(() => {
    fetchRecentDocs();
  }, []);

  const handleFileUpload = async (file: File) => {
    setIsProcessing(true);
    setErrorMsg(null);
    setStatusMessage('Uploading document to PyMuPDF & PaddleOCR parser...');

    try {
      const formData = new FormData();
      formData.append('file', file);

      setStatusMessage('Extracting chemistry, IIW Carbon Equivalent & ASTM standards...');
      const response = await api.uploadDocument(formData);

      if (typeof window !== 'undefined') {
        sessionStorage.setItem('current_mtc', JSON.stringify(response));
      }

      router.push('/upload/review');
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to process document. Please check file format.');
      setIsProcessing(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileUpload(e.dataTransfer.files[0]);
    }
  };

  return (
    <ProtectedRoute allowedRoles={['SITE_ENGINEER', 'MATERIALS_MANAGER', 'TECHNICAL_AUTHORITY', 'SUPER_ADMIN']}>
      <div className="space-y-4 max-w-7xl mx-auto pb-10">
        {/* Header */}
        <div className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-lg p-4 transition-colors">
          <div className="flex items-center gap-2">
            <h1 className="text-sm font-semibold text-zinc-900 dark:text-zinc-100 font-sans">
              Material Test Certificate (MTC) Intake
            </h1>
            <span className="px-1.5 py-0.2 text-[10px] font-mono text-zinc-500 bg-zinc-100 dark:bg-zinc-800 rounded border border-zinc-200 dark:border-zinc-750">
              PyMuPDF & PaddleOCR
            </span>
          </div>
          <p className="text-xs text-zinc-500 dark:text-zinc-400 font-mono mt-0.5">
            OCR attribute extraction, IIW carbon equivalent weldability ($CE \le 0.43\%$), and ASTM specification boundary checks.
          </p>
        </div>

        {errorMsg && (
          <div className="p-2.5 bg-rose-500/10 border border-rose-500/20 text-rose-700 dark:text-rose-400 text-xs font-mono rounded-lg flex items-center justify-between">
            <span>{errorMsg}</span>
            <button onClick={() => setErrorMsg(null)} className="text-zinc-400 hover:text-zinc-600">&times;</button>
          </div>
        )}

        {/* Upload Drop Zone */}
        <div
          onDragOver={(e) => {
            e.preventDefault();
            setIsDragging(true);
          }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={handleDrop}
          onClick={() => !isProcessing && fileInputRef.current?.click()}
          className={`border border-dashed rounded-lg p-8 text-center transition-colors cursor-pointer select-none bg-white dark:bg-zinc-900 ${
            isDragging
              ? 'border-zinc-500 bg-zinc-50 dark:bg-zinc-850'
              : 'border-zinc-300 dark:border-zinc-700 hover:border-zinc-400 dark:hover:border-zinc-600'
          }`}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.png,.jpg,.jpeg,.tiff,.tif"
            className="hidden"
            onChange={(e) => {
              if (e.target.files && e.target.files[0]) {
                handleFileUpload(e.target.files[0]);
              }
            }}
          />

          {isProcessing ? (
            <div className="py-4 flex flex-col items-center justify-center space-y-2.5">
              <Loader2 className="h-6 w-6 text-zinc-700 dark:text-zinc-300 animate-spin" />
              <p className="font-mono text-xs font-medium text-zinc-800 dark:text-zinc-200">
                {statusMessage || 'Processing certificate...'}
              </p>
              <p className="text-[11px] text-zinc-400 font-mono">
                Extracting textual tokens and checking chemistry tolerances against ASTM standards
              </p>
            </div>
          ) : (
            <div className="py-2">
              <div className="w-10 h-10 mx-auto rounded-md bg-zinc-100 dark:bg-zinc-800 flex items-center justify-center text-zinc-600 dark:text-zinc-300 mb-2 border border-zinc-200 dark:border-zinc-700">
                <Upload size={18} />
              </div>
              <h3 className="text-xs font-medium text-zinc-900 dark:text-zinc-100 font-sans">
                Drag and drop Material Test Certificate (MTC)
              </h3>
              <p className="text-[11px] text-zinc-500 font-mono mt-0.5">
                EN 10204 3.1 PDF certificates, scanned delivery challans, or inspection reports (.pdf, .png, .jpg)
              </p>
              <div className="mt-3">
                <span className="px-3 py-1 bg-zinc-900 hover:bg-zinc-800 text-white dark:bg-zinc-100 dark:hover:bg-zinc-200 dark:text-zinc-900 text-xs font-medium rounded-md transition-colors inline-block">
                  Browse Files
                </span>
              </div>
            </div>
          )}
        </div>

        {/* Recently Ingested Documents */}
        <div className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-lg overflow-hidden shadow-2xs">
          <div className="p-3 border-b border-zinc-100 dark:border-zinc-800 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <FileText size={14} className="text-zinc-500" />
              <h2 className="text-xs font-mono font-semibold uppercase tracking-wider text-zinc-700 dark:text-zinc-300">
                Ingested Documents
              </h2>
            </div>

            <button
              onClick={fetchRecentDocs}
              disabled={loadingDocs}
              className="p-1 bg-zinc-100 dark:bg-zinc-800 hover:bg-zinc-200 dark:hover:bg-zinc-700 text-zinc-600 dark:text-zinc-300 rounded text-xs transition-colors"
              title="Refresh list"
            >
              <RefreshCw size={12} className={loadingDocs ? 'animate-spin' : ''} />
            </button>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left compact-table border-collapse">
              <thead>
                <tr className="border-b border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-900/80">
                  <th className="w-16">Doc ID</th>
                  <th>Filename</th>
                  <th>Type</th>
                  <th>OCR Confidence</th>
                  <th>Uploaded</th>
                  <th className="text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-100 dark:divide-zinc-800/80 text-xs font-mono">
                {loadingDocs ? (
                  Array.from({ length: 3 }).map((_, i) => (
                    <tr key={i} className="h-[38px]">
                      <td><Skeleton className="h-4 w-10" /></td>
                      <td><Skeleton className="h-4 w-40" /></td>
                      <td><Skeleton className="h-4 w-24" /></td>
                      <td><Skeleton className="h-4 w-16" /></td>
                      <td><Skeleton className="h-4 w-28" /></td>
                      <td className="text-right"><Skeleton className="h-4 w-14 ml-auto" /></td>
                    </tr>
                  ))
                ) : recentDocs.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="py-10 text-center text-zinc-400 font-mono text-xs">
                      No documents ingested yet. Upload an MTC above to begin digital parsing.
                    </td>
                  </tr>
                ) : (
                  recentDocs.map((doc) => (
                    <tr key={doc.id} className="hover:bg-zinc-50 dark:hover:bg-zinc-800/50 transition-colors">
                      <td className="font-semibold text-zinc-900 dark:text-zinc-100 tabular-nums">
                        #{doc.id}
                      </td>
                      <td className="text-zinc-800 dark:text-zinc-200 truncate max-w-[280px]">
                        {doc.filename}
                      </td>
                      <td className="text-zinc-500">
                        {doc.doc_type || 'MTC_CERTIFICATE'}
                      </td>
                      <td className="tabular-nums font-medium text-zinc-700 dark:text-zinc-300">
                        {doc.confidence !== undefined && doc.confidence !== null ? `${(doc.confidence * 100).toFixed(1)}%` : '—'}
                      </td>
                      <td className="text-zinc-500 text-[11px]">
                        {doc.created_at ? new Date(doc.created_at).toLocaleString('en-IN') : 'Recently'}
                      </td>
                      <td className="text-right">
                        <button
                          onClick={() => {
                            if (typeof window !== 'undefined') {
                              sessionStorage.setItem('current_mtc', JSON.stringify(doc));
                            }
                            router.push('/upload/review');
                          }}
                          className="px-2 py-1 bg-zinc-100 dark:bg-zinc-800 hover:bg-zinc-200 dark:hover:bg-zinc-700 text-zinc-700 dark:text-zinc-300 rounded text-[11px] font-medium transition-colors"
                        >
                          Review &rarr;
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </ProtectedRoute>
  );
}
