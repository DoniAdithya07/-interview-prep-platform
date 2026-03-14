from backend.app.models.interview import AnswerSubmission
from backend.app.services.ai_service import evaluate_with_gemini

REASONING_MARKERS = ["because", "therefore", "tradeoff", "trade-off", "impact", "decision", "why"]
EXAMPLE_MARKERS = ["example", "for instance", "project", "production", "customer", "team"]
TECHNICAL_MARKERS = [
    "complexity",
    "latency",
    "testing",
    "scalable",
    "edge case",
    "performance",
    "cache",
    "api",
    "database",
]


def _clamp(score: int) -> int:
    return max(0, min(100, score))


def _compute_rubric(answer: str, question: str) -> tuple[dict, list[str]]:
    normalized = answer.lower()
    word_count = len(answer.split())
    reasons: list[str] = []

    communication = 35
    clarity = 35
    technical_accuracy = 35

    if word_count >= 25:
        communication += 15
        clarity += 10
        technical_accuracy += 10
        reasons.append("Answer length is sufficient to evaluate structure and depth.")
    elif word_count < 12:
        reasons.append("Answer is brief, which lowers scoring confidence.")

    reasoning_hits = sum(marker in normalized for marker in REASONING_MARKERS)
    example_hits = sum(marker in normalized for marker in EXAMPLE_MARKERS)
    technical_hits = sum(marker in normalized for marker in TECHNICAL_MARKERS)

    communication += min(20, example_hits * 7)
    clarity += min(20, reasoning_hits * 7)
    technical_accuracy += min(25, technical_hits * 6)

    if any(term in normalized for term in ["first", "second", "finally", "step", "approach"]):
        clarity += 10
        reasons.append("Answer uses explicit structure.")
    if any(term in normalized for term in ["tradeoff", "trade-off", "pros", "cons", "limitation"]):
        technical_accuracy += 10
        reasons.append("Answer discusses tradeoffs or limitations.")

    if question.lower().find("behavior") >= 0 or any(
        term in question.lower() for term in ["conflict", "teammate", "challenge", "situation"]
    ):
        if any(term in normalized for term in ["result", "outcome", "learned"]):
            communication += 8
            clarity += 5
            reasons.append("Behavioral answer includes outcome or learning.")

    breakdown = {
        "communication": _clamp(communication),
        "clarity": _clamp(clarity),
        "technicalAccuracy": _clamp(technical_accuracy),
    }
    return breakdown, reasons


def _build_star_breakdown(answer: str) -> dict | None:
    normalized = answer.lower()
    markers = {
        "situation": ["situation", "context", "background", "at the time"],
        "task": ["task", "goal", "responsibility", "needed to"],
        "action": ["action", "i did", "implemented", "led", "built", "designed"],
        "result": ["result", "outcome", "improved", "reduced", "increased", "saved"],
    }
    scores = {}
    detected = False
    for key, words in markers.items():
        hits = sum(1 for word in words if word in normalized)
        score = 45 + hits * 15
        if hits == 0:
            score -= 5
        score = min(100, max(30, score))
        scores[key] = score
        detected = detected or hits > 0
    return scores if detected else None


def _build_accuracy(method: str, confidence_label: str, reasons: list[str]) -> dict:
    return {
        "method": method,
        "confidenceLabel": confidence_label,
        "confidenceReasons": reasons[:4],
    }


def _heuristic_feedback(score: int, breakdown: dict, star_breakdown: dict | None) -> tuple[str, list[str], list[str]]:
    strengths: list[str] = []
    improvements: list[str] = []

    if breakdown["clarity"] >= 70:
        strengths.append("Your explanation is organized and easy to follow.")
    if breakdown["communication"] >= 70:
        strengths.append("You communicate with enough context for an interviewer to track your thinking.")
    if breakdown["technicalAccuracy"] >= 70:
        strengths.append("You mention meaningful technical considerations instead of only giving a surface answer.")

    if breakdown["clarity"] < 65:
        improvements.append("Structure the answer explicitly with steps, reasoning, and a concise conclusion.")
    if breakdown["communication"] < 65:
        improvements.append("Use a concrete project or production example to make the answer more persuasive.")
    if breakdown["technicalAccuracy"] < 65:
        improvements.append("Add tradeoffs, edge cases, or technical constraints to deepen the answer.")
    if star_breakdown and min(star_breakdown.values()) < 60:
        improvements.append("For behavioral questions, make the STAR flow explicit: situation, task, action, result.")

    if score >= 80:
        feedback = "Strong answer overall. You show useful depth and enough structure to sound interview-ready."
    elif score >= 65:
        feedback = "Solid start, but the answer still needs sharper structure and more explicit technical depth."
    else:
        feedback = "The answer is directionally correct, but too much of the reasoning is implied rather than stated."

    if not strengths:
        strengths.append("You attempted a direct response to the prompt.")
    if not improvements:
        improvements.append("Tighten the final summary so the interviewer hears the main takeaway clearly.")

    return feedback, strengths[:3], improvements[:3]


def evaluate_answer(payload: AnswerSubmission) -> dict:
    breakdown, rubric_reasons = _compute_rubric(payload.answer, payload.question)
    star_breakdown = _build_star_breakdown(payload.answer)
    rubric_score = round(
        (breakdown["communication"] + breakdown["clarity"] + breakdown["technicalAccuracy"]) / 3
    )

    ai_result = evaluate_with_gemini(payload.question, payload.answer)
    if ai_result is not None:
        ai_breakdown = ai_result["scoreBreakdown"]
        blended_breakdown = {
            key: round((breakdown[key] * 0.4) + (ai_breakdown[key] * 0.6))
            for key in breakdown
        }
        blended_score = round((rubric_score * 0.35) + (int(ai_result["score"]) * 0.65))
        confidence_reasons = rubric_reasons + [
            "Model scoring is blended with a deterministic rubric instead of being used raw.",
        ]
        if len(payload.answer.split()) >= 35:
            confidence_reasons.append("Longer answer length increases evaluation confidence.")
        return {
            "score": blended_score,
            "feedback": ai_result["feedback"],
            "scoreBreakdown": blended_breakdown,
            "starBreakdown": star_breakdown,
            "strengths": ai_result.get("strengths", [])[:3],
            "improvements": ai_result.get("improvements", [])[:3],
            "accuracy": _build_accuracy("ai_blended_rubric", "medium", confidence_reasons),
        }

    feedback, strengths, improvements = _heuristic_feedback(rubric_score, breakdown, star_breakdown)
    confidence = "medium" if len(payload.answer.split()) >= 25 else "low"
    confidence_reasons = rubric_reasons + [
        "AI scoring was unavailable, so the score uses a structured heuristic rubric.",
    ]
    return {
        "score": rubric_score,
        "feedback": feedback,
        "scoreBreakdown": breakdown,
        "starBreakdown": star_breakdown,
        "strengths": strengths,
        "improvements": improvements,
        "accuracy": _build_accuracy("structured_heuristic_rubric", confidence, confidence_reasons),
    }
