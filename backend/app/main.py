from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.api.auth import router as auth_router
from backend.app.api.evaluate import router as evaluate_router
from backend.app.api.history import router as history_router
from backend.app.api.interview import router as interview_router
from backend.app.api.resume import router as resume_router
from backend.app.core.config import settings
from backend.app.core.monitoring import setup_monitoring
from backend.app.database.firebase import get_firestore_client


setup_monitoring()
app = FastAPI(title="Interview Prep Platform", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(interview_router)
app.include_router(evaluate_router)
app.include_router(history_router)
app.include_router(resume_router)


@app.get("/health")
def health() -> dict:
    try:
        get_firestore_client()
        return {"status": "ok", "environment": settings.environment}
    except RuntimeError as exc:
        return JSONResponse(
            status_code=503,
            content={
                "status": "degraded",
                "environment": settings.environment,
                "detail": str(exc),
            },
        )
