from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status

from backend.app.core.dependencies import get_current_user
from backend.app.core.rate_limit import enforce_daily_rate_limit
from backend.app.database.db import get_db
from backend.app.models.interview import AnswerSubmission
from backend.app.models.result import EvaluationResult
from backend.app.services.evaluation_service import evaluate_answer
from backend.app.services.progress_service import sync_user_progress


router = APIRouter(prefix="/api", tags=["evaluation"])


@router.post("/evaluate", response_model=EvaluationResult)
def evaluate(
    payload: AnswerSubmission,
    user: dict = Depends(get_current_user),
) -> EvaluationResult:
    enforce_daily_rate_limit(user["id"], "evaluation")
    db = get_db()
    interview_ref = db.collection("interviews").document(payload.interviewId)
    snapshot = interview_ref.get()
    if not snapshot.exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview not found")

    interview = snapshot.to_dict() or {}
    if interview.get("userId") != user["id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Interview access denied")

    result = evaluate_answer(payload)
    interview_ref.update(
        {
            "answers": [payload.answer],
            "score": result["score"],
            "aiFeedback": result["feedback"],
            "scoreBreakdown": result["scoreBreakdown"],
            "starBreakdown": result.get("starBreakdown"),
            "strengths": result.get("strengths", []),
            "improvements": result.get("improvements", []),
            "accuracy": result.get("accuracy"),
            "duration": payload.duration_seconds or 0,
            "status": "completed",
            "completedAt": datetime.now(timezone.utc),
        }
    )
    sync_user_progress(user["id"])
    return EvaluationResult(**result)
