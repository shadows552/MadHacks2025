# 3Docs - Interactive 3D Repair Guide

Transform traditional PDF repair manuals into interactive 3D repair guides using AI.

## Quick Start with Docker

1. **Clone the repository**
```bash
git clone <repository-url>
cd MadHacks2025
```

2. **Set up environment variables**
```bash
cp backend/.env.example backend/.env
```

Edit `backend/.env` and add your API keys:
- `GEMINI_API_KEY`: Get from [Google AI Studio](https://makersuite.google.com/app/apikey)
- `TRIPO_API_KEY`: Get from [Tripo3D Platform](https://platform.tripo3d.ai/)

3. **Build and run with Docker Compose**
```bash
docker-compose up --build
```

4. **Access the application**
- Frontend: http://localhost:3000
- Backend: http://localhost:8000

## Local Development

### Backend
```bash
cd backend
pip install -r requirements.txt
python main.py
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Architecture

- **Backend**: Python-based PDF processing with Gemini AI and Tripo3D integration
- **Frontend**: Next.js 16 with React 19 and TypeScript

## Features

- PDF manual processing and image extraction
- AI-powered instruction identification using Gemini
- 3D model generation from manual images
- Interactive repair guide presentation

## Documentation

See [claude.md](./claude.md) for comprehensive documentation.

## Project Structure

```
MadHacks2025/
├── backend/          # Python processing service
├── frontend/         # Next.js web application
├── docker-compose.yml
└── claude.md         # Detailed documentation
```

## License

See repository for license information.
