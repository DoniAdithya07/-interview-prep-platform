"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import QuestionCard from "@/components/QuestionCard";
import AnswerBox from "@/components/AnswerBox";

export default function InterviewTypePage() {
  const params = useParams();
  const type = params.type as string; // 'dsa', 'hr', etc.
  
  const [question, setQuestion] = useState<string | null>(null);
  const [interviewId, setInterviewId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchQuestion = async () => {
      try {
        const token = localStorage.getItem("token");
        const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "http://127.0.0.1:8000";
        // We'll normalize type to match schema difficulty/role concepts, or simply pass it as topic
        const res = await fetch(`${backendUrl}/api/question`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            ...(token && { Authorization: `Bearer ${token}` }),
          },
          body: JSON.stringify({
            role: "Software Engineer", 
            topic: type === 'dsa' ? "Data Structures and Algorithms" : type === 'hr' ? "Behavioral" : "General",
            difficulty: "medium"
          })
        });
        
        if (!res.ok) throw new Error("Failed to load question");
        const data = await res.json();
        setQuestion(data.question);
        setInterviewId(data.interviewId);
      } catch (err) {
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchQuestion();
  }, [type]);

  if (isLoading) {
    return (
      <div className="flex bg-black text-white min-h-screen items-center justify-center">
        <p>Loading question...</p>
      </div>
    );
  }

  if (!question || !interviewId) {
    return (
      <div className="flex bg-black text-white min-h-screen items-center justify-center">
        <p>Could not load question. Please refresh to try again.</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center justify-center h-screen bg-black text-white p-10 gap-6">
      <QuestionCard question={question} />

      <AnswerBox question={question} interviewId={interviewId} />
    </div>
  );
}