"use client";

import { useEffect, useState } from "react";
import { Copy, Loader2 } from "lucide-react";
import { getSummary } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/Tabs";
import { toast } from "sonner";

function truncateBySentences(text: string, count: number): string {
  const sentences = text.match(/[^.!?]+[.!?]+/g) || [text];
  return sentences.slice(0, count).join(" ").trim() || text;
}

export function SummaryTabs({ paperId }: { paperId: string }) {
  const [summary, setSummary] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    getSummary(paperId)
      .then((res) => {
        if (!cancelled) setSummary(res.summary);
      })
      .catch((e) => {
        if (!cancelled) setError(e instanceof Error ? e.message : "Failed to load summary");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => { cancelled = true; };
  }, [paperId]);

  const handleCopy = () => {
    if (!summary) return;
    navigator.clipboard.writeText(summary);
    toast.success("Summary copied to clipboard.");
  };

  if (loading) {
    return (
      <div className="flex flex-1 items-center justify-center p-8">
        <Loader2 className="h-8 w-8 animate-spin text-[var(--primary)]" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center gap-4 p-8">
        <p className="text-sm text-red-600">{error}</p>
        <Button variant="outline" onClick={() => window.location.reload()}>
          Retry
        </Button>
      </div>
    );
  }

  if (!summary) {
    return (
      <div className="flex flex-1 items-center justify-center p-8 text-sm text-[var(--muted-foreground)]">
        No summary available.
      </div>
    );
  }

  const short = truncateBySentences(summary, 2);
  const medium = truncateBySentences(summary, 4);
  const isShortTruncated = short.length < summary.length;
  const isMediumTruncated = medium.length < summary.length;

  return (
    <div className="flex flex-1 flex-col gap-4 bg-[var(--background)] p-6">
      <div className="flex items-center justify-between gap-4">
        <Tabs defaultValue="detailed" className="flex-1">
          <TabsList className="w-fit">
            <TabsTrigger value="short">
              Short {isShortTruncated && "(UI truncated)"}
            </TabsTrigger>
            <TabsTrigger value="medium">
              Medium {isMediumTruncated && "(UI truncated)"}
            </TabsTrigger>
            <TabsTrigger value="detailed">Detailed</TabsTrigger>
          </TabsList>
          <div className="mt-4">
            <TabsContent value="short">
              <Card className="prose prose-sm max-w-none">
                <p className="whitespace-pre-wrap text-neutral-700">{short}</p>
              </Card>
            </TabsContent>
            <TabsContent value="medium">
              <Card className="prose prose-sm max-w-none">
                <p className="whitespace-pre-wrap text-neutral-700">{medium}</p>
              </Card>
            </TabsContent>
            <TabsContent value="detailed">
              <Card className="prose prose-sm max-w-none">
                <p className="whitespace-pre-wrap text-neutral-700">{summary}</p>
              </Card>
            </TabsContent>
          </div>
        </Tabs>
        <Button variant="ghost" size="sm" className="shrink-0 gap-2" onClick={handleCopy}>
          <Copy className="h-4 w-4" />
          Copy
        </Button>
      </div>
    </div>
  );
}
