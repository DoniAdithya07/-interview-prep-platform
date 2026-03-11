"use client";

import { useState } from "react";
import { useAuth } from "@/context/AuthContext";
import { useRouter } from "next/navigation";

export default function AnswerBox({ question, interviewId }: { question: string; interviewId: string }) {
  const [answer, setAnswer] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { user } = useAuth(); // or grab token from localStorage if AuthContext is not exporting user
  const router = useRouter();

  const handleSubmit = async () => {
    if (!answer.trim()) return;
    setIsSubmitting(true);

    try {
      const token = localStorage.getItem("token");
      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "http://127.0.0.1:8000";
      const response = await fetch(`${backendUrl}/api/evaluate`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token && { Authorization: `Bearer ${token}` }),
        },
        body: JSON.stringify({ interviewId, question, answer }),
      });

      if (!response.ok) {
        throw new Error("Evaluation failed");
      }

      await response.json();
      
      // Redirect to the results page instead of showing it inline
      router.push(`/results/${interviewId}`);
    } catch (error) {
      console.error(error);
      alert("Failed to submit answer.");
      setIsSubmitting(false); // Only stop loading if we failed (prevent UI flash if redirecting)
    }
  };

  return (
    <div className="mt-6 w-full max-w-md">
      <textarea
        className="w-full p-3 border rounded bg-black text-white"
        placeholder="Type your answer..."
        value={answer}
        onChange={(e) => setAnswer(e.target.value)}
      />

      <button
        className={`mt-3 px-4 py-2 ${isSubmitting ? 'bg-blue-400' : 'bg-blue-600'} text-white rounded font-medium`}
        onClick={handleSubmit}
        disabled={isSubmitting}
      >
        {isSubmitting ? "Evaluating..." : "Submit Answer"}
      </button>
    </div>
  );
}