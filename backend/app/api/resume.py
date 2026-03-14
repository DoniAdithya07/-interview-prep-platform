from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, Form, UploadFile

from backend.app.core.dependencies import get_current_user
from backend.app.core.rate_limit import enforce_daily_rate_limit
from backend.app.database.db import get_db
from backend.app.database.serializers import serialize_firestore_value
from backend.app.models.interview import CoachingResponse, ResumeRewriteRequest, ResumeRewriteResponse
from backend.app.models.result import InterviewHistoryItem, ResumeAnalysisResult
from backend.app.services.ai_service import build_coaching_summary
from backend.app.services.interview_service import rewrite_resume_entry
from backend.app.services.resume_analysis_service import analyze_resume_against_job_description
from backend.app.services.resume_service import extract_resume_text


router = APIRouter(prefix="/api/resume", tags=["resume"])


@router.post("/analyze", response_model=ResumeAnalysisResult)
async def analyze_resume(
    job_description: str = Form(...),
    resume: UploadFile = File(...),
    user: dict = Depends(get_current_user),
) -> ResumeAnalysisResult:
    enforce_daily_rate_limit(user["id"], "resume-analysis")
    db = get_db()
    resume_text = await extract_resume_text(resume)
    analysis = analyze_resume_against_job_description(resume_text, job_description)
    db.collection("resume_analysis_history").add(
        {
            "user_id": user["id"],
            "resumeText": resume_text[:4000],
            "jobDescription": job_description[:4000],
            "analysis": analysis.model_dump(),
            "created_at": datetime.now(timezone.utc),
        }
    )
    return analysis


@router.post("/rewrite", response_model=ResumeRewriteResponse)
def rewrite_resume(payload: ResumeRewriteRequest) -> ResumeRewriteResponse:
    # Rewrite remains unauthenticated at backend logic level but called from protected UI.
    return ResumeRewriteResponse(
        rewritten_text=rewrite_resume_entry(payload.role, payload.original_text)
    )


@router.get("/coach", response_model=CoachingResponse)
def coaching_summary(user: dict = Depends(get_current_user)) -> CoachingResponse:
    db = get_db()
    docs = (
        db.collection("interviews")
        .where("userId", "==", user["id"])
        .where("status", "==", "completed")
        .stream()
    )
    history = []
    for doc in docs:
        item = serialize_firestore_value(doc.to_dict() or {})
        history.append(
            InterviewHistoryItem(
                id=doc.id,
                **item,
            ).model_dump()
        )

    ai_summary = build_coaching_summary(history)
    if ai_summary is not None and ai_summary["summary"]:
        return CoachingResponse(
            summary=ai_summary["summary"],
            recommended_topics=ai_summary["recommendedTopics"],
            focus_areas=ai_summary["focusAreas"],
        )

    if not history:
        return CoachingResponse(
            summary="Start a few interviews to unlock personalized coaching.",
            recommended_topics=["Behavioral basics", "Core technical explanations", "Mock interview practice"],
            focus_areas=["Complete your first interview", "Review detailed AI feedback", "Practice consistently"],
        )

    low_topics: dict[str, list[int]] = {}
    for item in history:
        topic = str(item.get("type") or "General")
        low_topics.setdefault(topic, []).append(int(item.get("score") or 0))

    ranked_topics = sorted(
        (
            (topic, sum(scores) / len(scores))
            for topic, scores in low_topics.items()
        ),
        key=lambda pair: pair[1],
    )
    recommended = [topic for topic, _ in ranked_topics[:3]]
    return CoachingResponse(
        summary="Your interview history suggests consistent practice is helping, but weaker topics still need focused review.",
        recommended_topics=recommended or ["System design", "Behavioral storytelling", "Algorithms"],
        focus_areas=[
            "Use more concrete examples from projects.",
            "Call out tradeoffs explicitly in each answer.",
            "Practice concise summaries at the end of responses.",
        ],
    )
