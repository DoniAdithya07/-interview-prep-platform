import math
import re
from collections import Counter

from backend.app.models.result import ResumeAnalysisResult

try:
    import spacy
except ImportError:
    spacy = None

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
except ImportError:
    TfidfVectorizer = None


STOP_WORDS = {
    "the",
    "and",
    "for",
    "with",
    "that",
    "from",
    "this",
    "your",
    "have",
    "using",
    "into",
    "work",
    "worked",
    "build",
    "built",
    "role",
    "experience",
    "team",
    "project",
    "projects",
    "requirements",
    "requirement",
}

SKILL_SYNONYMS = {
    "javascript": {"js", "javascript", "ecmascript"},
    "typescript": {"ts", "typescript"},
    "react": {"react", "reactjs", "react.js"},
    "node": {"node", "nodejs", "node.js"},
    "aws": {"aws", "amazon web services"},
    "docker": {"docker", "containers"},
    "kubernetes": {"kubernetes", "k8s"},
    "ci/cd": {"ci/cd", "cicd", "continuous integration", "continuous delivery"},
    "system design": {"system design", "distributed systems", "scalability"},
    "sql": {"sql", "postgresql", "mysql", "sqlite"},
    "nosql": {"nosql", "mongodb", "cassandra", "dynamodb"},
    "testing": {"testing", "jest", "pytest", "unit test", "integration test"},
}


def _tokenize(text: str) -> list[str]:
    if spacy is not None:
        nlp = spacy.blank("en")
        doc = nlp(text.lower())
        return [
            token.text
            for token in doc
            if token.is_alpha and token.text not in STOP_WORDS and len(token.text) > 1
        ]
    return [
        token
        for token in re.findall(r"[A-Za-z][A-Za-z0-9+/.-]{1,}", text.lower())
        if token not in STOP_WORDS
    ]


def _cosine_similarity(counter_a: Counter, counter_b: Counter) -> float:
    if not counter_a or not counter_b:
        return 0.0

    shared = set(counter_a) & set(counter_b)
    numerator = sum(counter_a[token] * counter_b[token] for token in shared)
    denominator_a = math.sqrt(sum(value * value for value in counter_a.values()))
    denominator_b = math.sqrt(sum(value * value for value in counter_b.values()))
    if denominator_a == 0 or denominator_b == 0:
        return 0.0
    return numerator / denominator_a / denominator_b


def _extract_skill_hits(text: str) -> set[str]:
    normalized = text.lower()
    hits: set[str] = set()
    for canonical, variants in SKILL_SYNONYMS.items():
        if any(variant in normalized for variant in variants):
            hits.add(canonical)
    return hits


def _extract_keywords(job_description: str, token_counter: Counter) -> list[str]:
    ranked = [token for token, _ in token_counter.most_common(30)]
    skills = [skill for skill in SKILL_SYNONYMS if skill in job_description.lower()]
    merged = []
    for token in skills + ranked:
        if token not in merged:
            merged.append(token)
    return merged[:15]


def analyze_resume_against_job_description(
    resume_text: str,
    job_description: str,
) -> ResumeAnalysisResult:
    resume_tokens = _tokenize(resume_text)
    job_tokens = _tokenize(job_description)
    resume_counter = Counter(resume_tokens)
    job_counter = Counter(job_tokens)

    target_keywords = _extract_keywords(job_description, job_counter)
    resume_skill_hits = _extract_skill_hits(resume_text)
    job_skill_hits = _extract_skill_hits(job_description)

    matched = []
    missing = []
    for keyword in target_keywords:
        keyword_in_resume = keyword in resume_counter or keyword in resume_skill_hits
        if keyword_in_resume:
            matched.append(keyword)
        else:
            missing.append(keyword)

    keyword_recall = len(matched) / max(len(target_keywords), 1)
    skill_recall = len(job_skill_hits & resume_skill_hits) / max(len(job_skill_hits), 1)
    cosine = _cosine_similarity(resume_counter, job_counter)
    tfidf_similarity = 0.0
    if TfidfVectorizer is not None:
        vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
        matrix = vectorizer.fit_transform([resume_text, job_description])
        tfidf_similarity = float((matrix[0] @ matrix[1].T).toarray()[0][0])

    quantified_impact = 1.0 if re.search(r"\b\d+[%+x]?\b", resume_text) else 0.0
    section_quality = 1.0 if any(
        section in resume_text.lower()
        for section in ["experience", "projects", "skills", "education", "summary"]
    ) else 0.0

    semantic_score = max(cosine, tfidf_similarity)
    match_score = round(
        min(
            100,
            (
                semantic_score * 0.45
                + keyword_recall * 0.3
                + skill_recall * 0.2
                + quantified_impact * 0.05
            )
            * 100,
        )
    )
    ats_score = round(
        min(
            100,
            match_score * 0.75
            + section_quality * 10
            + quantified_impact * 8
            + max(0, 7 - len(missing[:7])) * 1,
        )
    )

    section_feedback: list[str] = []
    if missing:
        section_feedback.append(
            "Add missing role-specific keywords in experience or project bullets instead of a standalone skills list."
        )
    if not quantified_impact:
        section_feedback.append(
            "Add quantified outcomes such as latency reduction, user growth, cost savings, or delivery speed."
        )
    if not section_quality:
        section_feedback.append(
            "Use clearer resume sections such as Summary, Experience, Projects, Skills, and Education."
        )
    if len(resume_text.split()) < 140:
        section_feedback.append("Resume is brief. Expand ownership, scope, tools, and business impact.")
    if not section_feedback:
        section_feedback.append("Resume structure and keyword coverage are already strong for this job description.")

    confidence_reasons = []
    if TfidfVectorizer is not None:
        confidence_reasons.append("TF-IDF similarity is included in the scoring pipeline.")
    if spacy is not None:
        confidence_reasons.append("spaCy tokenization is active for cleaner keyword extraction.")
    if job_skill_hits:
        confidence_reasons.append("Skill synonyms are normalized before keyword matching.")
    confidence_label = "high" if TfidfVectorizer is not None and spacy is not None else "medium"

    summary = (
        f"ATS score is {ats_score}%. Resume-to-job match is {match_score}%. "
        f"{'Top missing keywords: ' + ', '.join(missing[:5]) + '.' if missing else 'Keyword coverage is strong.'}"
    )
    return ResumeAnalysisResult(
        atsScore=ats_score,
        matchScore=match_score,
        missingKeywords=[token.title() for token in missing[:10]],
        matchedKeywords=[token.title() for token in matched[:10]],
        summary=summary,
        sectionFeedback=section_feedback,
        accuracy={
            "method": "tfidf_plus_skill_normalization",
            "confidenceLabel": confidence_label,
            "confidenceReasons": confidence_reasons[:4],
        },
    )
