# 3Docs - Interactive 3D Repair Guide

Transform traditional PDF repair manuals into interactive 3D repair guides.

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
- `GEMINI_API_KEY`: Get from Google AI Studio
- `TRIPO_API_KEY`: Get from Tripo3D Platform

3. **Build and run with Docker Compose**
```bash
docker-compose up --build
```

4. **Access the application**
- Frontend: http://localhost:3000
- Backend: http://localhost:8000

## Local

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
