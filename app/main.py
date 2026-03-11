from datetime import datetime
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from firebase_admin import firestore

from app.auth import create_token, get_current_user, hash_password, verify_password
from app.firestore import db
from app.schemas import (
    AuthResponse,
    InterviewQuestion,
    StudyPlanRequest,
    UserLogin,
    UserRegister,
    AnswerSubmission,
)
from app.services import generate_question, generate_study_plan, evaluate_answer

BASE_DIR = Path(__file__).resolve().parent.parent

app = FastAPI(title="Interview Prep Platform", version="1.0.0")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "title": "Interview Prep Platform",
        },
    )


@app.post("/api/auth/register", response_model=AuthResponse)
def register(payload: UserRegister) -> dict:
    email = payload.email.strip().lower()
    users_ref = db.collection("users")
    existing = users_ref.where("email", "==", email).get()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered",
        )

    user_ref = users_ref.document()
    user_data = {
        "name": payload.name.strip(),
        "email": email,
        "password_hash": hash_password(payload.password),
        "created_at": datetime.utcnow(),
    }
    user_ref.set(user_data)

    token = create_token(user_ref.id)
    return {
        "token": token,
        "user": {
            "id": user_ref.id,
            "name": user_data["name"],
            "email": user_data["email"],
        },
    }


@app.post("/api/auth/login", response_model=AuthResponse)
def login(payload: UserLogin) -> dict:
    email = payload.email.strip().lower()
    users = db.collection("users").where("email", "==", email).get()

    if not users:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    user_doc = users[0]
    user_data = user_doc.to_dict()

    if not verify_password(payload.password, user_data["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    token = create_token(user_doc.id)
    return {
        "token": token,
        "user": {
            "id": user_doc.id,
            "name": user_data["name"],
            "email": user_data["email"],
        },
    }


@app.post("/api/question")
def question(payload: InterviewQuestion, user: dict = Depends(get_current_user)) -> dict:
    result = generate_question(payload)
    interview_doc = {
        "userId": user["id"],
        "type": "Core",
        "questions": [result["question"]],
        "answers": [],
        "score": 0,
        "aiFeedback": "",
        "duration": 0,
        "createdAt": datetime.utcnow(),
    }
    _, doc_ref = db.collection("interviews").add(interview_doc)

    progress_ref = db.collection("progress").document(user["id"])
    progress_doc = progress_ref.get()
    if progress_doc.exists:
        data = progress_doc.to_dict()
        old_total = int(data.get("totalInterviews", 0))
        old_avg = float(data.get("avgScore", 0))
        new_total = old_total + 1
        new_avg = ((old_avg * old_total) + interview_doc["score"]) / new_total
        topic_breakdown = data.get("topicBreakdown", {})
        topic_key = payload.topic.strip().lower()
        topic_breakdown[topic_key] = int(topic_breakdown.get(topic_key, 0)) + 1
        progress_ref.set(
            {
                "totalInterviews": new_total,
                "avgScore": new_avg,
                "topicBreakdown": topic_breakdown,
                "streakDays": int(data.get("streakDays", 0)),
                "lastActive": datetime.utcnow(),
            },
            merge=True,
        )
    else:
        progress_ref.set(
            {
                "totalInterviews": 1,
                "avgScore": interview_doc["score"],
                "topicBreakdown": {payload.topic.strip().lower(): 1},
                "streakDays": 1,
                "lastActive": datetime.utcnow(),
            }
        )

    result["interviewId"] = doc_ref.id
    return result


@app.post("/api/evaluate")
def evaluate(payload: AnswerSubmission, user: dict = Depends(get_current_user)) -> dict:
    result = evaluate_answer(payload)
    
    # Update the interview score and feedback
    db.collection("interviews").document(payload.interviewId).update({
        "answers": [payload.answer],
        "score": result["score"],
        "aiFeedback": result["feedback"]
    })
    
    return result


@app.post("/api/study-plan")
def study_plan(payload: StudyPlanRequest, user: dict = Depends(get_current_user)) -> dict:
    plan = generate_study_plan(payload)
    db.collection("study_plan_history").add(
        {
            "user_id": user["id"],
            "role": payload.role,
            "hours_per_week": payload.hours_per_week,
            "duration_weeks": payload.duration_weeks,
            "plan": plan,
            "created_at": datetime.utcnow(),
        }
    )
    return {"plan": plan}


@app.get("/api/history/questions")
def question_history(user: dict = Depends(get_current_user)) -> dict:
    docs = (
        db.collection("interviews")
        .where("userId", "==", user["id"])
        .order_by("createdAt", direction=firestore.Query.DESCENDING)
        .stream()
    )
    items = []
    for doc in docs:
        item = doc.to_dict()
        item["id"] = doc.id
        items.append(item)
    return {"items": items}


@app.get("/api/history/study-plans")
def study_plan_history(user: dict = Depends(get_current_user)) -> dict:
    docs = (
        db.collection("study_plan_history")
        .where("user_id", "==", user["id"])
        .order_by("created_at", direction=firestore.Query.DESCENDING)
        .stream()
    )
    items = []
    for doc in docs:
        item = doc.to_dict()
        item["id"] = doc.id
        items.append(item)
    return {"items": items}
