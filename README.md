## Smart Interview Prep Platform

This repo now has two parts:

1. Backend (Python + FastAPI + Firestore Admin): `/app`
2. Frontend (Next.js + Firebase Web SDK): `/frontend`

## Backend Setup
1. `python -m venv .venv`
2. `.venv\Scripts\Activate.ps1`
3. `pip install -r requirements.txt`
4. Configure env:
   - `JWT_SECRET_KEY=your-secret`
   - `FIREBASE_CREDENTIALS_PATH=firebase_key.json`
5. Put service account key JSON at project root as `firebase_key.json`
6. Run: `python run.py`

Backend URL: `http://127.0.0.1:8000`

## Frontend Setup
1. `cd frontend`
2. `npm install`
3. Create `frontend/.env.local` from `frontend/.env.example`
4. Run: `npm run dev`

Frontend URL: `http://localhost:3000`

## Auth Pages (Phase 4 Step 7)
- `frontend/app/auth/login/page.tsx`
- `frontend/app/auth/register/page.tsx`
- Shared auth state:
  - `frontend/context/AuthContext.tsx`
  - `frontend/app/providers.tsx`
  - `frontend/app/layout.tsx`

`onAuthStateChanged` is used in `AuthContext` to persist client auth sessions.
