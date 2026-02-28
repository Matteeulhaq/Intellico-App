# Assumptions

## Backend

1. **Keywords**: No `/api/keywords/<paper_id>` endpoint. Keywords come from upload response `data.metadata.keywords`. May be string (comma-separated) or array; frontend normalizes both.
2. **Relationships**: No dedicated endpoint. Concept relationships are only in the flowchart SVG. Keywords tab shows a note to use the Flowchart tab.
3. **Summary**: No `short`/`medium`/`detailed` parameter. UI truncation is used with clear labels.
4. **List papers**: No backend endpoint. Paper history is stored in `localStorage` only.
5. **Flowchart errors**: On 500, backend returns JSON `{ error: "..." }`. Memory/OOM errors often mention "memory", "cuda", "gpu"; frontend shows a friendly retry suggestion.
6. **Default port**: Backend assumed at `http://localhost:2750` unless `NEXT_PUBLIC_API_BASE_URL` is set.

## Frontend

1. **CORS**: Backend has CORS enabled for the frontend origin.
2. **PDF only**: Accepts `.pdf` files; other types rejected with toast.
3. **Paper selection**: When papers exist but none selected, first paper is auto-selected.
4. **Zustand persist**: Only `papers` array is persisted; `selectedPaperId` and `showUpload` are not (to avoid stale state across sessions).
