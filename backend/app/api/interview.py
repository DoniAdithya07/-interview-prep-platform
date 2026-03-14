from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from backend.app.core.dependencies import get_current_user
from backend.app.core.rate_limit import enforce_daily_rate_limit
from backend.app.database.db import get_db
from backend.app.models.interview import (
    CodingExecutionRequest,
    CodingExecutionResponse,
    CommunityQuestionCreate,
    CommunityQuestionItem,
    CommunityQuestionResponse,
    CommunityQuestionVoteRequest,
    ComplexityAnalysisRequest,
    ComplexityAnalysisResponse,
    InterviewQuestion,
    InterviewQuestionResponse,
    FollowUpQuestionRequest,
    FollowUpQuestionResponse,
    StudyPlanRequest,
    StudyPlanResponse,
    VoiceTranscriptionResponse,
)
from backend.app.services.coding_service import analyze_complexity, execute_code
from backend.app.services.interview_service import (
    generate_question,
    generate_question_from_resume,
    generate_follow_up,
    generate_study_plan,
)
from backend.app.services.resume_service import extract_resume_text
from backend.app.services.voice_service import transcribe_audio


router = APIRouter(prefix="/api", tags=["interview"])


@router.post("/question")
def create_question(
    payload: InterviewQuestion,
    user: dict = Depends(get_current_user),
) -> InterviewQuestionResponse:
    enforce_daily_rate_limit(user["id"], "interview")
    db = get_db()
    result = generate_question(payload)
    interview_doc = {
        "userId": user["id"],
        "role": payload.role.strip(),
        "type": payload.topic.strip(),
        "company": payload.company.strip() if payload.company else None,
        "language": payload.language.strip() if payload.language else None,
        "mode": payload.mode,
        "questions": [result["question"]],
        "answers": [],
        "score": 0,
        "aiFeedback": "",
        "scoreBreakdown": None,
        "strengths": [],
        "improvements": [],
        "resumeInsights": [],
        "resumeUsed": False,
        "followUps": [],
        "duration": 0,
        "status": "in_progress",
        "createdAt": datetime.now(timezone.utc),
    }
    _, doc_ref = db.collection("interviews").add(interview_doc)

    result["interviewId"] = doc_ref.id
    return InterviewQuestionResponse(**result)


@router.post("/resume-question", response_model=InterviewQuestionResponse)
async def create_resume_question(
    role: str = Form(...),
    topic: str = Form(...),
    difficulty: str = Form(...),
    company: str | None = Form(default=None),
    language: str | None = Form(default=None),
    mode: str = Form(default="technical"),
    resume: UploadFile = File(...),
    user: dict = Depends(get_current_user),
) -> InterviewQuestionResponse:
    enforce_daily_rate_limit(user["id"], "interview")
    db = get_db()
    if difficulty.strip() not in {"easy", "medium", "hard"}:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Difficulty must be easy, medium, or hard.",
        )
    if mode.strip() not in {"technical", "coding", "behavioral", "hr", "system-design", "ai-mock"}:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Mode must be one of technical, coding, behavioral, hr, system-design, or ai-mock.",
        )

    resume_text = await extract_resume_text(resume)
    result = generate_question_from_resume(
        role=role.strip(),
        topic=topic.strip(),
        difficulty=difficulty.strip(),
        resume_text=resume_text,
        company=company.strip() if company else None,
        language=language.strip() if language else None,
        mode=mode.strip(),
    )
    interview_doc = {
        "userId": user["id"],
        "role": role.strip(),
        "type": topic.strip(),
        "company": company.strip() if company else None,
        "language": language.strip() if language else None,
        "mode": mode.strip(),
        "questions": [result["question"]],
        "answers": [],
        "score": 0,
        "aiFeedback": "",
        "scoreBreakdown": None,
        "strengths": [],
        "improvements": [],
        "duration": 0,
        "status": "in_progress",
        "resumeInsights": result["resumeInsights"],
        "resumeUsed": True,
        "followUps": [],
        "createdAt": datetime.now(timezone.utc),
    }
    _, doc_ref = db.collection("interviews").add(interview_doc)
    result["interviewId"] = doc_ref.id
    return InterviewQuestionResponse(**result)


@router.post("/follow-up", response_model=FollowUpQuestionResponse)
def create_follow_up_question(
    payload: FollowUpQuestionRequest,
    user: dict = Depends(get_current_user),
) -> FollowUpQuestionResponse:
    enforce_daily_rate_limit(user["id"], "follow-up")
    db = get_db()
    interview_ref = db.collection("interviews").document(payload.interviewId)
    snapshot = interview_ref.get()
    if not snapshot.exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview not found")

    interview = snapshot.to_dict() or {}
    if interview.get("userId") != user["id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Interview access denied")

    question = generate_follow_up(
        {
            "question": payload.question,
            "answer": payload.answer,
            "role": payload.role or interview.get("role"),
            "topic": payload.topic or interview.get("type"),
            "company": payload.company or interview.get("company"),
            "mode": payload.mode or interview.get("mode", "technical"),
            "language": payload.language or interview.get("language"),
        }
    )
    follow_ups = list(interview.get("followUps") or [])
    follow_ups.append(question)
    interview_ref.update({"followUps": follow_ups})
    return FollowUpQuestionResponse(question=question)


@router.post("/study-plan", response_model=StudyPlanResponse)
def create_study_plan(
    payload: StudyPlanRequest,
    user: dict = Depends(get_current_user),
) -> StudyPlanResponse:
    enforce_daily_rate_limit(user["id"], "study-plan")
    db = get_db()
    plan = generate_study_plan(payload)
    db.collection("study_plan_history").add(
        {
            "user_id": user["id"],
            "role": payload.role,
            "hours_per_week": payload.hours_per_week,
            "duration_weeks": payload.duration_weeks,
            "plan": plan,
            "created_at": datetime.now(timezone.utc),
        }
    )
    return StudyPlanResponse(plan=plan)


@router.post("/coding/execute", response_model=CodingExecutionResponse)
def execute_coding_solution(
    payload: CodingExecutionRequest,
    user: dict = Depends(get_current_user),
) -> CodingExecutionResponse:
    enforce_daily_rate_limit(user["id"], "coding-execution")
    return CodingExecutionResponse(
        **execute_code(
            language=payload.language,
            code=payload.code,
            function_name=payload.function_name,
            test_cases=payload.test_cases,
        )
    )


@router.post("/coding/analyze", response_model=ComplexityAnalysisResponse)
def analyze_coding_solution(
    payload: ComplexityAnalysisRequest,
    user: dict = Depends(get_current_user),
) -> ComplexityAnalysisResponse:
    enforce_daily_rate_limit(user["id"], "coding-analysis")
    return ComplexityAnalysisResponse(**analyze_complexity(payload.code))


@router.get("/community/questions", response_model=CommunityQuestionResponse)
def list_community_questions(
    search: str | None = None,
    user: dict = Depends(get_current_user),
) -> CommunityQuestionResponse:
    db = get_db()
    docs = db.collection("community_questions").stream()
    items = []
    for doc in docs:
        payload = doc.to_dict() or {}
        if search:
            haystack = " ".join(
                [
                    str(payload.get("title", "")),
                    str(payload.get("role", "")),
                    str(payload.get("topic", "")),
                    str(payload.get("question", "")),
                ]
            ).lower()
            if search.strip().lower() not in haystack:
                continue
        items.append(
            CommunityQuestionItem(
                id=doc.id,
                title=payload.get("title", ""),
                role=payload.get("role", ""),
                topic=payload.get("topic", ""),
                question=payload.get("question", ""),
                mode=payload.get("mode", "technical"),
                company=payload.get("company"),
                user_id=payload.get("user_id", ""),
                created_at=str(payload.get("created_at")) if payload.get("created_at") else None,
                votes=int(payload.get("votes", 0) or 0),
                reports=int(payload.get("reports", 0) or 0),
            )
        )
    return CommunityQuestionResponse(items=items)


@router.post("/community/questions", response_model=CommunityQuestionItem)
def create_community_question(
    payload: CommunityQuestionCreate,
    user: dict = Depends(get_current_user),
) -> CommunityQuestionItem:
    enforce_daily_rate_limit(user["id"], "community")
    db = get_db()
    record = {
        "title": payload.title,
        "role": payload.role,
        "topic": payload.topic,
        "question": payload.question,
        "mode": payload.mode,
        "company": payload.company,
        "user_id": user["id"],
        "votes": 0,
        "reports": 0,
        "created_at": datetime.now(timezone.utc),
    }
    _, doc_ref = db.collection("community_questions").add(record)
    return CommunityQuestionItem(
        id=doc_ref.id,
        title=payload.title,
        role=payload.role,
        topic=payload.topic,
        question=payload.question,
        mode=payload.mode,
        company=payload.company,
        user_id=user["id"],
        created_at=str(record["created_at"]),
        votes=0,
        reports=0,
    )


@router.post("/community/questions/vote", response_model=CommunityQuestionItem)
def vote_community_question(
    payload: CommunityQuestionVoteRequest,
    user: dict = Depends(get_current_user),
) -> CommunityQuestionItem:
    db = get_db()
    doc_ref = db.collection("community_questions").document(payload.question_id)
    snapshot = doc_ref.get()
    if not snapshot.exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Community question not found")
    record = snapshot.to_dict() or {}
    record["votes"] = int(record.get("votes", 0) or 0) + 1
    doc_ref.update({"votes": record["votes"]})
    return CommunityQuestionItem(
        id=snapshot.id,
        title=record.get("title", ""),
        role=record.get("role", ""),
        topic=record.get("topic", ""),
        question=record.get("question", ""),
        mode=record.get("mode", "technical"),
        company=record.get("company"),
        user_id=record.get("user_id", ""),
        created_at=str(record.get("created_at")) if record.get("created_at") else None,
        votes=record["votes"],
        reports=int(record.get("reports", 0) or 0),
    )


@router.post("/community/questions/report", response_model=CommunityQuestionItem)
def report_community_question(
    payload: CommunityQuestionVoteRequest,
    user: dict = Depends(get_current_user),
) -> CommunityQuestionItem:
    db = get_db()
    doc_ref = db.collection("community_questions").document(payload.question_id)
    snapshot = doc_ref.get()
    if not snapshot.exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Community question not found")
    record = snapshot.to_dict() or {}
    record["reports"] = int(record.get("reports", 0) or 0) + 1
    doc_ref.update({"reports": record["reports"]})
    return CommunityQuestionItem(
        id=snapshot.id,
        title=record.get("title", ""),
        role=record.get("role", ""),
        topic=record.get("topic", ""),
        question=record.get("question", ""),
        mode=record.get("mode", "technical"),
        company=record.get("company"),
        user_id=record.get("user_id", ""),
        created_at=str(record.get("created_at")) if record.get("created_at") else None,
        votes=int(record.get("votes", 0) or 0),
        reports=record["reports"],
    )


@router.post("/voice/transcribe", response_model=VoiceTranscriptionResponse)
async def transcribe_voice_answer(
    audio: UploadFile = File(...),
    user: dict = Depends(get_current_user),
) -> VoiceTranscriptionResponse:
    enforce_daily_rate_limit(user["id"], "voice")
    return VoiceTranscriptionResponse(transcript=await transcribe_audio(audio))
