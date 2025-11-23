# 3Docs - Interactive 3D Repair Guide

## Overview

3Docs is an innovative application that transforms traditional PDF repair manuals into interactive 3D repair guides. The system uses AI to analyze manual images, extract instructional content, and generate 3D models to assist users in repair processes.

## Architecture

The application consists of two main components:

### Backend (Python)
- **Framework**: FastAPI REST API server with async processing pipeline
- **Server**: Always-running server.py with on-demand PDF processing
- **AI Integration**: Google Gemini AI for image analysis and instruction extraction
- **3D Generation**: Tripo3D API for generating 3D models
- **Text-to-Speech**: Fish Audio API for generating audio instructions
- **PDF Processing**: PyMuPDF for extracting images and text from manuals
- **Database**: SQLite for storing instruction metadata
- **Location**: `/backend`

### Frontend (Next.js)
- **Framework**: Next.js 16 with React 19
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Location**: `/frontend`

## Project Structure

```
MadHacks2025/
├── backend/
│   ├── server.py           # FastAPI REST API server (main entry point)
│   ├── main.py             # Processing pipeline (can run standalone)
│   ├── preprocessing.py    # PDF extraction logic
│   ├── gemini_service.py   # Gemini AI integration
│   ├── tripo.py           # Tripo3D API integration
│   ├── tts.py             # Text-to-speech functionality (Fish Audio)
│   ├── database.py        # SQLite database operations
│   ├── requirements.txt   # Python dependencies
│   ├── Dockerfile         # Backend container configuration
│   ├── .env.example       # Environment variables template
│   └── volume/            # PDF storage and processed files
│       ├── instructions.db   # SQLite database
│       ├── *.pdf            # Input PDFs
│       ├── *.mp3            # Generated audio files
│       ├── *.glb            # Generated 3D models
│       └── *.txt            # Extracted instructions
├── frontend/
│   ├── app/                # Next.js app directory
│   ├── public/             # Static assets
│   ├── package.json        # Node.js dependencies
│   └── next.config.ts      # Next.js configuration
└── docker-compose.yml      # Docker orchestration
```

## Key Features

1. **PDF Processing**: Extracts images and text from repair manuals
2. **AI Analysis**: Uses Gemini AI to identify instructional content
3. **3D Model Generation**: Creates 3D models from manual images
4. **Interactive Guides**: Presents repair instructions in an engaging format

## Technology Stack

### Backend Dependencies
- `fastapi`: Modern web framework for building APIs
- `uvicorn`: ASGI server for running FastAPI
- `google-generativeai`: Gemini AI integration
- `PyMuPDF`: PDF processing
- `tripo3d`: 3D model generation
- `aiohttp`: Async HTTP client for Fish Audio TTS API
- `python-dotenv`: Environment configuration
- `python-multipart`: File upload support
- `Pillow`: Image processing
- `pydantic`: Data validation

### Frontend Dependencies
- `next`: React framework
- `react` & `react-dom`: UI library
- `tailwindcss`: Utility-first CSS
- `typescript`: Type safety

## Getting Started

### Prerequisites
- Docker and Docker Compose (recommended)
- OR Python 3.9+ and Node.js 18+ for local development

### Environment Setup

1. Copy the environment template:
```bash
cp backend/.env.example backend/.env
```

2. Configure API keys in `backend/.env`:
   - `GEMINI_API_KEY`: Get from [Google AI Studio](https://makersuite.google.com/app/apikey)
   - `TRIPO_API_KEY`: Get from [Tripo3D Platform](https://platform.tripo3d.ai/)
   - `FISH_AUDIO_API_KEY`: Get from [Fish Audio](https://fish.audio/)

### Running with Docker (Recommended)

```bash
# Build and start all services
docker-compose up --build

# Frontend will be available at http://localhost:3000
# Backend will be available at http://localhost:8000
```

### Running Locally

#### Backend (Server Mode - Recommended)
```bash
cd backend
pip install -r requirements.txt
uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```

#### Backend (Standalone Mode - for testing)
```bash
cd backend
pip install -r requirements.txt
# Process a specific PDF with custom options
python main.py --pdf test.pdf --voice-id zh_CN-female-1
# Skip TTS or 3D generation
python main.py --pdf myfile.pdf --no-tts
python main.py --pdf myfile.pdf --no-3d
```

#### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Development Workflow

### Backend Development

#### Server-Based Workflow (Production)
1. Start the FastAPI server: `uvicorn server:app --reload`
2. The server provides REST API endpoints:
   - `GET /` - Health check
   - `GET /health` - Detailed health status
   - `POST /process` - Process existing PDF in volume directory
   - `POST /upload-and-process` - Upload and process PDF in one request
3. Send requests to trigger on-demand processing

#### Standalone Workflow (Testing)
1. Place PDF manuals in `backend/volume/`
2. Run `python main.py --pdf <filename>` to process
3. The pipeline orchestrates:
   - PDF extraction (`preprocessing.py`)
   - AI analysis (`gemini_service.py`)
   - TTS generation (`tts.py`)
   - 3D model generation (`tripo.py`)
   - Database storage (`database.py`)
4. Results are stored in database and volume directory

### Frontend Development
- Use `npm run dev` for hot-reload development
- Build for production: `npm run build`
- Start production server: `npm start`

## Backend API Endpoints

### Health Checks
- `GET /` - Basic health check, returns service status
- `GET /health` - Detailed health check with database and volume status

### PDF Processing
#### `POST /process`
Process a PDF file already in the volume directory.

**Request Body:**
```json
{
  "pdf_filename": "test.pdf",
  "voice_id": "zh_CN-female-1",
  "generate_tts": true,
  "generate_3d": true
}
```

**Response:**
```json
{
  "success": true,
  "message": "Successfully processed test.pdf",
  "pdf_hash": "a1b2c3d4e5f6g7h8",
  "steps_processed": 5,
  "tts_files_generated": 5,
  "models_generated": 5
}
```

#### `POST /upload-and-process`
Upload a PDF file and process it immediately.

**Form Data:**
- `file`: PDF file (required)
- `voice_id`: Voice ID for TTS (default: "zh_CN-female-1")
- `generate_tts`: Whether to generate TTS (default: true)
- `generate_3d`: Whether to generate 3D models (default: true)

**Response:** Same as `/process` endpoint

### Example Usage
```bash
# Process existing PDF
curl -X POST http://localhost:8000/process \
  -H "Content-Type: application/json" \
  -d '{"pdf_filename": "test.pdf"}'

# Upload and process new PDF
curl -X POST http://localhost:8000/upload-and-process \
  -F "file=@manual.pdf" \
  -F "voice_id=zh_CN-female-1" \
  -F "generate_tts=true" \
  -F "generate_3d=true"
```

## External API Integration

### Gemini AI Service
- Analyzes extracted images from manuals
- Identifies instructional vs. informational content
- Extracts titles and descriptions for repair steps

### Tripo3D Service
- Generates 3D models from instructional images
- Provides interactive 3D visualizations for repair guides

### Fish Audio TTS Service
- Generates natural-sounding audio instructions
- Supports multiple voice IDs and languages

## Docker Configuration

The project includes:
- `Dockerfile.backend`: Python backend containerization
- `Dockerfile.frontend`: Next.js frontend containerization
- `docker-compose.yml`: Multi-container orchestration
- `.dockerignore` files: Optimize build context
