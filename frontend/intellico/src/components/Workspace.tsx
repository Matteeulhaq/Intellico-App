"use client";

import { useEffect } from "react";
import { PaperHeader } from "./PaperHeader";
import { SummaryTabs } from "./SummaryTabs";
import { ChatPanel } from "./ChatPanel";
import { KeywordPanel } from "./KeywordPanel";
import { FlowchartPanel } from "./FlowchartPanel";
import { UploadDropzone } from "./UploadDropzone";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/Tabs";
import { useStore } from "@/lib/store";

export function Workspace() {
  const showUpload = useStore((s) => s.showUpload);
  const setShowUpload = useStore((s) => s.setShowUpload);
  const selectedPaperId = useStore((s) => s.selectedPaperId);
  const setSelectedPaper = useStore((s) => s.setSelectedPaper);
  const getPaper = useStore((s) => s.getPaper);
  const papers = useStore((s) => s.papers);

  const paper = selectedPaperId ? getPaper(selectedPaperId) : undefined;

  const onUploadSuccess = () => setShowUpload(false);

  const showUploadView = showUpload || papers.length === 0;

  useEffect(() => {
    if (papers.length > 0 && !selectedPaperId && !showUpload) {
      setSelectedPaper(papers[0].paper_id);
    }
  }, [papers.length, selectedPaperId, showUpload, setSelectedPaper]);

  if (showUploadView && !paper) {
    return (
      <div className="flex flex-1 flex-col">
        {papers.length > 0 && (
          <div className="flex items-center gap-4 border-b border-neutral-200 px-6 py-3">
            <button
              type="button"
              onClick={() => setShowUpload(false)}
              className="text-sm text-neutral-600 hover:text-neutral-900"
            >
              ← Back
            </button>
          </div>
        )}
        <UploadDropzone onSuccess={onUploadSuccess} />
      </div>
    );
  }

  if (!paper) return null;

  return (
    <div className="flex flex-1 flex-col overflow-hidden bg-[var(--background)]">
      <PaperHeader paper={paper} />
      <Tabs defaultValue="summary" className="flex flex-1 flex-col overflow-hidden">
        <div className="border-b border-[var(--border)] bg-white px-6">
          <TabsList className="w-full justify-start gap-0 rounded-none border-0 bg-transparent p-0">
            <TabsTrigger
              value="summary"
              className="rounded-none border-b-2 border-transparent data-[state=active]:border-[var(--primary)] data-[state=active]:bg-transparent data-[state=active]:shadow-none"
            >
              Summary
            </TabsTrigger>
            <TabsTrigger
              value="qa"
              className="rounded-none border-b-2 border-transparent data-[state=active]:border-[var(--primary)] data-[state=active]:bg-transparent data-[state=active]:shadow-none"
            >
              Q&A
            </TabsTrigger>
            <TabsTrigger
              value="keywords"
              className="rounded-none border-b-2 border-transparent data-[state=active]:border-[var(--primary)] data-[state=active]:bg-transparent data-[state=active]:shadow-none"
            >
              Keywords
            </TabsTrigger>
            <TabsTrigger
              value="flowchart"
              className="rounded-none border-b-2 border-transparent data-[state=active]:border-[var(--primary)] data-[state=active]:bg-transparent data-[state=active]:shadow-none"
            >
              Flowchart
            </TabsTrigger>
          </TabsList>
        </div>
        <div className="flex flex-1 flex-col overflow-hidden bg-[var(--background)]">
          <TabsContent value="summary" className="m-0 flex flex-1 flex-col overflow-hidden">
            <SummaryTabs paperId={paper.paper_id} />
          </TabsContent>
          <TabsContent value="qa" className="m-0 flex flex-1 flex-col overflow-hidden">
            <ChatPanel paperId={paper.paper_id} />
          </TabsContent>
          <TabsContent value="keywords" className="m-0 flex flex-1 flex-col overflow-hidden">
            <KeywordPanel paper={paper} />
          </TabsContent>
          <TabsContent value="flowchart" className="m-0 flex flex-1 flex-col overflow-hidden">
            <FlowchartPanel paperId={paper.paper_id} />
          </TabsContent>
        </div>
      </Tabs>
    </div>
  );
}
