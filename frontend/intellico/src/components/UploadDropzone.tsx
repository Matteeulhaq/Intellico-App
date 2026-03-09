"use client";

import { useCallback, useState } from "react";
import { Upload, FileText, Loader2 } from "lucide-react";
import { uploadPdf } from "@/lib/api";
import { useStore } from "@/lib/store";
import type { PaperRecord } from "@/types";
import { toast } from "sonner";

export function UploadDropzone({ onSuccess }: { onSuccess: () => void }) {
  const [drag, setDrag] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const addPaper = useStore((s) => s.addPaper);
  const setSelectedPaper = useStore((s) => s.setSelectedPaper);

  const handleUpload = useCallback(
    async (f: File) => {
      if (!f.name.toLowerCase().endsWith(".pdf")) {
        toast.error("Please upload a PDF file.");
        return;
      }
      setUploading(true);
      setFile(f);
      try {
        const res = await uploadPdf(f);
        const record: PaperRecord = {
          paper_id: res.paper_id,
          filename: res.data.filename,
          word_count: res.data.word_count,
          page_count: res.data.page_count,
          sections: res.data.sections,
          metadata: res.data.metadata,
          uploadedAt: Date.now(),
        };
        addPaper(record);
        setSelectedPaper(res.paper_id);
        toast.success("Paper uploaded and indexed successfully.");
        onSuccess();
      } catch (e) {
        toast.error(e instanceof Error ? e.message : "Upload failed.");
      } finally {
        setUploading(false);
        setFile(null);
      }
    },
    [addPaper, setSelectedPaper, onSuccess]
  );

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDrag(false);
      const f = e.dataTransfer.files[0];
      if (f) handleUpload(f);
    },
    [handleUpload]
  );

  const onDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDrag(true);
  }, []);

  const onDragLeave = useCallback(() => setDrag(false), []);

  const onFileChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const f = e.target.files?.[0];
      if (f) handleUpload(f);
      e.target.value = "";
    },
    [handleUpload]
  );

  return (
    <div className="flex flex-1 flex-col items-center justify-center px-6 py-10">
      <div
        onDrop={onDrop}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        className={`flex w-full max-w-xl flex-col items-center justify-center rounded-2xl border border-dashed bg-white/80 p-10 shadow-sm transition-colors ${
          drag
            ? "border-[var(--primary)] bg-[var(--muted)]"
            : "border-[var(--border)] hover:border-[var(--primary)]"
        }`}
      >
        {uploading ? (
          <>
            <Loader2 className="h-12 w-12 animate-spin text-[var(--primary)]" />
            <p className="mt-4 text-sm font-medium text-[var(--foreground)]">Processing…</p>
            {file && (
              <p className="mt-1 flex items-center gap-2 text-xs text-[var(--muted-foreground)]">
                <FileText className="h-3 w-3" />
                {file.name} ({(file.size / 1024).toFixed(1)} KB)
              </p>
            )}
          </>
        ) : (
          <>
            <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-[var(--primary)]/10 text-[var(--primary)]">
              <Upload className="h-7 w-7" />
            </div>
            <p className="mt-4 text-sm font-semibold text-[var(--foreground)]">
              Drag & drop a PDF here, or click to browse
            </p>
            <p className="mt-1 text-xs text-[var(--muted-foreground)]">
              Intellico analyzes dental research papers securely on-device.
            </p>
            <label className="mt-4 cursor-pointer">
              <input
                type="file"
                accept=".pdf"
                className="sr-only"
                onChange={onFileChange}
                disabled={uploading}
              />
              <span className="inline-flex h-10 items-center justify-center rounded-lg border border-[var(--primary)]/20 bg-[var(--primary)]/5 px-4 text-sm font-medium text-[var(--primary)] hover:bg-[var(--primary)]/10">
                Choose file
              </span>
            </label>
          </>
        )}
      </div>
    </div>
  );
}
