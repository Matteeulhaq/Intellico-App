# Intellico Frontend

Dental research assistant UI — upload PDFs, summarize, Q&A, keywords, and flowcharts.

## How to Run

### Prerequisites

- Node.js 18+
- Backend running at `http://localhost:2750` (or set `NEXT_PUBLIC_API_BASE_URL`)

### Setup

```bash
cd frontend/intellico
npm install
```

### Environment

Create `.env.local` (optional):

```
NEXT_PUBLIC_API_BASE_URL=http://localhost:2750
```

### Development

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

### Production Build

```bash
npm run build
npm start
```

## File Structure

```
frontend/intellico/
├── src/
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx
│   │   └── globals.css
│   ├── components/
│   │   ├── ui/
│   │   │   ├── Button.tsx
│   │   │   ├── Card.tsx
│   │   │   ├── Input.tsx
│   │   │   └── Tabs.tsx
│   │   ├── Sidebar.tsx
│   │   ├── UploadDropzone.tsx
│   │   ├── PaperHeader.tsx
│   │   ├── SummaryTabs.tsx
│   │   ├── ChatPanel.tsx
│   │   ├── KeywordPanel.tsx
│   │   ├── FlowchartPanel.tsx
│   │   └── Workspace.tsx
│   ├── lib/
│   │   ├── api.ts
│   │   └── store.ts
│   └── types/
│       └── index.ts
├── .env.example
└── package.json
```
