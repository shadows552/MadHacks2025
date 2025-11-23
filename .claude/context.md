# 3Docs - Claude Code Context

## Project Quick Reference

### Technology Stack
- **Backend**: Python 3.9+, FastAPI, SQLite
- **Frontend**: Next.js 16, React 19, TypeScript, Tailwind CSS
- **AI Services**: Google Gemini AI, Tripo3D, Fish Audio TTS

### Key Directories
- `/backend` - Python FastAPI application
  - `server.py` - Main REST API server (entry point)
  - `main.py` - Processing pipeline (standalone mode)
  - `volume/` - PDF storage, database, and generated files
- `/frontend` - Next.js application
  - `app/` - Next.js app directory structure

### Environment Variables
All API keys are stored in `backend/.env`:
- `GEMINI_API_KEY` - Google Gemini AI
- `TRIPO_API_KEY` - Tripo3D platform
- `FISH_AUDIO_API_KEY` - Fish Audio TTS

### Common Development Tasks

#### Starting Services
```bash
# Full stack with Docker
docker-compose up --build

# Backend only (local)
cd backend && uvicorn server:app --reload

# Frontend only (local)
cd frontend && npm run dev
```

#### Processing PDFs
```bash
# Via API (server running)
curl -X POST http://localhost:8000/process \
  -H "Content-Type: application/json" \
  -d '{"pdf_filename": "test.pdf"}'

# Standalone mode
cd backend && python main.py --pdf test.pdf
```

### Architecture Flow
1. User uploads PDF manual → Backend receives file
2. PyMuPDF extracts images and text
3. Gemini AI analyzes images → Identifies instructional steps
4. Tripo3D generates 3D models from instructional images
5. Fish Audio creates TTS audio for instructions
6. SQLite stores metadata
7. Frontend displays interactive 3D guide

### Important Notes
- The backend server (`server.py`) is the production entry point
- `main.py` can be used for standalone testing
- All generated files are stored in `backend/volume/`
- Database is SQLite at `backend/volume/instructions.db`

### Code Style Guidelines
- **Backend**: Follow PEP 8, use type hints, async/await for I/O
- **Frontend**: TypeScript strict mode, functional components, Tailwind for styling
- **Documentation**: Keep README.md and claude.md in sync

### Testing
- Backend: Use pytest (when implemented)
- Frontend: Use Jest/React Testing Library (when implemented)

### API Endpoints
- `GET /` - Health check
- `GET /health` - Detailed status
- `POST /process` - Process existing PDF
- `POST /upload-and-process` - Upload and process PDF
