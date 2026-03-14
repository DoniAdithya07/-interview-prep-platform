from backend.app.models.interview import InterviewQuestion, StudyPlanRequest
from backend.app.services.ai_service import (
    generate_follow_up_question,
    generate_question_with_gemini,
    generate_resume_interview_with_gemini,
    rewrite_resume_text,
    generate_study_plan_with_gemini,
)
from backend.app.services.question_bank import random_question
from backend.app.services.resume_service import fallback_resume_insights


def generate_question(payload: InterviewQuestion) -> dict:
    generated_question = generate_question_with_gemini(
        payload.role,
        payload.topic,
        payload.difficulty,
        company=payload.company,
        language=payload.language,
        mode=payload.mode,
    )

    bank_question = random_question(payload.mode, payload.topic)
    fallback_question = (
        bank_question
        or (
            f"You are interviewing for a {payload.role} role"
            f"{f' at {payload.company}' if payload.company else ''}. "
            f"Ask a {payload.difficulty} {payload.mode} question about {payload.topic}"
            f"{f' using {payload.language}' if payload.language else ''}, "
            "then probe for reasoning, tradeoffs, and a real-world example."
        )
    )

    return {
        "role": payload.role,
        "topic": payload.topic,
        "difficulty": payload.difficulty,
        "company": payload.company,
        "language": payload.language,
        "mode": payload.mode,
        "question": generated_question or fallback_question,
    }


def generate_question_from_resume(
    role: str,
    topic: str,
    difficulty: str,
    resume_text: str,
    company: str | None = None,
    language: str | None = None,
    mode: str = "technical",
) -> dict:
    ai_result = generate_resume_interview_with_gemini(
        role,
        topic,
        difficulty,
        resume_text,
        company=company,
        language=language,
        mode=mode,
    )
    if ai_result is not None:
        return {
            "role": role,
            "topic": topic,
            "difficulty": difficulty,
            "company": company,
            "language": language,
            "mode": mode,
            "question": ai_result["question"],
            "resumeUsed": True,
            "resumeInsights": ai_result["resumeInsights"],
        }

    bank_question = random_question(mode, topic)
    fallback_question = (
        bank_question
        or f"Based on your resume background, describe a {difficulty} {mode} {topic} challenge you handled "
        f"for a {role} role{f' interviewing with {company}' if company else ''}, "
        "explain your decisions, and quantify the outcome."
    )
    return {
        "role": role,
        "topic": topic,
        "difficulty": difficulty,
        "company": company,
        "language": language,
        "mode": mode,
        "question": fallback_question,
        "resumeUsed": True,
        "resumeInsights": fallback_resume_insights(resume_text),
    }


def generate_follow_up(payload: dict) -> str:
    follow_up = generate_follow_up_question(**payload)
    if follow_up:
        return follow_up

    mode = payload.get("mode", "technical")
    if mode == "behavioral":
        return "What was the result, and what would you do differently next time?"
    if mode == "coding":
        return "What are the time and space complexity tradeoffs in your approach?"
    return "What are the key tradeoffs or limitations in that approach?"


def rewrite_resume_entry(role: str, original_text: str) -> str:
    rewritten = rewrite_resume_text(role, original_text)
    if rewritten:
        return rewritten

    cleaned = original_text.strip().rstrip(".")
    return (
        f"Delivered {cleaned.lower()} using relevant tools and clear ownership, "
        "with measurable impact on performance, quality, or user outcomes."
    )


def generate_study_plan(payload: StudyPlanRequest) -> list[dict]:
    ai_plan = generate_study_plan_with_gemini(
        payload.role,
        payload.hours_per_week,
        payload.duration_weeks,
    )
    if ai_plan is not None:
        return ai_plan

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
            "weeks": max(1, payload.duration_weeks - max(1, payload.duration_weeks // 2)),
            "focus": f"Timed revision with {mock_interviews} mock interview sessions",
            "hours": revision_hours,
        },
    ]
