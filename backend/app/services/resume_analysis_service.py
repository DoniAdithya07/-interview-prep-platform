from backend.app.models.result import AccuracyMetadata, ResumeAnalysisResult


def analyze_resume_against_job_description(resume_text: str, job_description: str) -> ResumeAnalysisResult:
    # Lightweight heuristic placeholder to keep local runs working without heavy NLP deps.
    resume_words = set(resume_text.lower().split())
    job_words = set(job_description.lower().split())
    matched = sorted(list(resume_words & job_words))[:10]
    missing = sorted(list(job_words - resume_words))[:10]

    match_score = int(min(100, max(10, (len(matched) / (len(job_words) + 1)) * 100)))
    ats_score = max(50, min(95, match_score + 10))

    return ResumeAnalysisResult(
        atsScore=ats_score,
        matchScore=match_score,
        missingKeywords=missing,
        matchedKeywords=matched,
        summary="Heuristic resume/job description match run locally (no NLP dependencies).",
        sectionFeedback=[],
        accuracy=AccuracyMetadata(
            method="lightweight_keyword_overlap",
            confidenceLabel="low",
            confidenceReasons=[
                "Using simple keyword overlap because NLP dependencies are unavailable in this environment."
            ],
        ),
    )
