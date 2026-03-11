# Development Log

This file tracks code changes from the Python migration onward.

## 2026-03-04

### 1. Python migration started
- Goal recorded: make the project Python-only because the developer is comfortable with Python.
- Decision: use FastAPI for backend + simple HTML template for UI.

### 2. Dependency setup
- Added `requirements.txt` with:
  - `fastapi`
  - `uvicorn`
  - `jinja2`
  - `python-multipart`

### 3. App runtime entrypoint
- Added `run.py` to start the FastAPI app with reload on `127.0.0.1:8000`.

### 4. Core application package
- Added `app/__init__.py`.
- Added `app/main.py` with routes:
  - `GET /`
  - `GET /health`
  - `POST /api/question`
  - `POST /api/study-plan`
- Added `app/schemas.py` for request validation using Pydantic models.
- Added `app/services.py` for interview question and study-plan generation logic.

### 5. UI and static assets
- Added `templates/index.html` to display service status and available API routes.
- Added `static/styles.css` for base styling.

### 6. Repository and documentation updates
- Updated `README.md` with Python setup and run instructions.
- Updated `.gitignore` to include Python artifacts (`.venv`, `__pycache__`, `*.pyc`).

### 7. Logging policy
- `DEVELOPMENT_LOG.md` created and initialized.
- Rule: every meaningful code/configuration change should be appended here in chronological order until project completion.

### 8. Validation and runtime readiness
- Installed Python dependencies with `pip install -r requirements.txt`.
- Verified app import: `python -c "import app.main; print('python app import ok')"`.
- Result: Python app imports successfully and is ready to run with `python run.py`.

### 9. Phase 3 implementation (core platform features)
- Added `app/database.py` with SQLite database initialization for:
  - `users`
  - `auth_tokens`
  - `question_history`
  - `study_plan_history`
- Added `app/auth.py`:
  - salted SHA-256 password hashing
  - password verification
  - bearer token generation and lookup
  - `get_current_user` auth dependency for protected routes
- Updated `app/schemas.py` with auth models:
  - `UserRegister`
  - `UserLogin`
  - `AuthResponse`
- Updated `app/main.py`:
  - startup DB init
  - `POST /api/auth/register`
  - `POST /api/auth/login`
  - protected `POST /api/question` with DB history save
  - protected `POST /api/study-plan` with DB history save
  - `GET /api/history/questions`
  - `GET /api/history/study-plans`
- Updated `templates/index.html` to show new Phase 3 endpoints.
- Updated `README.md` with Phase 3 endpoint documentation.

### 10. Phase 3 verification
- Tested end-to-end with FastAPI `TestClient`:
  - registration/login
  - token-authenticated question generation
  - token-authenticated study plan generation
  - retrieval of question and study plan history
- Result: `phase3 checks ok`.

### 11. Repository hygiene update
- Added `interview_prep.db` to `.gitignore` so local SQLite runtime data is not committed.

### 12. Phase 3 (Firestore Data Architecture - Step 6)
- Updated `firestore.rules` to enforce ownership:
  - `/users/{userId}` only accessible by same authenticated UID
  - `/interviews/{interviewId}` requires `userId == request.auth.uid`
  - `/progress/{userId}` only accessible by same authenticated UID
- Updated `firestore.indexes.json` with indexes for:
  - recent interviews by `userId`
  - recent interviews by `userId + type`
- Added `docs/firestore_data_architecture.md` documenting:
  - `/users/{userId}`
  - `/interviews/{interviewId}`
  - `/progress/{userId}`
  - security model and query indexes
- Added `app/firestore_models.py` with Pydantic models to mirror Firestore document shapes.
- Updated `README.md` with Firestore Step 6 section and removed leftover Next.js links.

### 13. Legacy Next.js/Firebase JS cleanup
- Removed old frontend/build artifacts not used by Python FastAPI backend:
  - `.next/`
  - `node_modules/`
  - `functions/`
  - `lib/`
  - `public/`
  - `package.json`
  - `package-lock.json`
  - `next.config.ts`
  - `tsconfig.json`
  - `eslint.config.mjs`
  - `postcss.config.mjs`
- Removed additional Next.js leftover file:
  - `next-env.d.ts`
- Updated `.gitignore` to ignore local `venv/` folder in addition to `.venv/`.

### 14. Pre-Phase-4 full audit and fixes
- Added missing runtime dependencies in `requirements.txt`:
  - `firebase-admin`
  - `PyJWT`
- Hardened auth configuration in `app/auth.py`:
  - `JWT_SECRET_KEY` now read from environment variable (with fallback default string)
- Hardened Firestore initialization in `app/firestore.py`:
  - service-account path from `FIREBASE_CREDENTIALS_PATH`
  - guarded app initialization to avoid duplicate-init errors on reload
- Replaced `app/main.py` with clean UTF-8 content and removed corrupted comment characters.
- Updated Firestore queries in `app/main.py` to use `firestore.Query.DESCENDING`.
- Aligned history storage with architecture:
  - interview records now written to `interviews`
  - progress metrics now updated in `progress/{userId}`
- Removed obsolete non-Python files from `app/`:
  - `layout.tsx`, `page.tsx`, `globals.css`, `favicon.ico`
- Removed unused SQLite module file:
  - `app/database.py`
- Added `.env.example` with required keys:
  - `JWT_SECRET_KEY`
  - `FIREBASE_CREDENTIALS_PATH`
- Removed obsolete `.env.local.example`.
- Updated `.gitignore` to ignore `firebase_key.json` (secret file).
- Rewrote `README.md` so setup instructions match current Python + Firestore backend.
- Validation performed:
  - `python -m compileall app` passed
  - `firestore.indexes.json` JSON validation passed

### 15. Phase 4 Step 7 (Auth Pages + AuthContext)
- Added Next.js Firebase client config:
  - `app/firebase/client.ts`
- Added shared auth context with `useContext` and `onAuthStateChanged`:
  - `app/context/AuthContext.tsx`
- Added auth provider wrapper:
  - `app/providers.tsx`
- Added root layout to apply provider app-wide:
  - `app/layout.tsx`
- Added auth pages:
  - `app/auth/login/page.tsx` (Google + Email login)
  - `app/auth/register/page.tsx` (Google + Email signup)

### 16. Full-file consistency pass and fixes
- Identified architecture split issue:
  - frontend auth pages/context were placed in backend `app/` by mistake.
- Fixed by moving/auth-implementing in `frontend/`:
  - `frontend/context/AuthContext.tsx`
  - `frontend/app/providers.tsx`
  - `frontend/app/auth/login/page.tsx`
  - `frontend/app/auth/register/page.tsx`
  - updated `frontend/app/layout.tsx` to wrap `Providers`
  - updated `frontend/app/page.tsx` with auth session-aware home screen
- Updated `frontend/lib/firebase.ts` to use `getApps()/getApp()` guard.
- Fixed formatting in `frontend/.env.local` (removed quotes/spaces that break parsing).
- Added `frontend/.env.example` template.
- Removed misplaced frontend files from backend:
  - `app/layout.tsx`
  - `app/providers.tsx`
  - `app/context/`
  - `app/firebase/`
  - `app/auth/`
- Rewrote root `README.md` to document backend + frontend setup clearly.
- Validation:
  - `python -m compileall app` passed
  - `python -c "import app.main"` passed
  - `cd frontend && npm run lint` passed
