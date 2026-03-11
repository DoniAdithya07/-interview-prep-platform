from pydantic import BaseModel, Field


class UserRegister(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: str = Field(..., min_length=5, max_length=200)
    password: str = Field(..., min_length=6, max_length=100)


class UserLogin(BaseModel):
    email: str = Field(..., min_length=5, max_length=200)
    password: str = Field(..., min_length=6, max_length=100)


class AuthResponse(BaseModel):
    token: str
    user: dict


class InterviewQuestion(BaseModel):
    role: str = Field(..., min_length=2, max_length=100)
    topic: str = Field(..., min_length=2, max_length=100)
    difficulty: str = Field(..., pattern="^(easy|medium|hard)$")


class StudyPlanRequest(BaseModel):
    role: str = Field(..., min_length=2, max_length=100)
    hours_per_week: int = Field(..., ge=1, le=80)
    duration_weeks: int = Field(..., ge=1, le=52)


class AnswerSubmission(BaseModel):
    interviewId: str = Field(..., min_length=1)
    question: str = Field(..., min_length=5)
    answer: str = Field(..., min_length=1)


class AnswerEvaluationResponse(BaseModel):
    score: int
    feedback: str
