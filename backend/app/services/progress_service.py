from datetime import datetime, timedelta, timezone

from backend.app.database.db import get_db


def sync_user_progress(user_id: str) -> dict:
    db = get_db()
    docs = (
        db.collection("interviews")
        .where("userId", "==", user_id)
        .where("status", "==", "completed")
        .stream()
    )

    items = [doc.to_dict() or {} for doc in docs]
    total_interviews = len(items)
    avg_score = (
        sum(int(item.get("score") or 0) for item in items) / total_interviews
        if total_interviews
        else 0
    )

    topic_breakdown: dict[str, int] = {}
    completed_days: set[str] = set()
    for item in items:
        topic_key = str(item.get("type") or "general").strip().lower()
        topic_breakdown[topic_key] = topic_breakdown.get(topic_key, 0) + 1
        completed_at = item.get("completedAt") or item.get("createdAt")
        if isinstance(completed_at, datetime):
            completed_days.add(completed_at.astimezone(timezone.utc).date().isoformat())
        elif isinstance(completed_at, str) and completed_at:
            completed_days.add(str(completed_at)[:10])

    today = datetime.now(timezone.utc).date()
    streak_days = 0
    check_date = today
    while check_date.isoformat() in completed_days:
        streak_days += 1
        check_date = check_date - timedelta(days=1)

    achievements: list[str] = []
    if total_interviews >= 1:
        achievements.append("First Interview")
    if total_interviews >= 10:
        achievements.append("10 Interviews Completed")
    if any(int(item.get("score") or 0) >= 90 for item in items):
        achievements.append("Score Above 90")
    if streak_days >= 5:
        achievements.append("5-Day Practice Streak")

    payload = {
        "totalInterviews": total_interviews,
        "avgScore": round(avg_score, 2),
        "topicBreakdown": topic_breakdown,
        "streakDays": streak_days,
        "achievements": achievements,
    }
    db.collection("progress").document(user_id).set(payload, merge=True)
    return payload
