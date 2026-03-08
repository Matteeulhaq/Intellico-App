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
    <header className="border-b border-neutral-200 bg-white px-6 py-4">
      <h2 className="text-lg font-semibold text-neutral-900">{title}</h2>
      {meta && <p className="mt-0.5 text-sm text-neutral-500">{meta}</p>}
    </header>
  );
}
