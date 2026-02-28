"use client";

import { FileText, Plus } from "lucide-react";
import { useStore } from "@/lib/store";
import { Button } from "@/components/ui/Button";

export function Sidebar({ className = "" }: { className?: string }) {
  const { papers, selectedPaperId, setSelectedPaper, setShowUpload } = useStore();

  const onNewUpload = () => setShowUpload(true);

  return (
    <aside
      className={`flex w-64 flex-col border-r border-neutral-200 bg-neutral-50/50 ${className}`}
    >
      <div className="border-b border-neutral-200 p-4">
        <h1 className="text-xl font-semibold text-neutral-900">Intellico</h1>
        <p className="mt-0.5 text-xs text-neutral-500">Dental Research Assistant</p>
      </div>
      <div className="flex-1 overflow-y-auto p-3">
        <Button
          variant="outline"
          size="md"
          className="w-full gap-2"
          onClick={onNewUpload}
        >
          <Plus className="h-4 w-4" />
          New Upload
        </Button>
        <div className="mt-4 space-y-1">
          {papers.length === 0 && (
            <p className="px-2 py-4 text-center text-sm text-neutral-500">
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
                  ? "bg-white text-neutral-900 shadow-sm"
                  : "text-neutral-600 hover:bg-neutral-100 hover:text-neutral-900"
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
