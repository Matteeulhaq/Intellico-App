# Intellico Development Guide

## Prerequisites

- Python 3.11+
- Node.js 18+
- MongoDB (local or Docker)

## Local Development

### Initial Setup

1. **Install Dependencies**
   ```bash
   npm run install:all
   ```

2. **Configure Environment**
   - Root `.env` already configured with backend settings
   - Frontend `.env.local` will be auto-created (defaults to http://localhost:2750)

3. **Start MongoDB**
   ```bash
   # Option A: Docker
   docker run -d -p 27018:27017 --name mongo mongo:6.0

   # Option B: Local MongoDB
   sudo systemctl start mongod
   ```

### Running the Application

#### Development Mode (Recommended)
```bash
npm run dev
```
This starts:
- Backend on http://localhost:2750
- Frontend on http://localhost:3000

#### Individual Services
```bash
# Backend only
npm run dev:backend

# Frontend only
npm run dev:frontend
```

#### Docker Mode
```bash
# Build and start all containers
npm run docker:up

# View logs
npm run docker:logs

# Stop containers
npm run docker:down
```

Access the application at http://localhost:2600

## Application Architecture

### Backend (Flask)
- Port: 2750 (development), 5000 (Docker internal)
- Framework: Flask with CORS
- ML Models: Qwen2.5-1.5B with fine-tuned adapter
- Database: MongoDB

### Frontend (Next.js)
- Port: 3000 (development), 2600 (Docker)
- Framework: Next.js 16.1.6 with React 19.2.3
- State: Zustand with localStorage persistence
- Styling: Tailwind CSS + shadcn/ui

## API Communication

The frontend communicates directly with the backend via REST API:

- Health Check: `GET /health`
- Upload PDF: `POST /api/upload`
- Generate Summary: `GET /api/summarize/<paper_id>`
- Q&A: `POST /api/qa/<paper_id>`
- Flowchart: `GET /api/flowchart/<paper_id>`

## Troubleshooting

### Frontend can't reach backend
1. Check backend is running: `curl http://localhost:2750/health`
2. Verify `NEXT_PUBLIC_API_BASE_URL` in `frontend/intellico/.env.local`
3. Check CORS is enabled (already configured in backend)

### Docker issues
1. Rebuild containers: `docker-compose down && docker-compose up -d --build`
2. Check logs: `docker-compose logs frontend` or `docker-compose logs backend`
3. Verify network: `docker network inspect intellico_net`

### Model loading errors
1. Check `ADAPTER_PATH` in `.env`
2. Verify `HUGGINGFACE_TOKEN` is set
3. Ensure `USE_HUGGINGFACE_REPO=true`
