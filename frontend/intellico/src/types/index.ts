export interface PaperMetadata {
  title?: string;
  authors?: string;
  abstract?: string;
  keywords?: string | string[];
  publication_date?: string;
}

export interface PaperRecord {
  paper_id: string;
  filename: string;
  word_count?: number;
  page_count?: number;
  sections?: string[];
  metadata?: PaperMetadata;
  uploadedAt: number;
}

export interface UploadResponse {
  paper_id: string;
  status: string;
  data: {
    filename: string;
    word_count: number;
    page_count: number;
    sections: string[];
    metadata: PaperMetadata;
  };
}

export interface SummaryResponse {
  paper_id: string;
  summary: string;
}

export interface QAResponse {
  paper_id: string;
  question: string;
  answer: string;
  num_chunks_used: number;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  numChunks?: number;
}
