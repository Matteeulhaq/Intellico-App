const getBaseUrl = () =>
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:2750";

export async function healthCheck(): Promise<{ status: string }> {
  const res = await fetch(`${getBaseUrl()}/health`);
  if (!res.ok) throw new Error("Health check failed");
  return res.json();
}

export async function uploadPdf(file: File): Promise<{
  paper_id: string;
  status: string;
  data: {
    filename: string;
    word_count: number;
    page_count: number;
    sections: string[];
    metadata: { title?: string; authors?: string; abstract?: string; keywords?: string | string[]; publication_date?: string };
  };
}> {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${getBaseUrl()}/api/upload`, {
    method: "POST",
    body: formData,
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || "Upload failed");
  return data;
}

export async function getSummary(paperId: string): Promise<{ paper_id: string; summary: string }> {
  const res = await fetch(`${getBaseUrl()}/api/summarize/${paperId}`);
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || "Summary failed");
  return data;
}

export async function askQuestion(
  paperId: string,
  question: string
): Promise<{ paper_id: string; question: string; answer: string; num_chunks_used: number }> {
  const res = await fetch(`${getBaseUrl()}/api/qa/${paperId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || "Q&A failed");
  return data;
}

export async function getFlowchart(paperId: string): Promise<Blob> {
  const res = await fetch(`${getBaseUrl()}/api/flowchart/${paperId}`);
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error((data as { error?: string }).error || "Flowchart generation failed");
  }
  return res.blob();
}

export async function getPaperStatus(paperId: string): Promise<{
  paper_id: string;
  status: "processing" | "ready";
  message: string;
  chunks_count?: number;
}> {
  const res = await fetch(`${getBaseUrl()}/api/status/${paperId}`);
  const data = await res.json();
  if (!res.ok && res.status !== 202) throw new Error(data.error || "Status check failed");
  return data;
}

export async function getPaper(paperId: string): Promise<{
  paper_id: string;
  filename?: string;
  extracted_metadata?: {
    title?: string;
    authors?: string | string[];
    abstract?: string;
    keywords?: string | string[];
    publication_date?: string;
  };
  metadata_extracted: boolean;
  metadata_extracted_at?: string;
  processing_error?: string;
}> {
  const res = await fetch(`${getBaseUrl()}/api/paper/${paperId}`);
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || "Failed to fetch paper");
  return data;
}
