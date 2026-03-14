from fastapi import APIRouter, Depends, HTTPException, status
from firebase_admin import firestore

from backend.app.core.dependencies import get_current_user
from backend.app.database.db import get_db
from backend.app.database.serializers import serialize_firestore_value
from backend.app.models.result import (
    HistoryResponse,
    InterviewHistoryItem,
    LeaderboardEntry,
    LeaderboardResponse,
    ProgressResponse,
)


router = APIRouter(prefix="/api/history", tags=["history"])


def _serialize_doc(doc) -> InterviewHistoryItem:
    item = serialize_firestore_value(doc.to_dict() or {})
    item["id"] = doc.id
    return InterviewHistoryItem(**item)


@router.get("/questions", response_model=HistoryResponse)
def question_history(user: dict = Depends(get_current_user)) -> HistoryResponse:
    db = get_db()
    docs = (
        db.collection("interviews")
        .where("userId", "==", user["id"])
        .order_by("createdAt", direction=firestore.Query.DESCENDING)
        .stream()
    )
    return HistoryResponse(items=[_serialize_doc(doc) for doc in docs])


@router.get("/questions/{interview_id}", response_model=InterviewHistoryItem)
def question_history_item(interview_id: str, user: dict = Depends(get_current_user)) -> InterviewHistoryItem:
    db = get_db()
    doc = db.collection("interviews").document(interview_id).get()
    if not doc.exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview not found")

    payload = doc.to_dict() or {}
    if payload.get("userId") != user["id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Interview access denied")

    return _serialize_doc(doc)


@router.get("/study-plans")
def study_plan_history(user: dict = Depends(get_current_user)) -> dict:
    db = get_db()
    docs = (
        db.collection("study_plan_history")
        .where("user_id", "==", user["id"])
        .order_by("created_at", direction=firestore.Query.DESCENDING)
        .stream()
    )
    items = []
    for doc in docs:
        item = serialize_firestore_value(doc.to_dict() or {})
        item["id"] = doc.id
        items.append(item)
    return {"items": items}


@router.get("/progress", response_model=ProgressResponse)
def progress_summary(user: dict = Depends(get_current_user)) -> ProgressResponse:
    db = get_db()
    doc = db.collection("progress").document(user["id"]).get()
    if not doc.exists:
        return ProgressResponse()
    payload = serialize_firestore_value(doc.to_dict() or {})
    return ProgressResponse(**payload)


def _mask_user_id(user_id: str) -> str:
    if len(user_id) <= 8:
        return user_id
    return f"{user_id[:4]}...{user_id[-4:]}"


@router.get("/leaderboard", response_model=LeaderboardResponse)
def leaderboard(user: dict = Depends(get_current_user)) -> LeaderboardResponse:
    db = get_db()
    docs = db.collection("progress").stream()
    entries: list[LeaderboardEntry] = []

    for doc in docs:
        payload = serialize_firestore_value(doc.to_dict() or {})
        total_interviews = int(payload.get("totalInterviews", 0) or 0)
        avg_score = float(payload.get("avgScore", 0) or 0)
        streak_days = int(payload.get("streakDays", 0) or 0)
        points = int(total_interviews * 100 + round(avg_score * 5) + streak_days * 25)
        user_doc = db.collection("users").document(doc.id).get()
        user_payload = serialize_firestore_value(user_doc.to_dict() or {}) if user_doc.exists else {}
        saved_name = str(user_payload.get("name") or "").strip()
        display_name = saved_name or f"Candidate {_mask_user_id(doc.id)}"
        if doc.id == user["id"]:
            display_name = "You"
        entries.append(
            LeaderboardEntry(
                rank=0,
                userId=doc.id,
                displayName=display_name,
                points=points,
                avgScore=avg_score,
                totalInterviews=total_interviews,
                streakDays=streak_days,
            )
        )

    entries.sort(key=lambda item: (-item.points, -item.avgScore, -item.totalInterviews, item.displayName))
    ranked = [
        item.model_copy(update={"rank": index + 1})
        for index, item in enumerate(entries[:10])
    ]
    return LeaderboardResponse(items=ranked)
