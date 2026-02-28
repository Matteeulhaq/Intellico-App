import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { PaperRecord } from "@/types";

interface AppState {
  papers: PaperRecord[];
  selectedPaperId: string | null;
  showUpload: boolean;
  addPaper: (paper: PaperRecord) => void;
  setSelectedPaper: (id: string | null) => void;
  setShowUpload: (show: boolean) => void;
  getPaper: (id: string) => PaperRecord | undefined;
}

const STORAGE_KEY = "intellico-papers";

export const useStore = create<AppState>()(
  persist(
    (set, get) => ({
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
    }),
    { name: STORAGE_KEY, partialize: (s) => ({ papers: s.papers }) }
  )
);
