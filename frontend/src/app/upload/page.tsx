"use client";
import React, { useState } from 'react';
import { Card } from '@/components/ui';
import { Upload, FileText, CheckCircle2 } from 'lucide-react';
import { useRouter } from 'next/navigation';

export default function UploadPage() {
  const [isDragging, setIsDragging] = useState(false);
  const router = useRouter();

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    // Mock processing delay then redirect
    setTimeout(() => router.push('/upload/review'), 1000);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold font-mono">Document Intake</h1>
      </div>

      <div 
        onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        className={`border-2 border-dashed rounded-xl p-12 text-center transition-colors cursor-pointer ${
          isDragging ? 'border-emerald-500 bg-emerald-50 dark:bg-emerald-900/20' : 'border-slate-300 dark:border-slate-700 hover:border-slate-400'
        }`}
        onClick={() => setTimeout(() => router.push('/upload/review'), 1000)}
      >
        <Upload className="mx-auto h-12 w-12 text-slate-400 mb-4" />
        <h3 className="text-lg font-semibold">Drag & Drop MTC Certificates</h3>
        <p className="text-sm text-slate-500 mt-2">Support for PDF, Scanned Images (OCR powered)</p>
        <button className="mt-6 px-4 py-2 bg-slate-900 text-white rounded shadow hover:bg-slate-800 transition-colors">
          Browse Files
        </button>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <Card className="cursor-pointer hover:border-emerald-500 transition-colors" onClick={() => router.push('/upload/review')}>
          <div className="flex items-center gap-3 mb-2">
            <FileText className="text-blue-500" />
            <h4 className="font-semibold">Demo Preset 1</h4>
          </div>
          <p className="text-sm text-slate-500">ASTM A105 Carbon Steel Flange MTC (Clear scan)</p>
        </Card>
        <Card className="cursor-pointer hover:border-emerald-500 transition-colors" onClick={() => router.push('/upload/review')}>
          <div className="flex items-center gap-3 mb-2">
            <FileText className="text-amber-500" />
            <h4 className="font-semibold">Demo Preset 2</h4>
          </div>
          <p className="text-sm text-slate-500">Noisy SS316L Certificate with smudges</p>
        </Card>
      </div>
    </div>
  );
}
