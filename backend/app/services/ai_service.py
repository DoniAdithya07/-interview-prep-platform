import json
import logging

from backend.app.core.config import settings
from backend.app.services.cache_service import build_cache_key, get_cached_value, set_cached_value
from backend.app.services.company_service import get_company_profile
from backend.app.services.local_ai_service import generate_json_with_ollama

try:
    import google.generativeai as genai
except ImportError:
    genai = None


logger = logging.getLogger(__name__)


def _generate_json(prompt: str) -> dict | list | None:
    cache_key = build_cache_key("ai-json", settings.ai_provider, settings.ollama_model, prompt)
    cached_payload = get_cached_value(cache_key)
    if cached_payload is not None:
        return cached_payload

    ollama_payload = generate_json_with_ollama(prompt)
    if ollama_payload is not None:
        set_cached_value(cache_key, ollama_payload, ttl_seconds=3600)
        return ollama_payload

    if not settings.gemini_api_key or genai is None:
        return None

    try:
        genai.configure(api_key=settings.gemini_api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                response_mime_type="application/json",
            ),
        )
        if not response.text:
            return None
        payload = json.loads(response.text)
        set_cached_value(cache_key, payload, ttl_seconds=3600)
        return payload
    except Exception:
        logger.exception("Gemini request failed")
        return None


def evaluate_with_gemini(question: str, answer: str) -> dict | None:
    payload = _generate_json(
        f"""
        You are an expert technical interviewer. Evaluate the following answer to the interview question.
        Score the answer in four dimensions:
        - communication
        - clarity
        - technicalAccuracy
        - overall score
        Also provide:
        - feedback: one concise paragraph
        - strengths: array of 2-3 short strings
        - improvements: array of 2-3 short strings
        Output your response strictly in JSON with keys:
        "score", "feedback", "scoreBreakdown", "strengths", "improvements".
        "scoreBreakdown" must contain "communication", "clarity", and "technicalAccuracy".

        Question: {question}
        Answer: {answer}
        """
    )
    if not isinstance(payload, dict):
        return None

    breakdown_payload = payload.get("scoreBreakdown", {})
    if not isinstance(breakdown_payload, dict):
        breakdown_payload = {}

    communication = int(breakdown_payload.get("communication", 0))
    clarity = int(breakdown_payload.get("clarity", 0))
    technical_accuracy = int(breakdown_payload.get("technicalAccuracy", 0))
    if not any([communication, clarity, technical_accuracy]):
        average = int(payload.get("score", 0))
        communication = average
        clarity = average
        technical_accuracy = average

    return {
        "score": int(payload.get("score", 0)),
        "feedback": str(payload.get("feedback", "No feedback provided.")),
        "scoreBreakdown": {
            "communication": max(0, min(100, communication)),
            "clarity": max(0, min(100, clarity)),
            "technicalAccuracy": max(0, min(100, technical_accuracy)),
        },
        "strengths": [str(item) for item in payload.get("strengths", [])[:3]],
        "improvements": [str(item) for item in payload.get("improvements", [])[:3]],
    }


def generate_follow_up_question(
    *,
    question: str,
    answer: str,
    role: str | None = None,
    topic: str | None = None,
    company: str | None = None,
    mode: str = "technical",
    language: str | None = None,
) -> str | None:
    payload = _generate_json(
        f"""
        You are a realistic interviewer asking a follow-up question.
        Interview mode: {mode}
        Role: {role or "General"}
        Topic: {topic or "General"}
        Company style: {get_company_profile(company)}
        Programming language: {language or "Not specified"}
        Original question: {question}
        Candidate answer: {answer}

        Return JSON with a single key "question".
        The follow-up should probe deeper into reasoning, tradeoffs, limitations, or examples.
        """
    )
    if not isinstance(payload, dict):
        return None

    follow_up = str(payload.get("question", "")).strip()
    return follow_up or None


def generate_question_with_gemini(
    role: str,
    topic: str,
    difficulty: str,
    company: str | None = None,
    language: str | None = None,
    mode: str = "technical",
) -> str | None:
    payload = _generate_json(
        f"""
        You are preparing a mock interview question.
        Return JSON with a single string field named "question".
        The question should be specific, realistic, and suited for a {difficulty} {role} interview on the topic "{topic}".
        Interview mode: {mode}
        Company style: {get_company_profile(company)}
        Programming language: {language or "Not specified"}
        """
    )
    if not isinstance(payload, dict):
        return None

    question = str(payload.get("question", "")).strip()
    return question or None


def generate_resume_interview_with_gemini(
    role: str,
    topic: str,
    difficulty: str,
    resume_text: str,
    company: str | None = None,
    language: str | None = None,
    mode: str = "technical",
) -> dict | None:
    payload = _generate_json(
        f"""
        You are preparing a targeted interview question based on a candidate resume.
        Return JSON with keys:
        - question: string
        - resumeInsights: array of 2-3 short strings describing why this question fits the resume
        The role is "{role}".
        The interview topic is "{topic}".
        The difficulty is "{difficulty}".
        The interview mode is "{mode}".
        The company style is "{get_company_profile(company)}".
        The programming language is "{language or 'Not specified'}".
        Resume:
        {resume_text[:8000]}
        """
    )
    if not isinstance(payload, dict):
        return None

    question = str(payload.get("question", "")).strip()
    insights = payload.get("resumeInsights", [])
    if not isinstance(insights, list):
        insights = []

    if not question:
        return None

    return {
        "question": question,
        "resumeInsights": [str(item).strip() for item in insights[:3] if str(item).strip()],
    }


def rewrite_resume_text(role: str, original_text: str) -> str | None:
    payload = _generate_json(
        f"""
        Rewrite the following resume bullet or short section for a {role} role.
        Make it specific, concise, and impact-oriented.
        Return JSON with one key "rewrittenText".

        Original text:
        {original_text}
        """
    )
    if not isinstance(payload, dict):
        return None
    rewritten_text = str(payload.get("rewrittenText", "")).strip()
    return rewritten_text or None


def build_coaching_summary(history: list[dict]) -> dict | None:
    payload = _generate_json(
        f"""
        You are a personal AI interview coach.
        Analyze the interview history below and return JSON with:
        - summary: short paragraph
        - recommendedTopics: array of 3 short topic strings
        - focusAreas: array of 3 short actionable recommendations

        History:
        {json.dumps(history)[:12000]}
        """
    )
    if not isinstance(payload, dict):
        return None
    return {
        "summary": str(payload.get("summary", "")).strip(),
        "recommendedTopics": [
            str(item).strip() for item in payload.get("recommendedTopics", [])[:3] if str(item).strip()
        ],
        "focusAreas": [
            str(item).strip() for item in payload.get("focusAreas", [])[:3] if str(item).strip()
        ],
    }


def generate_study_plan_with_gemini(
    role: str,
    hours_per_week: int,
    duration_weeks: int,
) -> list[dict] | None:
    payload = _generate_json(
        f"""
        Create a practical interview study plan for a {role}.
        The candidate can study {hours_per_week} hours per week for {duration_weeks} weeks.
        Return JSON as an array of objects. Each object must contain:
        "phase" (string), "weeks" (integer), "focus" (string), and "hours" (integer).
        """
    )
    if not isinstance(payload, list):
        return None

    plan: list[dict] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        try:
            plan.append(
                {
                    "phase": str(item.get("phase", "Practice")).strip() or "Practice",
                    "weeks": max(1, int(item.get("weeks", 1))),
                    "focus": str(item.get("focus", "Interview preparation")).strip()
                    or "Interview preparation",
                    "hours": max(1, int(item.get("hours", 1))),
                }
            )
        except (TypeError, ValueError):
            continue

    return plan or None
