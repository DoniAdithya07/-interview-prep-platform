from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from backend.app.api import evaluate as evaluate_api
from backend.app.api import history as history_api
from backend.app.api import interview as interview_api
from backend.app.models.interview import AnswerSubmission, InterviewQuestion
from backend.app.services import progress_service


class FakeDocSnapshot:
    def __init__(self, doc_id: str, data: dict | None):
        self.id = doc_id
        self._data = data

    @property
    def exists(self) -> bool:
        return self._data is not None

    def to_dict(self) -> dict | None:
        return self._data


class FakeDocumentReference:
    def __init__(self, store: dict, collection_name: str, doc_id: str):
        self.store = store
        self.collection_name = collection_name
        self.doc_id = doc_id

    def get(self) -> FakeDocSnapshot:
        return FakeDocSnapshot(self.doc_id, self.store[self.collection_name].get(self.doc_id))

    def update(self, payload: dict) -> None:
        if self.doc_id not in self.store[self.collection_name]:
            raise KeyError(self.doc_id)
        self.store[self.collection_name][self.doc_id].update(payload)

    def set(self, payload: dict, merge: bool = False) -> None:
        current = self.store[self.collection_name].get(self.doc_id, {}) if merge else {}
        current.update(payload)
        self.store[self.collection_name][self.doc_id] = current


class FakeQuery:
    def __init__(self, docs: list[FakeDocSnapshot]):
        self.docs = docs

    def where(self, field: str, op: str, value):
        assert op == "=="
        return FakeQuery(
            [doc for doc in self.docs if (doc.to_dict() or {}).get(field) == value]
        )

    def order_by(self, field: str, direction=None):
        reverse = str(direction).upper().endswith("DESCENDING")
        return FakeQuery(
            sorted(
                self.docs,
                key=lambda doc: (doc.to_dict() or {}).get(field) or "",
                reverse=reverse,
            )
        )

    def stream(self):
        return iter(self.docs)


class FakeCollection:
    def __init__(self, store: dict, name: str):
        self.store = store
        self.name = name

    def document(self, doc_id: str) -> FakeDocumentReference:
        return FakeDocumentReference(self.store, self.name, doc_id)

    def add(self, payload: dict):
        doc_id = f"{self.name}-{len(self.store[self.name]) + 1}"
        self.store[self.name][doc_id] = payload
        return None, SimpleNamespace(id=doc_id)

    def where(self, field: str, op: str, value):
        docs = [
            FakeDocSnapshot(doc_id, data)
            for doc_id, data in self.store[self.name].items()
            if data.get(field) == value
        ]
        return FakeQuery(docs)

    def stream(self):
        return iter(
            [FakeDocSnapshot(doc_id, data) for doc_id, data in self.store[self.name].items()]
        )


class FakeDB:
    def __init__(self, store: dict):
        self.store = store

    def collection(self, name: str) -> FakeCollection:
        self.store.setdefault(name, {})
        return FakeCollection(self.store, name)


@pytest.fixture
def fake_store():
    return {
        "interviews": {},
        "progress": {},
        "study_plan_history": {},
    }


def test_create_question_starts_in_progress(monkeypatch, fake_store):
    fake_db = FakeDB(fake_store)
    monkeypatch.setattr(interview_api, "get_db", lambda: fake_db)
    monkeypatch.setattr(
        interview_api,
        "generate_question",
        lambda payload: {
            "role": payload.role,
            "topic": payload.topic,
            "difficulty": payload.difficulty,
            "question": "Explain idempotency in APIs.",
        },
    )

    response = interview_api.create_question(
        InterviewQuestion(role="Backend Engineer", topic="API Design", difficulty="medium"),
        {"id": "user-1", "email": "user@example.com"},
    )

    assert response.interviewId == "interviews-1"
    created = fake_store["interviews"]["interviews-1"]
    assert created["status"] == "in_progress"
    assert fake_store["progress"] == {}


def test_evaluate_rejects_other_users(monkeypatch, fake_store):
    fake_store["interviews"]["int-1"] = {
        "userId": "owner-1",
        "type": "Behavioral",
        "questions": ["Tell me about a challenge."],
        "answers": [],
        "score": 0,
        "aiFeedback": "",
        "status": "in_progress",
    }
    fake_db = FakeDB(fake_store)
    monkeypatch.setattr(evaluate_api, "get_db", lambda: fake_db)

    with pytest.raises(HTTPException) as exc_info:
        evaluate_api.evaluate(
            AnswerSubmission(
                interviewId="int-1",
                question="Valid interview question",
                answer="A detailed answer",
            ),
            {"id": "user-2", "email": "intruder@example.com"},
        )

    assert exc_info.value.status_code == 403


def test_evaluate_updates_interview_and_progress(monkeypatch, fake_store):
    fake_store["interviews"]["int-1"] = {
        "userId": "user-1",
        "type": "Behavioral",
        "questions": ["Tell me about a challenge."],
        "answers": [],
        "score": 0,
        "aiFeedback": "",
        "status": "in_progress",
    }
    fake_db = FakeDB(fake_store)
    monkeypatch.setattr(evaluate_api, "get_db", lambda: fake_db)
    monkeypatch.setattr(progress_service, "get_db", lambda: fake_db)
    monkeypatch.setattr(
        evaluate_api,
        "evaluate_answer",
        lambda payload: {
            "score": 88,
            "feedback": "Solid",
            "scoreBreakdown": {
                "communication": 84,
                "clarity": 87,
                "technicalAccuracy": 93,
            },
            "strengths": ["Clear structure"],
            "improvements": ["Add more detail"],
        },
    )

    response = evaluate_api.evaluate(
        AnswerSubmission(
            interviewId="int-1",
            question="Tell me about a challenge you resolved.",
            answer="I structured the problem, aligned stakeholders, and measured the result.",
            duration_seconds=42,
        ),
        {"id": "user-1", "email": "user@example.com"},
    )

    interview = fake_store["interviews"]["int-1"]
    assert response.score == 88
    assert interview["status"] == "completed"
    assert interview["duration"] == 42
    assert interview["scoreBreakdown"]["technicalAccuracy"] == 93
    assert fake_store["progress"]["user-1"]["totalInterviews"] == 1
    assert fake_store["progress"]["user-1"]["avgScore"] == 88.0


def test_history_item_blocks_access_to_other_users(monkeypatch, fake_store):
    fake_store["interviews"]["int-1"] = {
        "userId": "user-1",
        "type": "Behavioral",
        "questions": ["Question"],
        "answers": ["Answer"],
        "score": 80,
        "aiFeedback": "Feedback",
        "status": "completed",
        "createdAt": "2026-03-12T00:00:00+00:00",
    }
    fake_db = FakeDB(fake_store)
    monkeypatch.setattr(history_api, "get_db", lambda: fake_db)

    with pytest.raises(HTTPException) as exc_info:
        history_api.question_history_item("int-1", {"id": "user-2", "email": "other@example.com"})

    assert exc_info.value.status_code == 403
