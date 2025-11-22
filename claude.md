# 3Docs - Interactive 3D Repair Guide

## Overview

3Docs is an innovative application that transforms traditional PDF repair manuals into interactive 3D repair guides. The system uses AI to analyze manual images, extract instructional content, and generate 3D models to assist users in repair processes.

## Architecture

The application consists of two main components:

### Backend (Python)
- **Framework**: Python-based processing pipeline
- **AI Integration**: Google Gemini AI for image analysis and instruction extraction
- **3D Generation**: Tripo3D API for generating 3D models
- **PDF Processing**: PyMuPDF for extracting images and text from manuals
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
│   ├── main.py              # Main processing pipeline
│   ├── preprocessing.py     # PDF extraction logic
│   ├── gemini_service.py    # Gemini AI integration
│   ├── tripo.py            # Tripo3D API integration
│   ├── tts.py              # Text-to-speech functionality
│   ├── database.py         # Database operations
│   ├── requirements.txt    # Python dependencies
│   ├── .env.example        # Environment variables template
│   └── volume/             # PDF storage and processed files
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
- `google-generativeai`: Gemini AI integration
- `PyMuPDF`: PDF processing
- `tripo3d`: 3D model generation
- `python-dotenv`: Environment configuration
- `Pillow`: Image processing
- `requests`: HTTP client

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

### Running with Docker (Recommended)

```bash
# Build and start all services
docker-compose up --build

# Frontend will be available at http://localhost:3000
# Backend will be available at http://localhost:8000
```

### Running Locally

#### Backend
```bash
cd backend
pip install -r requirements.txt
python main.py
```

#### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Development Workflow

### Backend Development
1. Place PDF manuals in `backend/volume/`
2. The main pipeline (`main.py`) orchestrates:
   - PDF extraction (`preprocessing.py`)
   - AI analysis (`gemini_service.py`)
   - 3D generation (`tripo.py`)
3. Results are processed and stored for frontend consumption

### Frontend Development
- Use `npm run dev` for hot-reload development
- Build for production: `npm run build`
- Start production server: `npm start`

## API Integration

### Gemini AI Service
- Analyzes extracted images from manuals
- Identifies instructional vs. informational content
- Extracts titles and descriptions for repair steps

### Tripo3D Service
- Generates 3D models from instructional images
- Provides interactive 3D visualizations for repair guides

## Docker Configuration

The project includes:
- `Dockerfile.backend`: Python backend containerization
- `Dockerfile.frontend`: Next.js frontend containerization
- `docker-compose.yml`: Multi-container orchestration
- `.dockerignore` files: Optimize build context

## Future Enhancements

- [ ] REST API endpoints for PDF upload
- [ ] Real-time processing status updates
- [ ] Database persistence for processed manuals
- [ ] User authentication and manual library
- [ ] Advanced 3D model interactions
- [ ] Multi-language support

## Contributing

This project was created for MadHacks 2025. Contributions are welcome!

## License

See project repository for license information.
