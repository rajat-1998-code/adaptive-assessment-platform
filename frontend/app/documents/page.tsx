"use client";

import { useEffect, useRef, useState } from "react";

import { ApiError } from "@/lib/api";
import { documentService } from "@/services/documents/document.service";
import type { DocumentListOptions, DocumentMetadata, DocumentSortBy, PaginatedDocuments } from "@/types/api";

const MAX_BYTES = 25 * 1024 * 1024;
const TYPES = ["pdf", "docx", "txt", "md", "pptx", "png", "jpg", "jpeg"];
const INITIAL: DocumentListOptions = { page: 1, page_size: 20, search: "", file_type: "", status: "", sort_by: "created_at", sort_order: "desc" };

function Icon({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" className={`h-5 w-5 ${className}`}>{children}</svg>;
}

function size(value: number | null) {
  if (value === null) return "Unknown size";
  if (value < 1024) return `${value} B`;
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KB`;
  return `${(value / (1024 * 1024)).toFixed(1)} MB`;
}

function date(value: string) { return new Intl.DateTimeFormat(undefined, { dateStyle: "medium" }).format(new Date(value)); }
function typeOf(document: DocumentMetadata) { return document.original_filename.split(".").pop()?.toUpperCase() ?? "FILE"; }
function message(error: unknown) { return error instanceof ApiError || error instanceof Error ? error.message : "Something went wrong. Please try again."; }

function DocumentRow({ document }: { document: DocumentMetadata }) {
  return <div className="flex flex-col gap-4 border-b border-white/[.07] px-5 py-5 transition hover:bg-white/[.025] md:flex-row md:items-center md:gap-6">
    <div className="flex min-w-0 flex-1 items-center gap-4"><span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl border border-white/10 bg-white/[.04] text-[#ff9a3d]"><Icon><path d="M6 3.5h8l4 4V20a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V4.5a1 1 0 0 1 1-1Z" /><path d="M14 3.5V8h4" /></Icon></span><div className="min-w-0"><p className="truncate font-medium text-white">{document.title}</p><p className="mt-1 truncate text-sm text-slate-500">{document.original_filename}</p></div></div>
    <div className="flex items-center gap-5 pl-[60px] text-sm md:pl-0"><span className="rounded-md border border-[#ff9a3d]/25 bg-[#ff9a3d]/10 px-2.5 py-1 text-xs font-semibold text-[#ffb477]">{typeOf(document)}</span><span className="min-w-20 text-slate-400">{size(document.file_size)}</span><span className="min-w-28 text-slate-500">{date(document.created_at)}</span><span className="inline-flex items-center gap-2 rounded-full bg-emerald-400/10 px-2.5 py-1 text-xs text-emerald-300"><i className="h-1.5 w-1.5 rounded-full bg-emerald-400" />{document.processing_status}</span></div>
  </div>;
}

export default function DocumentsPage() {
  const [options, setOptions] = useState(INITIAL);
  const [result, setResult] = useState<PaginatedDocuments | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [dragging, setDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [refresh, setRefresh] = useState(0);
  const fileInput = useRef<HTMLInputElement>(null);

  useEffect(() => {
    let active = true;
    const timer = window.setTimeout(() => {
      setLoading(true);
      void documentService.list(options).then(({ data }) => { if (active) { setResult(data); setError(null); } }).catch((requestError: unknown) => { if (active) setError(message(requestError)); }).finally(() => { if (active) setLoading(false); });
    }, options.search ? 250 : 0);
    return () => { active = false; window.clearTimeout(timer); };
  }, [options, refresh]);

  useEffect(() => {
    function clearOnEscape(event: KeyboardEvent) {
      if (event.key === "Escape" && file) {
        setFile(null);
        setUploadError(null);
        if (fileInput.current) fileInput.current.value = "";
      }
    }
    window.addEventListener("keydown", clearOnEscape);
    return () => window.removeEventListener("keydown", clearOnEscape);
  }, [file]);

  function update(patch: Partial<DocumentListOptions>) { setOptions((current) => ({ ...current, ...patch, page: patch.page ?? 1 })); }
  function choose(next: File | null) {
    setFile(next); setUploadError(null);
    if (!next) return;
    const extension = next.name.split(".").pop()?.toLowerCase();
    if (!extension || !TYPES.includes(extension)) setUploadError(`Supported files: ${TYPES.join(", ")}.`);
    else if (next.size > MAX_BYTES) setUploadError("Files must be 25 MiB or smaller.");
  }
  async function upload() {
    if (!file || uploadError) return;
    setUploading(true);
    try { await documentService.upload(file); setFile(null); if (fileInput.current) fileInput.current.value = ""; setRefresh((value) => value + 1); }
    catch (requestError) { setUploadError(message(requestError)); }
    finally { setUploading(false); }
  }

  return <main className="relative flex-1 px-5 py-6 md:px-10 md:py-9"><div className="pointer-events-none absolute inset-0 -z-10 bg-[radial-gradient(circle_at_50%_0%,rgba(255,138,42,.12),transparent_35%)]" /><div className="mx-auto max-w-6xl">
    <div className="rounded-2xl border border-white/10 bg-[#0b0f12]/75 p-5 shadow-2xl shadow-black/20 md:p-6"><div className="grid gap-5 md:grid-cols-[minmax(0,.8fr)_minmax(520px,1.2fr)] md:items-start"><div><div className="flex items-center gap-4 pt-2"><Icon className="h-8 w-8 text-[#ff9a3d]"><path d="M3.5 6.5A2.5 2.5 0 0 1 6 4h5l2 2h5A2.5 2.5 0 0 1 20.5 8.5v9A2.5 2.5 0 0 1 18 20H6a2.5 2.5 0 0 1-2.5-2.5z" /></Icon><h1 className="mono-ui text-2xl font-semibold uppercase tracking-[.14em] text-[#ff9a3d]">Document library</h1></div><p className="mt-4 text-base text-white">Upload and organize the learning material that powers your assessments.</p></div>

    <div onDragOver={(event) => { event.preventDefault(); setDragging(true); }} onDragLeave={() => setDragging(false)} onDrop={(event) => { event.preventDefault(); setDragging(false); choose(event.dataTransfer.files[0] ?? null); }} className={`relative flex h-full min-h-[240px] flex-col items-center justify-center rounded-2xl border border-dashed px-6 py-6 text-center transition md:pr-48 ${dragging ? "border-[#ff9a3d] bg-[#ff9a3d]/10" : "border-white/20 bg-[#0d1114]/70"}`}><span className="rounded-2xl bg-[#ff9a3d]/10 p-4 text-[#ff9a3d]"><Icon className="h-7 w-7"><path d="M12 16V4m0 0L7.5 8.5M12 4l4.5 4.5" /><path d="M5 14.5A4.5 4.5 0 0 0 5.5 23h13a4 4 0 0 0 .6-7.95A7 7 0 0 0 5 14.5Z" /></Icon></span><p className="mt-5 text-lg font-medium text-white">Drop a document here</p><p className="mt-2 text-sm text-slate-400">or <button type="button" onClick={() => fileInput.current?.click()} className="font-medium text-[#ff9a3d] hover:text-[#ffc18d]">browse your device</button></p><input ref={fileInput} type="file" className="sr-only" accept={TYPES.map((type) => `.${type}`).join(",")} onChange={(event) => choose(event.target.files?.[0] ?? null)} /><div className="mt-5 flex flex-wrap justify-center gap-2">{TYPES.map((type) => <span key={type} className="mono-ui rounded-md border border-white/10 px-2.5 py-1 text-[.65rem] text-slate-400">.{type}</span>)}</div><p className="mt-3 text-xs text-slate-500">PDF, DOCX, TXT, MD, PPTX, PNG, JPG, JPEG · max 25 MiB</p>{file && <p className="mt-3 max-w-full truncate text-sm text-slate-300">{file.name}</p>}{uploadError && <p className="mt-3 text-sm text-red-300">{uploadError}</p>}<button type="button" disabled={!file || Boolean(uploadError) || uploading} onClick={() => void upload()} className="mt-5 rounded-lg bg-[#e8791b] px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-orange-950/30 transition hover:bg-[#ff9a3d] disabled:cursor-not-allowed disabled:opacity-40 md:absolute md:right-8 md:top-1/2 md:mt-0 md:-translate-y-1/2">{uploading ? "Uploading…" : "Upload document"}</button></div></div></div>

    <section className="mt-8 overflow-hidden rounded-2xl border border-white/10 bg-[#0c1012]/85"><div className="flex flex-col gap-4 border-b border-white/10 p-5 md:flex-row md:items-center md:justify-between"><div><h2 className="text-lg font-medium text-white">Your uploaded documents</h2><p className="mt-1 text-sm text-slate-500">Search and organize your own files.</p></div><div className="flex flex-col gap-2 sm:flex-row"><input value={options.search} onChange={(event) => update({ search: event.target.value })} placeholder="Search title or filename" className="rounded-lg border border-white/10 bg-black/20 px-3 py-2.5 text-sm text-white placeholder:text-slate-600" /><select value={options.file_type} onChange={(event) => update({ file_type: event.target.value })} className="rounded-lg border border-white/10 bg-black/20 px-3 py-2.5 text-sm text-slate-300"><option value="">All types</option>{TYPES.map((type) => <option key={type} value={type}>{type.toUpperCase()}</option>)}</select><select value={`${options.sort_by}:${options.sort_order}`} onChange={(event) => { const [sort_by, sort_order] = event.target.value.split(":") as [DocumentSortBy, "asc" | "desc"]; update({ sort_by, sort_order }); }} className="rounded-lg border border-white/10 bg-black/20 px-3 py-2.5 text-sm text-slate-300"><option value="created_at:desc">Newest first</option><option value="created_at:asc">Oldest first</option><option value="title:asc">Title A–Z</option><option value="title:desc">Title Z–A</option></select></div></div>{error ? <div className="p-14 text-center text-sm text-red-200"><p>{error}</p><button type="button" onClick={() => setRefresh((value) => value + 1)} className="mt-3 underline">Try again</button></div> : loading ? <div className="p-16 text-center text-sm text-slate-500">Loading documents…</div> : result?.items.length ? <>{result.items.map((document) => <DocumentRow key={document.id} document={document} />)}</> : <div className="p-16 text-center"><p className="text-lg font-medium text-white">No uploads yet</p><p className="mt-2 text-sm text-slate-500">Upload your first document to add it to your private library.</p></div>}{result && result.pages > 1 && <div className="flex items-center justify-between border-t border-white/10 p-5 text-sm text-slate-500"><span>Page {result.page} of {result.pages}</span><div className="flex gap-2"><button type="button" disabled={result.page <= 1} onClick={() => update({ page: result.page - 1 })} className="rounded-lg border border-white/10 px-3 py-2 text-slate-300 disabled:opacity-30">Previous</button><button type="button" disabled={result.page >= result.pages} onClick={() => update({ page: result.page + 1 })} className="rounded-lg border border-white/10 px-3 py-2 text-slate-300 disabled:opacity-30">Next</button></div></div>}</section>
  </div></main>;
}
