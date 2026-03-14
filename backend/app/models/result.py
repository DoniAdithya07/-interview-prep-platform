from pydantic import BaseModel, Field


class AccuracyMetadata(BaseModel):
    method: str
    confidenceLabel: str = Field(..., pattern="^(high|medium|low)$")
    confidenceReasons: list[str] = Field(default_factory=list)


class ScoreBreakdown(BaseModel):
    communication: int = Field(..., ge=0, le=100)
    clarity: int = Field(..., ge=0, le=100)
    technicalAccuracy: int = Field(..., ge=0, le=100)


class StarBreakdown(BaseModel):
    situation: int = Field(..., ge=0, le=100)
    task: int = Field(..., ge=0, le=100)
    action: int = Field(..., ge=0, le=100)
    result: int = Field(..., ge=0, le=100)


class InterviewHistoryItem(BaseModel):
    id: str
    type: str | None = None
    score: int | float | None = None
    questions: list[str] = Field(default_factory=list)
    answers: list[str] = Field(default_factory=list)
    aiFeedback: str | None = None
    scoreBreakdown: ScoreBreakdown | None = None
    starBreakdown: StarBreakdown | None = None
    strengths: list[str] = Field(default_factory=list)
    improvements: list[str] = Field(default_factory=list)
    resumeInsights: list[str] = Field(default_factory=list)
    followUps: list[str] = Field(default_factory=list)
    role: str | None = None
    company: str | None = None
    language: str | None = None
    mode: str = "technical"
    createdAt: str | None = None
    completedAt: str | None = None
    status: str = "in_progress"
    duration: int = 0
    accuracy: AccuracyMetadata | None = None


class HistoryResponse(BaseModel):
    items: list[InterviewHistoryItem]


class EvaluationResult(BaseModel):
    score: int
    feedback: str
    scoreBreakdown: ScoreBreakdown
    starBreakdown: StarBreakdown | None = None
    strengths: list[str] = Field(default_factory=list)
    improvements: list[str] = Field(default_factory=list)
    accuracy: AccuracyMetadata


class ResumeAnalysisResult(BaseModel):
    atsScore: int = Field(..., ge=0, le=100)
    matchScore: int = Field(..., ge=0, le=100)
    missingKeywords: list[str] = Field(default_factory=list)
    matchedKeywords: list[str] = Field(default_factory=list)
    summary: str
    sectionFeedback: list[str] = Field(default_factory=list)
    accuracy: AccuracyMetadata


class ProgressResponse(BaseModel):
    totalInterviews: int = 0
    avgScore: float = 0
    topicBreakdown: dict[str, int] = Field(default_factory=dict)
    streakDays: int = 0
    achievements: list[str] = Field(default_factory=list)


class LeaderboardEntry(BaseModel):
    rank: int
    userId: str
    displayName: str
    points: int
    avgScore: float = 0
    totalInterviews: int = 0
    streakDays: int = 0


class LeaderboardResponse(BaseModel):
    items: list[LeaderboardEntry] = Field(default_factory=list)
