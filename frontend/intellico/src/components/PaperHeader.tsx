"use client";

import type { PaperRecord } from "@/types";

export function PaperHeader({ paper }: { paper: PaperRecord }) {
  const title = paper.metadata?.title || paper.filename || "Untitled";
  const meta = [
    paper.page_count != null && `${paper.page_count} pages`,
    paper.word_count != null && `${paper.word_count.toLocaleString()} words`,
  ]
    .filter(Boolean)
    .join(" · ");

  return (
    <header className="border-b border-[var(--border)] bg-white/95 px-6 py-4 backdrop-blur">
      <h2 className="text-lg font-semibold text-[var(--foreground)]">{title}</h2>
      {meta && <p className="mt-0.5 text-sm text-[var(--muted-foreground)]">{meta}</p>}
    </header>
  );
}
