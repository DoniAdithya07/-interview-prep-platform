## Smart Interview Prep Platform

This repo is organized into:

1. Backend (FastAPI + Firebase Admin): `/backend`
2. DevMentor app (Next.js + Firebase Web SDK): `/devmentor`
3. Docker files: `/docker`

## Project Structure

```text
interview-prep-platform/
|- backend/
|  |- app/
|  |  |- api/
|  |  |- core/
|  |  |- database/
|  |  |- models/
|  |  |- services/
|  |  `- main.py
|  |- .env.example
|  `- requirements.txt
|- devmentor/
|  |- app/
|  |- components/
|  |- context/
|  |- hooks/
|  |- lib/
|  |- styles/
|  `- types/
|- docker/
`- run.py
```

## Backend Setup
1. `python -m venv .venv`
2. `.venv\Scripts\Activate.ps1`
3. `pip install -r backend/requirements.txt`
4. Create `backend/.env` from `backend/.env.example`
5. Put the Firebase service account key at the project root as `firebase_key.json`
6. Run: `python run.py`

Backend URL: `http://127.0.0.1:8000`

## Frontend Setup
1. `cd devmentor`
2. `npm install`
3. Create `devmentor/.env.local` from `devmentor/.env.example`
4. Run: `npm run dev`

Frontend URL: `http://localhost:3000`
