"use client";

import React, { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Card } from '@/components/ui';
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
      <div className="flex flex-col space-y-5 max-w-[1400px] mx-auto pb-10">
      {/* Top Banner */}
      <div className="p-5 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl shadow-2xs">
        <div className="flex items-center gap-2 mb-1">
          <span className="text-xs font-mono font-semibold text-emerald-700 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/60 px-2 py-0.5 rounded border border-emerald-200 dark:border-emerald-800">
            DOCUMENT INTAKE
          </span>
          <span className="text-xs font-mono text-slate-500">
            PyMuPDF Vector Stream & PaddleOCR Multi-Modal Pipeline
          </span>
        </div>
        <h1 className="text-xl font-bold text-slate-900 dark:text-white tracking-tight">
          Material Test Certificate (MTC) & Procurement Document Intake
        </h1>
        <p className="text-xs text-slate-600 dark:text-slate-400 mt-0.5">
          Automatic digital attribute extraction, chemical composition analysis (IIW CE / PREN), and ASTM boundary validation.
        </p>
      </div>

      {errorMsg && (
        <div className="p-3 bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900 text-rose-800 dark:text-rose-300 text-xs font-mono rounded-lg flex items-center justify-between">
          <span>{errorMsg}</span>
          <button onClick={() => setErrorMsg(null)} className="text-slate-500 hover:text-slate-700">&times;</button>
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
        className={`border-2 border-dashed rounded-xl p-10 text-center transition-colors cursor-pointer select-none bg-white dark:bg-slate-900 ${
          isDragging
            ? 'border-emerald-500 bg-emerald-50/30 dark:bg-emerald-950/20'
            : 'border-slate-300 dark:border-slate-700 hover:border-emerald-500 hover:bg-slate-50/50 dark:hover:bg-slate-800/40'
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
          <div className="py-6 flex flex-col items-center justify-center space-y-3">
            <Loader2 className="h-9 w-9 text-emerald-600 dark:text-emerald-400 animate-spin" />
            <p className="font-mono text-sm font-semibold text-slate-800 dark:text-slate-200">
              {statusMessage || 'Processing certificate...'}
            </p>
            <p className="text-xs text-slate-400 font-mono">
              Running OCR and validating chemical tolerances against ASTM specifications
            </p>
          </div>
        ) : (
          <div className="py-4">
            <div className="w-12 h-12 mx-auto rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center text-emerald-600 dark:text-emerald-400 mb-3 border border-slate-200 dark:border-slate-700">
              <Upload size={22} />
            </div>
            <h3 className="text-base font-semibold text-slate-900 dark:text-slate-100">
              Select or Drag & Drop Material Test Certificate (MTC)
            </h3>
            <p className="text-xs text-slate-500 mt-1 font-mono">
              Supports EN 10204 3.1 PDF certificates, scanned delivery challans, and inspection reports (.pdf, .png, .jpg)
            </p>
            <div className="mt-4">
              <span className="px-4 py-2 bg-slate-900 dark:bg-emerald-600 hover:bg-slate-800 dark:hover:bg-emerald-700 text-white text-xs font-mono font-semibold rounded transition-colors inline-block">
                Browse Files
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Recently Ingested Documents from Backend */}
      <Card className="p-5 border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900">
        <div className="flex items-center justify-between pb-3 border-b border-slate-200 dark:border-slate-800 mb-3">
          <div className="flex items-center gap-2">
            <FileText size={16} className="text-emerald-600 dark:text-emerald-400" />
            <h2 className="text-sm font-mono font-bold uppercase tracking-wider text-slate-900 dark:text-white">
              Recently Ingested Documents
            </h2>
          </div>

          <button
            onClick={fetchRecentDocs}
            disabled={loadingDocs}
            className="p-1.5 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-300 rounded text-xs transition-colors"
            title="Refresh documents list"
          >
            <RefreshCw size={13} className={loadingDocs ? 'animate-spin' : ''} />
          </button>
        </div>

        <div className="overflow-x-auto">
          {loadingDocs ? (
            <div className="py-8 text-center text-xs font-mono text-slate-500">
              Loading ingested documents from database...
            </div>
          ) : recentDocs.length === 0 ? (
            <div className="py-8 text-center text-xs font-mono text-slate-500">
              No documents ingested yet. Upload an MTC above to begin digital extraction.
            </div>
          ) : (
            <table className="w-full text-left text-xs font-mono border-collapse">
              <thead>
                <tr className="border-b border-slate-200 dark:border-slate-800 text-slate-500">
                  <th className="py-2 pr-3 font-semibold">DOC ID</th>
                  <th className="py-2 px-3 font-semibold">FILENAME</th>
                  <th className="py-2 px-3 font-semibold">TYPE</th>
                  <th className="py-2 px-3 font-semibold">CONFIDENCE</th>
                  <th className="py-2 px-3 font-semibold">UPLOADED</th>
                  <th className="py-2 pl-3 font-semibold text-right">INSPECT</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60">
                {recentDocs.map((doc) => (
                  <tr key={doc.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors">
                    <td className="py-2.5 pr-3 font-bold text-slate-900 dark:text-slate-100">
                      #{doc.id}
                    </td>
                    <td className="py-2.5 px-3 text-slate-800 dark:text-slate-200 truncate max-w-[280px]">
                      {doc.filename}
                    </td>
                    <td className="py-2.5 px-3 text-slate-600 dark:text-slate-400">
                      {doc.doc_type || 'MTC_CERTIFICATE'}
                    </td>
                    <td className="py-2.5 px-3 text-emerald-700 dark:text-emerald-400 font-semibold">
                      {((doc.confidence || 0.95) * 100).toFixed(1)}%
                    </td>
                    <td className="py-2.5 px-3 text-slate-500 text-[11px]">
                      {doc.created_at ? new Date(doc.created_at).toLocaleString('en-IN') : 'Recently'}
                    </td>
                    <td className="py-2.5 pl-3 text-right">
                      <button
                        onClick={() => {
                          if (typeof window !== 'undefined') {
                            sessionStorage.setItem('current_mtc', JSON.stringify(doc));
                          }
                          router.push('/upload/review');
                        }}
                        className="text-emerald-600 dark:text-emerald-400 hover:underline font-semibold"
                      >
                        Review &rarr;
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </Card>
      </div>
    </ProtectedRoute>
  );
}
