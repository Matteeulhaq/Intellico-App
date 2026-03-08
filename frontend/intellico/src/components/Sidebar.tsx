"use client";

import Image from "next/image";
import { FileText, Plus } from "lucide-react";
import { useStore } from "@/lib/store";
import { Button } from "@/components/ui/Button";

export function Sidebar({ className = "" }: { className?: string }) {
  const { papers, selectedPaperId, setSelectedPaper, setShowUpload } = useStore();

  const onNewUpload = () => {
    setSelectedPaper(null);
    setShowUpload(true);
  };

  return (
    <aside
      className={`flex w-64 flex-col border-r border-[var(--sidebar-border)] bg-[var(--sidebar)] text-[var(--sidebar-foreground)] ${className}`}
    >
      <div className="px-4 pt-4 pb-3">
        <Image
          src="/logo_transparent.png"
          alt="Intellico"
          width={180}
          height={40}
          className="h-auto w-[180px] object-contain"
          priority
        />
      </div>
      <div className="flex-1 overflow-y-auto px-4 pb-4 pt-1">
        <Button
          variant="primary"
          size="md"
          className="w-full gap-2 shadow-sm shadow-[var(--sidebar-ring)]/20"
          onClick={onNewUpload}
        >
          <Plus className="h-4 w-4" />
          New Upload
        </Button>
        <div className="mt-5 space-y-1 text-xs font-medium uppercase tracking-wide text-[var(--sidebar-accent-foreground)]/70">
          <span className="px-2">Recent Papers</span>
        </div>
        <div className="mt-2 space-y-1">
          {papers.length === 0 && (
            <p className="px-2 py-4 text-center text-xs text-[var(--sidebar-accent-foreground)]/70">
              No papers yet. Upload a PDF to get started.
            </p>
          )}
          {papers.map((p) => (
            <button
              key={p.paper_id}
              type="button"
              onClick={() => setSelectedPaper(p.paper_id)}
              className={`flex w-full items-center gap-2 rounded-lg px-3 py-2.5 text-left text-sm transition-colors ${
                selectedPaperId === p.paper_id
                  ? "bg-[var(--sidebar-accent)] text-white"
                  : "text-[var(--sidebar-accent-foreground)] hover:bg-white/5 hover:text-white"
              }`}
            >
              <FileText className="h-4 w-4 shrink-0" />
              <span className="truncate">{p.filename || p.paper_id.slice(0, 8)}</span>
            </button>
          ))}
        </div>
      </div>
    </aside>
  );
}
