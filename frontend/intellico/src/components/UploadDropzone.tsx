"use client";

import { useCallback, useState } from "react";
import { Upload, FileText, Loader2 } from "lucide-react";
import { uploadPdf, getPaperStatus, getPaper } from "@/lib/api";
import { useStore } from "@/lib/store";
import type { PaperRecord } from "@/types";
import { toast } from "sonner";

export function UploadDropzone({ onSuccess }: { onSuccess: () => void }) {
  const [drag, setDrag] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const addPaper = useStore((s) => s.addPaper);
  const setSelectedPaper = useStore((s) => s.setSelectedPaper);

  const pollStatus = useCallback(async (paperId: string): Promise<boolean> => {
    const maxAttempts = 60; // 2 minutes total (60 * 2s)
    const pollInterval = 2000; // 2 seconds

    for (let attempt = 0; attempt < maxAttempts; attempt++) {
      try {
        const status = await getPaperStatus(paperId);
        if (status.status === "ready") {
          // FIX: Fetch and update metadata when processing completes
          const paper = await getPaper(paperId);
          if (paper.extracted_metadata) {
            // Get fresh reference to avoid dependency issues
            const { updatePaperMetadata: refreshMetadata } = useStore.getState();
            refreshMetadata(paperId, paper);
            console.log("Metadata updated:", paper.extracted_metadata);
          }

          toast.success("Paper processing complete!");
          return true;
        }
        await new Promise(resolve => setTimeout(resolve, pollInterval));
      } catch (error) {
        console.error("Status check failed:", error);
        await new Promise(resolve => setTimeout(resolve, pollInterval));
      }
    }

    toast.error("Processing is taking longer than expected. Please wait a moment and refresh.");
    return false;
  }, []); // Empty dependency array - get fresh reference in callback

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

        // Start background processing polling
        setUploading(false);
        setProcessing(true);
        toast.info("Processing paper in background... (this may take 1-2 minutes)");

        const ready = await pollStatus(res.paper_id);
        setProcessing(ready);

        if (ready) {
          onSuccess();
        }
      } catch (e) {
        toast.error(e instanceof Error ? e.message : "Upload failed.");
      } finally {
        setUploading(false);
        setProcessing(false);
        setFile(null);
      }
    },
    [addPaper, setSelectedPaper, onSuccess, pollStatus]
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
        {uploading || processing ? (
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
                disabled={uploading || processing}
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
