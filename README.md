# 3Docs - Interactive 3D Repair Guide

Transform 2d manuals into interactive 3D repair guides.

Transparency Notice:
This repository was created for the MadHacks 2025 Hackathon and is not a polished project. Much of the less complex programming was done with AI assistance.

## Demo
To view the 3Docs demo without inputting API keys and waiting, navigate to the root of the repository and run 'docker-compose up --build'

Navigate to http://localhost:3000/ using a web browser. Using the file upload box, input demo.pdf from the volume directory. This will use the cached API outputs instead of regenerating everything from scratch.

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
- `FISH_API_KEY`: Get from Fish Audio
TripoAI API NOTE: This can get quite expensive quite fast. Make sure that you are monitoring usage. Also, WebUI generations are different from API generations, you do not need to purchase a subscription to purchase API credits for TripoAI.

3. **Build and run with Docker Compose**
```bash
docker-compose up --build
```

4. **Access the application**
- Frontend: http://localhost:3000
- Backend: http://localhost:8000

## Local (No Docker)

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
