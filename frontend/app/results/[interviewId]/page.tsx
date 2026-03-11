"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";

interface ResultData {
  question: string;
  answer: string;
  score: number;
  feedback: string;
  date: string;
}

export default function ResultsPage() {
  const params = useParams();
  const router = useRouter();
  const interviewId = params.interviewId as string;
  
  const [data, setData] = useState<ResultData | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // In a full implementation, you'd fetch the specific interview from a new `/api/interview/{id}` endpoint.
    // However, since we already built `/api/history/questions`, we can use it to find our specific interview.
    const fetchResults = async () => {
      try {
        const token = localStorage.getItem("token");
        const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "http://127.0.0.1:8000";
        const res = await fetch(`${backendUrl}/api/history/questions`, {
          headers: {
            ...(token && { Authorization: `Bearer ${token}` }),
          },
        });
        if (!res.ok) throw new Error("Failed to load results");
        const historyData = await res.json();
        
        // Find our specific session
        const session = historyData.items.find((item: any) => item.id === interviewId);
        if (session) {
          setData({
            question: session.questions[0], // Assuming 1 question per session for now
            answer: session.answers[0] || "No answer provided.",
            score: session.score,
            feedback: session.aiFeedback,
            date: new Date(session.createdAt).toLocaleDateString()
          });
        }
      } catch (err) {
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    };

    if (interviewId) {
      fetchResults();
    }
  }, [interviewId]);

  if (isLoading) {
    return (
      <div className="flex min-h-screen bg-black text-white items-center justify-center">
        <p className="animate-pulse">Analyzing results...</p>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="flex flex-col min-h-screen bg-black text-white items-center justify-center gap-4">
        <p>Could not load results. They may still be processing.</p>
        <button onClick={() => router.push('/dashboard')} className="text-blue-500 underline">Return to Dashboard</button>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-black text-white p-8 md:p-16 flex flex-col items-center">
      <div className="w-full max-w-3xl space-y-8">
        <div className="text-center">
          <h1 className="text-4xl font-bold mb-2">Interview Results</h1>
          <p className="text-gray-400">Completed on {data.date}</p>
        </div>

        <div className="flex flex-col md:flex-row gap-6">
          {/* Score Card */}
          <div className="flex-1 bg-gray-900 border border-gray-800 rounded-xl p-6 flex flex-col items-center justify-center">
            <h2 className="text-xl font-semibold mb-2 text-gray-400">Your Score</h2>
            <div className={`text-6xl font-bold ${data.score >= 80 ? 'text-green-500' : data.score >= 60 ? 'text-yellow-500' : 'text-red-500'}`}>
              {data.score}
            </div>
            <p className="text-sm mt-2 text-gray-500">out of 100</p>
          </div>

          {/* Feedback Card */}
          <div className="flex-[2] bg-gray-900 border border-gray-800 rounded-xl p-6">
            <h2 className="text-xl font-semibold mb-3 text-blue-400">AI Feedback</h2>
            <p className="text-gray-300 leading-relaxed">{data.feedback}</p>
          </div>
        </div>

        <div className="space-y-6">
          {/* Question / Answer Review */}
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
            <h3 className="text-sm font-semibold uppercase text-gray-500 mb-2">The Question</h3>
            <p className="text-lg">{data.question}</p>
          </div>

          <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
            <h3 className="text-sm font-semibold uppercase text-gray-500 mb-2">Your Answer</h3>
            <p className="text-gray-300 whitespace-pre-wrap">{data.answer}</p>
          </div>
        </div>

        <div className="pt-6 flex gap-4 justify-center">
          <Link href="/interview" className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors">
            Practice Another
          </Link>
          <Link href="/dashboard" className="px-6 py-3 bg-gray-800 hover:bg-gray-700 text-white border border-gray-700 rounded-lg font-medium transition-colors">
            Back to Dashboard
          </Link>
        </div>
      </div>
    </div>
  );
}
