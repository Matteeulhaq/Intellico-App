"use client";

import { useState, useMemo, useEffect } from "react";
import { Search, Loader2 } from "lucide-react";
import { Input } from "@/components/ui/Input";
import { Card } from "@/components/ui/Card";
import { getPaperStatus, getPaper } from "@/lib/api";
import { useStore } from "@/lib/store";
import type { PaperRecord } from "@/types";

function normalizeKeywords(meta: PaperRecord["metadata"]): string[] {
  const kw = meta?.keywords;
  if (!kw) return [];
  if (Array.isArray(kw)) return kw.filter(Boolean).map(String);
  if (typeof kw === "string") return kw.split(/[,;]/).map((s) => s.trim()).filter(Boolean);
  return [];
}

export function KeywordPanel({ paper }: { paper: PaperRecord }) {
  const [search, setSearch] = useState("");
  const [processing, setProcessing] = useState(false);
  const keywords = useMemo(() => normalizeKeywords(paper.metadata), [paper.metadata]);
  const filtered = useMemo(() => {
    if (!search.trim()) return keywords;
    const q = search.toLowerCase();
    return keywords.filter((k) => k.toLowerCase().includes(q));
  }, [keywords, search]);

  // Check if paper is still processing when keywords are empty
  useEffect(() => {
    if (keywords.length === 0) {
      getPaperStatus(paper.paper_id)
        .then(async (status) => {
          const isProcessing = status.status === "processing";
          setProcessing(isProcessing);

          // FIX: If processing just completed, refresh metadata
          if (!isProcessing) {
            try {
              const paperData = await getPaper(paper.paper_id);
              if (paperData.extracted_metadata) {
                // Get fresh reference to avoid dependency issues
                const { updatePaperMetadata: refreshMetadata } = useStore.getState();
                refreshMetadata(paper.paper_id, paperData);
                console.log("Keywords refreshed:", paperData.extracted_metadata.keywords);
              }
            } catch (error) {
              console.error("Failed to refresh metadata:", error);
            }
          }
        })
        .catch(() => {
          setProcessing(false);
        });
    } else {
      setProcessing(false);
    }
  }, [paper.paper_id, keywords.length]); // Removed updatePaperMetadata dependency

  return (
    <div className="flex flex-1 flex-col gap-4 p-6">
      <div className="flex items-center gap-2">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-neutral-400" />
          <Input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search keywords…"
            className="pl-9"
          />
        </div>
      </div>
      {keywords.length === 0 ? (
        <Card className="p-8 text-center">
          {processing ? (
            <>
              <Loader2 className="mx-auto h-8 w-8 animate-spin text-neutral-400" />
              <p className="mt-4 text-sm text-neutral-600">
                Extracting keywords and metadata...
              </p>
              <p className="mt-2 text-xs text-neutral-500">
                This typically takes 1-2 minutes after upload.
              </p>
            </>
          ) : (
            <>
              <p className="text-sm text-neutral-500">
                No keywords extracted for this paper. Keywords come from upload metadata.
              </p>
              <p className="mt-2 text-xs text-neutral-400">
                Concept relationships are visualized in the Flowchart tab.
              </p>
            </>
          )}
        </Card>
      ) : (
        <>
          <Card>
            <h4 className="mb-3 text-sm font-medium text-neutral-700">Keywords</h4>
            <ul className="flex flex-wrap gap-2">
              {filtered.map((k) => (
                <li
                  key={k}
                  className="rounded-md bg-neutral-100 px-3 py-1.5 text-sm text-neutral-800"
                >
                  {k}
                </li>
              ))}
            </ul>
          </Card>
          <Card>
            <h4 className="mb-3 text-sm font-medium text-neutral-700">Relationships</h4>
            <p className="text-sm text-neutral-500">
              Concept relationships (A → B) are shown in the Flowchart tab. Open the Flowchart tab
              to view the visual diagram.
            </p>
          </Card>
        </>
      )}
    </div>
  );
}
