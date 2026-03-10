import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { PaperRecord, ChatMessage } from "@/types";

interface AppState {
  papers: PaperRecord[];
  selectedPaperId: string | null;
  showUpload: boolean;
  addPaper: (paper: PaperRecord) => void;
  setSelectedPaper: (id: string | null) => void;
  setShowUpload: (show: boolean) => void;
  getPaper: (id: string) => PaperRecord | undefined;
  addChatMessage: (paperId: string, message: ChatMessage) => void;
  clearChatHistory: (paperId: string) => void;
  updatePaperMetadata: (paperId: string, metadata: any) => void;
}

const STORAGE_KEY = "intellico-papers";

// Stable function creators to prevent re-renders
const createUpdatePaperMetadata = (set: any) => (paperId: string, metadata: any) =>
  set((state: AppState) => ({
    papers: state.papers.map((p) =>
      p.paper_id === paperId
        ? { ...p, metadata: metadata.extracted_metadata }
        : p
    ),
  }));

const createAddChatMessage = (set: any) => (paperId: string, message: ChatMessage) =>
  set((state: AppState) => ({
    papers: state.papers.map((p) =>
      p.paper_id === paperId
        ? { ...p, chatHistory: [...(p.chatHistory || []), message] }
        : p
    ),
  }));

const createClearChatHistory = (set: any) => (paperId: string) =>
  set((state: AppState) => ({
    papers: state.papers.map((p) =>
      p.paper_id === paperId ? { ...p, chatHistory: [] } : p
    ),
  }));

export const useStore = create<AppState>()(
  persist(
    (set, get) => {
      // Create stable functions once
      const updatePaperMetadata = createUpdatePaperMetadata(set);
      const addChatMessage = createAddChatMessage(set);
      const clearChatHistory = createClearChatHistory(set);

      return {
        papers: [],
        selectedPaperId: null,
        showUpload: false,
        addPaper: (paper) =>
          set((state) => {
            const exists = state.papers.some((p) => p.paper_id === paper.paper_id);
            if (exists) return state;
            return { papers: [paper, ...state.papers] };
          }),
        setSelectedPaper: (id) => set({ selectedPaperId: id, showUpload: false }),
        setShowUpload: (show) => set({ showUpload: show }),
        getPaper: (id) => get().papers.find((p) => p.paper_id === id),
        addChatMessage,
        clearChatHistory,
        updatePaperMetadata,
      };
    },
    { name: STORAGE_KEY, partialize: (s) => ({ papers: s.papers }) }
  )
);
