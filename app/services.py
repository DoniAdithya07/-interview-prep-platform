from typing import List

from app.schemas import InterviewQuestion, StudyPlanRequest


def generate_question(payload: InterviewQuestion) -> dict:
    return {
        "role": payload.role,
        "topic": payload.topic,
        "difficulty": payload.difficulty,
        "question": (
            f"Explain a {payload.difficulty} {payload.topic} concept "
            f"relevant to a {payload.role} interview, and provide one real-world example."
        ),
    }


def generate_study_plan(payload: StudyPlanRequest) -> List[dict]:
    total_hours = payload.hours_per_week * payload.duration_weeks
    mock_interviews = max(1, payload.duration_weeks // 2)
    practice_hours = max(1, int(total_hours * 0.6))
    revision_hours = total_hours - practice_hours

    return [
        {
            "phase": "Core Concepts",
            "weeks": max(1, payload.duration_weeks // 2),
            "focus": f"{payload.role} fundamentals and key patterns",
            "hours": practice_hours,
        },
        {
            "phase": "Revision + Mock Interviews",
            "weeks": payload.duration_weeks - max(1, payload.duration_weeks // 2),
            "focus": f"Timed revision with {mock_interviews} mock interview sessions",
            "hours": revision_hours,
        },
    ]
