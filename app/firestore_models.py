from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class FirestoreUser(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: str = Field(..., min_length=5, max_length=200)
    role: str = Field(..., min_length=2, max_length=100)
    createdAt: str
    profilePicture: Optional[str] = None


class FirestoreInterview(BaseModel):
    userId: str = Field(..., min_length=1)
    type: Literal["DSA", "HR", "Core"]
    questions: List[str]
    answers: List[str]
    score: float
    aiFeedback: str
    duration: int = Field(..., ge=1)
    createdAt: str


class FirestoreProgress(BaseModel):
    totalInterviews: int = Field(..., ge=0)
    avgScore: float = Field(..., ge=0)
    topicBreakdown: Dict[str, float]
    streakDays: int = Field(..., ge=0)
    lastActive: str
