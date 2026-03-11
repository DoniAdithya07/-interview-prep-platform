"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

interface HistoryItem {
  id: string;
  type: string;
  score: number;
  createdAt: string;
  questions: string[];
}

export default function HistoryPage() {
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const token = localStorage.getItem("token");
        const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "http://127.0.0.1:8000";
        const res = await fetch(`${backendUrl}/api/history/questions`, {
          headers: {
            ...(token && { Authorization: `Bearer ${token}` }),
          },
        });
        
        if (!res.ok) throw new Error("Failed to fetch history");

        const data = await res.json();
        setHistory(data.items);
      } catch (err) {
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchHistory();
  }, []);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-black text-white p-8 md:p-16">
        <h1 className="text-3xl font-bold mb-8">Interview History</h1>
        <p className="animate-pulse text-gray-400">Loading your past sessions...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-black text-white p-8 md:p-16">
      <div className="max-w-4xl mx-auto">
        <div className="flex justify-between items-end mb-8 border-b border-gray-800 pb-4">
          <div>
            <h1 className="text-3xl font-bold">Interview History</h1>
            <p className="text-gray-400 mt-2">Review your past answers and AI feedback</p>
          </div>
          <Link href="/dashboard" className="text-blue-500 hover:text-blue-400 text-sm font-medium">
            &larr; Back to Dashboard
          </Link>
        </div>

        {history.length === 0 ? (
          <div className="text-center py-16 bg-gray-900 border border-gray-800 rounded-xl">
            <p className="text-gray-400 mb-4">You haven't completed any interviews yet.</p>
            <Link href="/interview" className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded font-medium transition-colors">
              Start an Interview
            </Link>
          </div>
        ) : (
          <div className="grid gap-4">
            {history.map((session) => (
              <Link 
                key={session.id} 
                href={`/results/${session.id}`}
                className="block bg-gray-900 border border-gray-800 rounded-xl p-6 hover:border-gray-600 transition-colors group cursor-pointer"
              >
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <span className="px-2 py-1 bg-gray-800 rounded text-xs font-semibold uppercase tracking-wider text-gray-300">
                        {session.type || "General"}
                      </span>
                      <span className="text-gray-500 text-sm">
                        {new Date(session.createdAt).toLocaleDateString()}
                      </span>
                    </div>
                    <p className="text-gray-200 font-medium line-clamp-2">
                      {session.questions?.[0] || "Unknown Question"}
                    </p>
                  </div>
                  
                  <div className="flex items-center gap-6">
                    <div className="text-right">
                      <p className="text-sm text-gray-500">Score</p>
                      <p className={`text-2xl font-bold ${session.score >= 80 ? 'text-green-500' : session.score >= 60 ? 'text-yellow-500' : 'text-red-500'}`}>
                        {session.score || 0}
                      </p>
                    </div>
                    
                    <div className="text-gray-600 group-hover:text-blue-500 transition-colors">
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                      </svg>
                    </div>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
