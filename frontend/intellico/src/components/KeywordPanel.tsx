"use client";

import { useState, useMemo } from "react";
import { Search } from "lucide-react";
import { Input } from "@/components/ui/Input";
import { Card } from "@/components/ui/Card";
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
  const keywords = useMemo(() => normalizeKeywords(paper.metadata), [paper.metadata]);
  const filtered = useMemo(() => {
    if (!search.trim()) return keywords;
    const q = search.toLowerCase();
    return keywords.filter((k) => k.toLowerCase().includes(q));
  }, [keywords, search]);

  return (
    <div className="flex flex-1 flex-col gap-4 bg-[var(--background)] p-6">
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
          <p className="text-sm text-[var(--muted-foreground)]">
            No keywords extracted for this paper. Keywords come from upload metadata.
          </p>
          <p className="mt-2 text-xs text-[var(--muted-foreground)]/80">
            Concept relationships are visualized in the Flowchart tab.
          </p>
        </Card>
      ) : (
        <>
          <Card>
            <h4 className="mb-3 text-sm font-medium text-[var(--foreground)]">Keywords</h4>
            <ul className="flex flex-wrap gap-2">
              {filtered.map((k) => (
                <li
                  key={k}
                  className="rounded-md bg-[var(--secondary)] px-3 py-1.5 text-sm text-[var(--secondary-foreground)]"
                >
                  {k}
                </li>
              ))}
            </ul>
          </Card>
          <Card>
            <h4 className="mb-3 text-sm font-medium text-[var(--foreground)]">Relationships</h4>
            <p className="text-sm text-[var(--muted-foreground)]">
              Concept relationships (A → B) are shown in the Flowchart tab. Open the Flowchart tab
              to view the visual diagram.
            </p>
          </Card>
        </>
      )}
    </div>
  );
}
