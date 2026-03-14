from pydantic import BaseModel, Field


INTERVIEW_MODE_PATTERN = "^(technical|coding|behavioral|hr|system-design|ai-mock)$"


class InterviewQuestion(BaseModel):
    role: str = Field(..., min_length=2, max_length=100)
    topic: str = Field(..., min_length=2, max_length=100)
    difficulty: str = Field(..., pattern="^(easy|medium|hard)$")
    company: str | None = Field(default=None, max_length=100)
    language: str | None = Field(default=None, max_length=50)
    mode: str = Field(default="technical", pattern=INTERVIEW_MODE_PATTERN)


class StudyPlanRequest(BaseModel):
    role: str = Field(..., min_length=2, max_length=100)
    hours_per_week: int = Field(..., ge=1, le=80)
    duration_weeks: int = Field(..., ge=1, le=52)


class AnswerSubmission(BaseModel):
    interviewId: str = Field(..., min_length=1)
    question: str = Field(..., min_length=5)
    answer: str = Field(..., min_length=1)
    duration_seconds: int | None = Field(default=None, ge=0, le=14400)
    language: str | None = Field(default=None, max_length=50)


class InterviewQuestionResponse(BaseModel):
    interviewId: str
    role: str
    topic: str
    difficulty: str
    question: str
    company: str | None = None
    language: str | None = None
    mode: str = "technical"
    resumeUsed: bool = False
    resumeInsights: list[str] = Field(default_factory=list)


class StudyPlanResponse(BaseModel):
    plan: list[dict]


class FollowUpQuestionRequest(BaseModel):
    interviewId: str = Field(..., min_length=1)
    question: str = Field(..., min_length=5)
    answer: str = Field(..., min_length=1)
    role: str | None = Field(default=None, max_length=100)
    topic: str | None = Field(default=None, max_length=100)
    company: str | None = Field(default=None, max_length=100)
    mode: str = Field(default="technical", pattern=INTERVIEW_MODE_PATTERN)
    language: str | None = Field(default=None, max_length=50)


class FollowUpQuestionResponse(BaseModel):
    question: str


class ResumeRewriteRequest(BaseModel):
    role: str = Field(..., min_length=2, max_length=100)
    original_text: str = Field(..., min_length=5, max_length=3000)


class ResumeRewriteResponse(BaseModel):
    rewritten_text: str


class CoachingResponse(BaseModel):
    summary: str
    recommended_topics: list[str] = Field(default_factory=list)
    focus_areas: list[str] = Field(default_factory=list)


class CodingExecutionRequest(BaseModel):
    language: str = Field(..., pattern="^(python|javascript)$")
    code: str = Field(..., min_length=1, max_length=20000)
    function_name: str = Field(..., min_length=1, max_length=100)
    test_cases: list[dict] = Field(default_factory=list)


class CodingExecutionResponse(BaseModel):
    passed: int
    total: int
    results: list[dict] = Field(default_factory=list)


class ComplexityAnalysisRequest(BaseModel):
    language: str = Field(..., min_length=2, max_length=50)
    code: str = Field(..., min_length=1, max_length=20000)


class ComplexityAnalysisResponse(BaseModel):
    time_complexity: str
    suggestions: list[str] = Field(default_factory=list)
    observations: list[str] = Field(default_factory=list)


class CommunityQuestionCreate(BaseModel):
    title: str = Field(..., min_length=5, max_length=200)
    role: str = Field(..., min_length=2, max_length=100)
    topic: str = Field(..., min_length=2, max_length=100)
    question: str = Field(..., min_length=10, max_length=2000)
    mode: str = Field(default="technical", pattern=INTERVIEW_MODE_PATTERN)
    company: str | None = Field(default=None, max_length=100)


class CommunityQuestionItem(BaseModel):
    id: str
    title: str
    role: str
    topic: str
    question: str
    mode: str
    company: str | None = None
    user_id: str
    created_at: str | None = None
    votes: int = 0
    reports: int = 0


class CommunityQuestionResponse(BaseModel):
    items: list[CommunityQuestionItem] = Field(default_factory=list)


class CommunityQuestionVoteRequest(BaseModel):
    question_id: str = Field(..., min_length=1)


class VoiceTranscriptionResponse(BaseModel):
    transcript: str
