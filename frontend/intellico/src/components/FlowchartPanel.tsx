"use client";

import { useEffect, useState } from "react";
import { Download, Loader2, AlertCircle } from "lucide-react";
import { getFlowchart } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { toast } from "sonner";

export function FlowchartPanel({ paperId }: { paperId: string }) {
  const [svgUrl, setSvgUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    let url: string | null = null;
    setLoading(true);
    setError(null);
    setSvgUrl((prev) => {
      if (prev) URL.revokeObjectURL(prev);
      return null;
    });
    getFlowchart(paperId)
      .then((blob) => {
        if (cancelled) return;
        url = URL.createObjectURL(blob);
        setSvgUrl(url);
      })
      .catch((e) => {
        if (cancelled) return;
        const msg = e instanceof Error ? e.message : "Flowchart generation failed";
        setError(msg);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
      if (url) URL.revokeObjectURL(url);
    };
  }, [paperId]);

  const handleDownload = () => {
    if (!svgUrl) return;
    const a = document.createElement("a");
    a.href = svgUrl;
    a.download = `${paperId}_flowchart.svg`;
    a.click();
    toast.success("Flowchart downloaded.");
  };

  if (loading) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center gap-4 p-8">
        <Loader2 className="h-10 w-10 animate-spin text-[var(--primary)]" />
        <p className="text-sm text-[var(--muted-foreground)]">Generating flowchart…</p>
      </div>
    );
  }

  if (error) {
    const isMemory = /memory|oom|cuda|gpu/i.test(error);
    return (
      <div className="flex flex-1 flex-col items-center justify-center gap-4 bg-[var(--background)] p-8">
        <AlertCircle className="h-12 w-12 text-[var(--accent)]" />
        <p className="max-w-md text-center text-sm text-[var(--foreground)]">{error}</p>
        {isMemory && (
          <p className="max-w-md text-center text-xs text-[var(--muted-foreground)]">
            Try a shorter paper or run again. The backend clears GPU memory between requests.
          </p>
        )}
        <Button variant="outline" onClick={() => window.location.reload()}>
          Retry
        </Button>
      </div>
    );
  }

  if (!svgUrl) return null;

  return (
    <div className="flex flex-1 flex-col overflow-hidden bg-[var(--background)] p-6">
      <div className="mb-4 flex justify-end">
        <Button variant="outline" size="sm" className="gap-2" onClick={handleDownload}>
          <Download className="h-4 w-4" />
          Download SVG
        </Button>
      </div>
      <div className="flex-1 overflow-auto rounded-xl border border-neutral-200 bg-white p-4">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={svgUrl}
          alt="Concept flowchart"
          className="max-w-full"
          style={{ minHeight: 300 }}
        />
      </div>
    </div>
  );
}
