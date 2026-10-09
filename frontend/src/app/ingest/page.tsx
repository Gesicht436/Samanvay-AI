"use client";

import { ChangeEvent, DragEvent, useEffect, useRef, useState } from "react";
import { submitDocumentForOcr, submitTextForParsing } from "../../lib/api";
import type { IngestResult } from "../../lib/types";

type InputMode = "camera" | "upload" | "text";
const ACCEPTED = ".pdf,.png,.jpg,.jpeg,.tiff,.bmp,.webp";
const MAX_UPLOAD_BYTES = 15 * 1024 * 1024;
const SUPPORTED_EXTENSIONS = new Set(ACCEPTED.split(","));

function hasValue(value: unknown): boolean {
  if (Array.isArray(value)) return value.some(hasValue);
  if (value && typeof value === "object") return Object.values(value).some(hasValue);
  return value !== null && value !== undefined && value !== "";
}

function formatValue(value: unknown): string {
  if (Array.isArray(value)) return value.map(formatValue).join(", ") || "Not found";
  if (value && typeof value === "object") return Object.entries(value)
    .filter(([, entry]) => hasValue(entry))
    .map(([key, entry]) => `${key.replaceAll("_", " ")}: ${formatValue(entry)}`)
    .join(" · ") || "Not found";
  return value === null || value === undefined || value === "" ? "Not found" : String(value);
}

function IngestResultPanel({ result }: { result: IngestResult | null }) {
  if (!result) return <section className="ingest-empty"><span className="empty-mark">+</span><p>Your extracted certificate will appear here.</p><small>Review low-confidence OCR before sending it downstream.</small></section>;
  const confidence = Math.round(result.confidence * 100);
  const metadata = result.parsed_metadata;
  const engineering = metadata.engineering_attributes;
  const engineeringFields = engineering
    ? Object.entries(engineering).filter(([key, value]) => key !== "raw_description" && hasValue(value))
    : [];
  const chemistry = Array.isArray(metadata.chemical_composition) ? metadata.chemical_composition as Array<{ element: string; value?: number | null; unit?: string | null }> : [];
  const mechanical = Array.isArray(metadata.mechanical_properties) ? metadata.mechanical_properties as Array<{ property: string; value?: number | null; unit?: string | null }> : [];
  const manufacturers = Array.isArray(metadata.manufacturer_list) ? metadata.manufacturer_list as string[] : [];
  const tpis = Array.isArray(metadata.tpi_list) ? metadata.tpi_list as string[] : [];
  const metadataFields = ["certificate_type", "certificate_number", "purchase_order", "material_grade", "governing_standard", "heat_numbers", "quantity", "yield_strength_mpa", "tensile_strength_mpa", "elongation_pct", "product_description"];
  return <section className="result-panel" aria-live="polite">
    <div className="result-heading"><div><p className="eyebrow">Extraction complete</p><h2>{result.filename ?? "Manual certificate text"}</h2></div><span className={`method-badge ${confidence < 75 ? "warning" : ""}`}>{result.extraction_method.replaceAll("_", " ")}</span></div>
    <div className="result-stats"><div><span>Confidence</span><strong className={confidence < 75 ? "amber" : ""}>{confidence}%</strong></div><div><span>Pages</span><strong>{result.page_count}</strong></div><div><span>Fields found</span><strong>{Object.entries(metadata).filter(([key, value]) => key !== "engineering_attributes" && hasValue(value)).length + engineeringFields.length}</strong></div></div>
    {confidence < 75 && <p className="confidence-warning">Low OCR confidence. Double-check the text or use Paste Text for a cleaner result.</p>}
    <div className="result-grid"><div><p className="eyebrow">Raw text</p><pre className="raw-text">{result.raw_text || "No text detected."}</pre></div><div><p className="eyebrow">Certificate details</p><dl className="metadata-list">{metadataFields.map((key) => <div key={key}><dt>{key.replaceAll("_", " ")}</dt><dd>{formatValue(metadata[key])}</dd></div>)}</dl></div></div>
    {chemistry.length > 0 && <section className="ingest-data-section"><p className="eyebrow">Chemical composition</p><div className="table-scroll"><table className="ingest-table"><thead><tr><th>Element</th><th>Value</th><th>Unit</th></tr></thead><tbody>{chemistry.map((entry, index) => <tr key={`${entry.element}-${index}`}><td>{entry.element}</td><td>{formatValue(entry.value)}</td><td>{entry.unit ?? "%"}</td></tr>)}</tbody></table></div></section>}
    {mechanical.length > 0 && <section className="ingest-data-section"><p className="eyebrow">Mechanical properties</p><div className="table-scroll"><table className="ingest-table"><thead><tr><th>Property</th><th>Value</th><th>Unit</th></tr></thead><tbody>{mechanical.map((entry, index) => <tr key={`${entry.property}-${index}`}><td>{entry.property.replaceAll("_", " ")}</td><td>{formatValue(entry.value)}</td><td>{entry.unit ?? "—"}</td></tr>)}</tbody></table></div></section>}
    {engineeringFields.length > 0 && <section className="ingest-data-section"><p className="eyebrow">Engineering & procurement attributes</p><dl className="metadata-list">{engineeringFields.map(([key, value]) => <div key={key}><dt>{key.replaceAll("_", " ")}</dt><dd>{formatValue(value)}</dd></div>)}</dl></section>}
    {(manufacturers.length > 0 || tpis.length > 0) && <section className="ingest-data-section"><p className="eyebrow">Recognized manufacturer & TPI values</p><dl className="metadata-list">
      {manufacturers.length > 0 && <div><dt>Manufacturers</dt><dd>{manufacturers.join(", ")}</dd></div>}
      {tpis.length > 0 && <div><dt>TPI / inspection agencies</dt><dd>{tpis.join(", ")}</dd></div>}
    </dl></section>}
    {result.ocr_profile && result.pages?.some((page) => page.ocr_engine) && <section className="ingest-data-section"><p className="eyebrow">OCR configuration</p><p className="text-sm text-slate-600">{result.ocr_profile.routing.replaceAll("_", " ")} · {result.ocr_profile.raster_dpi} DPI · {result.ocr_profile.preprocessing.join(", ")} · {result.ocr_profile.primary_engine} with {result.ocr_profile.fallback_engine} fallback</p></section>}
    {result.pages && result.pages.some((page) => page.ocr_engine) && <section className="ingest-data-section"><p className="eyebrow">Per-page OCR routing</p><div className="table-scroll"><table className="ingest-table"><thead><tr><th>Page</th><th>Method</th><th>Engine</th><th>Raster</th></tr></thead><tbody>{result.pages.map((page) => <tr key={page.page}><td>{page.page}</td><td>{page.extraction_method?.replaceAll("_", " ") ?? "native text"}</td><td>{page.ocr_engine ?? "—"}</td><td>{page.raster_dpi ? `${page.raster_dpi} DPI` : "—"}</td></tr>)}</tbody></table></div></section>}
  </section>;
}

export default function IngestPage() {
  const [mode, setMode] = useState<InputMode>("camera");
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [text, setText] = useState("");
  const [result, setResult] = useState<IngestResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [cameraError, setCameraError] = useState<string | null>(null);
  const [cameraActive, setCameraActive] = useState(false);
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const streamRef = useRef<MediaStream | null>(null);

  const stopCamera = () => { streamRef.current?.getTracks().forEach((track) => track.stop()); streamRef.current = null; setCameraActive(false); };
  const openCamera = async () => {
    setCameraError(null);
    try { const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" } }); streamRef.current = stream; if (videoRef.current) videoRef.current.srcObject = stream; setCameraActive(true); }
    catch { setCameraError("Camera access was denied. Use the Upload PDF tab to choose a PDF or image instead."); setMode("upload"); }
  };
  useEffect(() => () => stopCamera(), []);
  useEffect(() => { if (mode === "camera" && !file && !preview) void openCamera(); if (mode !== "camera") stopCamera(); }, [mode]);

  const capture = () => { const video = videoRef.current; const canvas = canvasRef.current; if (!video || !canvas) return; canvas.width = video.videoWidth; canvas.height = video.videoHeight; canvas.getContext("2d")?.drawImage(video, 0, 0); canvas.toBlob((blob) => { if (!blob) return; setFile(new File([blob], "capture.jpg", { type: "image/jpeg" })); setPreview(URL.createObjectURL(blob)); stopCamera(); }, "image/jpeg", 0.9); };
  const chooseFile = (chosen: File | undefined) => {
    if (!chosen) return;
    const extension = `.${chosen.name.split(".").pop()?.toLowerCase() ?? ""}`;
    if (!SUPPORTED_EXTENSIONS.has(extension)) { setError("Use a PDF, JPG, PNG, TIFF, BMP, or WEBP document."); return; }
    if (chosen.size > MAX_UPLOAD_BYTES) { setError("File is too large. Maximum upload size is 15 MB."); return; }
    setFile(chosen);
    setPreview(chosen.type.startsWith("image/") ? URL.createObjectURL(chosen) : null);
    setError(null);
    setResult(null);
  };
  const onDrop = (event: DragEvent<HTMLDivElement>) => { event.preventDefault(); event.stopPropagation(); chooseFile(event.dataTransfer.files[0]); };
  const onFileChange = (event: ChangeEvent<HTMLInputElement>) => { chooseFile(event.target.files?.[0]); event.target.value = ""; };
  const submit = async () => {
    setError(null); setResult(null); setLoading(true);
    try { if (mode === "text") { if (!text.trim()) throw new Error("Paste certificate text before submitting."); setResult(await submitTextForParsing(text)); } else { if (!file) throw new Error(mode === "camera" ? "Capture a document photo first." : "Choose a document first."); setResult(await submitDocumentForOcr(file)); } }
    catch (cause) { setError(cause instanceof Error ? cause.message : "Unable to process this input."); }
    finally { setLoading(false); }
  };
  const selectMode = (next: InputMode) => { setMode(next); setError(null); setResult(null); if (next !== "camera") stopCamera(); };

  return <main className="ingest-page"><div className="ingest-intro"><div><p className="eyebrow">Operations / document intake</p><h1>Turn a document into<br /><em>usable evidence.</em></h1></div><p className="intro-copy">Capture a certificate in the field, upload a source file, or paste the text directly. Every path returns the same normalized material record.</p></div>
    <section className="ingest-workspace"><div className="input-column"><div className="mode-tabs" role="tablist">{([["camera", "Capture Photo", "01"], ["upload", "Upload PDF", "02"], ["text", "Paste Text", "03"]] as const).map(([value, label, number]) => <button key={value} className={mode === value ? "active" : ""} onClick={() => selectMode(value)} role="tab" aria-selected={mode === value}><span>{number}</span>{label}</button>)}</div>
      <div className="input-card">
        {mode === "camera" && <div className="camera-panel">{preview ? <><img src={preview} alt="Captured certificate" className="capture-preview" /><button className="secondary-button" onClick={() => { setPreview(null); setFile(null); void openCamera(); }}>Retake photo</button></> : <><div className="camera-frame">{cameraActive ? <video ref={videoRef} autoPlay playsInline muted /> : <div className="camera-placeholder"><span>◎</span><p>Preparing camera</p></div>}<div className="scan-corners" /></div><canvas ref={canvasRef} className="hidden" /><button className="capture-button" onClick={capture} disabled={!cameraActive}>Capture frame</button>{cameraError && <p className="inline-error">{cameraError}</p>}</>}</div>}
        {mode === "upload" && <div className="upload-panel"><div className="drop-zone" role="button" tabIndex={0} onClick={() => fileInputRef.current?.click()} onKeyDown={(event) => { if (event.key === "Enter" || event.key === " ") { event.preventDefault(); fileInputRef.current?.click(); } }} onDragOver={(event) => { event.preventDefault(); event.dataTransfer.dropEffect = "copy"; }} onDrop={onDrop}><input ref={fileInputRef} id="document-file" type="file" accept={ACCEPTED} onClick={(event) => event.stopPropagation()} onChange={onFileChange} tabIndex={-1} /><div><span className="upload-icon">↑</span><strong>Drop a document here</strong><small>or click to browse · PDF, JPG, PNG, TIFF, BMP, WEBP · 15 MB max</small></div></div>{file && <div className="selected-file">{preview ? <img src={preview} alt="Selected document" /> : <span className="file-icon">PDF</span>}<div><strong>{file.name}</strong><small>{(file.size / 1024 / 1024).toFixed(2)} MB</small></div><button onClick={() => { setFile(null); setPreview(null); }} aria-label="Remove selected file">×</button></div>}</div>}
        {mode === "text" && <div className="text-panel"><label htmlFor="raw-text">Certificate or material text</label><textarea id="raw-text" value={text} onChange={(event) => setText(event.target.value)} placeholder="Paste the OCR output or type the certificate details here..." /><small>{text.length} characters · manual parsing runs at full confidence</small></div>}
        <button className="submit-button" onClick={submit} disabled={loading}>{loading ? <><span className="spinner" />Processing document...</> : <>Process {mode === "camera" ? "photo" : mode === "upload" ? "file" : "text"} <span>→</span></>}</button>
        {error && <p className="inline-error">{error}</p>}
      </div></div><div className="result-column"><IngestResultPanel result={result} /></div></section>
  </main>;
}
