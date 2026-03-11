import os
import json
from typing import List

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

from app.schemas import InterviewQuestion, StudyPlanRequest, AnswerSubmission


def generate_question(payload: InterviewQuestion) -> dict:
    return {
        "role": payload.role,
        "topic": payload.topic,
        "difficulty": payload.difficulty,
        "question": (
            f"Explain a {payload.difficulty} {payload.topic} concept "
            f"relevant to a {payload.role} interview, and provide one real-world example."
        ),
    }


def generate_study_plan(payload: StudyPlanRequest) -> List[dict]:
    total_hours = payload.hours_per_week * payload.duration_weeks
    mock_interviews = max(1, payload.duration_weeks // 2)
    practice_hours = max(1, int(total_hours * 0.6))
    revision_hours = total_hours - practice_hours

    return [
        {
            "phase": "Core Concepts",
            "weeks": max(1, payload.duration_weeks // 2),
            "focus": f"{payload.role} fundamentals and key patterns",
            "hours": practice_hours,
        },
        {
            "phase": "Revision + Mock Interviews",
            "weeks": payload.duration_weeks - max(1, payload.duration_weeks // 2),
            "focus": f"Timed revision with {mock_interviews} mock interview sessions",
            "hours": revision_hours,
        },
    ]


def evaluate_answer(payload: AnswerSubmission) -> dict:
    openai_api_key = os.getenv("OPENAI_API_KEY")
    
    if openai_api_key and OpenAI is not None:
        try:
            client = OpenAI(api_key=openai_api_key)
            prompt = f"""
            You are an expert technical interviewer. Evaluate the following answer to the interview question.
            Provide a score from 0 to 100 based on accuracy, completeness, and clarity.
            Provide constructive feedback.
            Output your response strictly in JSON format with keys "score" (integer) and "feedback" (string).

            Question: {payload.question}
            Answer: {payload.answer}
            """
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert interviewer. You always respond in JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={ "type": "json_object" }
            )
            
            result_json = response.choices[0].message.content
            if result_json:
                result_data = json.loads(result_json)
                return {
                    "score": int(result_data.get("score", 0)),
                    "feedback": result_data.get("feedback", "No feedback provided.")
                }
        except Exception as e:
            print(f"OpenAI evaluation failed: {e}. Falling back to mock evaluation.")

    # Fallback / Mock implementation
    word_count = len(payload.answer.split())
    
    if word_count < 10:
        score = 40
        feedback = "Your answer is too short. Try to provide more details, mention real-world applications, and structure your explanation clearly. (Mock Feedback)"
    elif 10 <= word_count < 30:
        score = 70
        feedback = "Good start, but could be more comprehensive. Consider elaborating on edge cases and providing specific examples. (Mock Feedback)"
    else:
        score = 90
        feedback = "Excellent answer! You covered the concepts well and provided sufficient detail. (Mock Feedback)"
        
    return {
        "score": score,
        "feedback": feedback
    }
