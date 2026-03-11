"use client";

import { useEffect, useState } from "react";
import useRequireAuth from "@/hooks/useRequireAuth";
import Link from "next/link";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
} from "recharts";

export default function Dashboard() {
  const { user } = useRequireAuth();
  const [history, setHistory] = useState<any[]>([]);
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
        if (res.ok) {
          const data = await res.json();
          // reverse so the oldest is first for the trend line
          setHistory(data.items.reverse()); 
        }
      } catch (err) {
        console.error("Failed to load history", err);
      } finally {
        setIsLoading(false);
      }
    };
    if (user) fetchHistory();
  }, [user]);

  if (!user || isLoading) {
    return (
      <div className="flex bg-black text-white min-h-screen items-center justify-center">
        <p className="animate-pulse">Loading dashboard...</p>
      </div>
    );
  }

  // Calculate stats
  const totalInterviews = history.length;
  const avgScore = totalInterviews > 0 
    ? Math.round(history.reduce((acc, curr) => acc + (curr.score || 0), 0) / totalInterviews) 
    : 0;

  // Formatting data for Recharts
  const scoreTrendData = history.map((session, index) => ({
    name: `Int ${index + 1}`,
    score: session.score || 0,
  }));

  const topicCount: Record<string, number> = {};
  history.forEach(session => {
    const topic = session.type || "General";
    topicCount[topic] = (topicCount[topic] || 0) + 1;
  });
  const topicData = Object.entries(topicCount).map(([name, count]) => ({ name, count }));

  return (
    <div className="min-h-screen bg-black text-white p-8 md:p-12">
      <div className="max-w-6xl mx-auto space-y-8">
        
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 border-b border-gray-800 pb-6">
          <div>
            <h1 className="text-3xl font-bold">Dashboard</h1>
            <p className="text-gray-400 mt-1">Welcome back, {user.email}</p>
          </div>
          <div className="flex gap-4">
            <Link href="/history" className="px-4 py-2 border border-gray-700 hover:bg-gray-800 rounded font-medium transition-colors">
              View History
            </Link>
            <Link href="/interview" className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded font-medium transition-colors">
              New Interview
            </Link>
          </div>
        </div>

        {totalInterviews === 0 ? (
          <div className="text-center py-20 bg-gray-900 border border-gray-800 rounded-xl">
            <h2 className="text-xl font-semibold mb-2">No data yet</h2>
            <p className="text-gray-400 mb-6">Complete your first interview to see your analytics.</p>
            <Link href="/interview" className="px-6 py-3 bg-blue-600 hover:bg-blue-700 rounded font-medium transition-colors">
              Start an Interview
            </Link>
          </div>
        ) : (
          <>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {/* Stat Cards */}
              <div className="bg-gray-900 border border-gray-800 p-6 rounded-xl">
                <p className="text-sm text-gray-400 font-semibold uppercase">Total Interviews</p>
                <p className="text-4xl font-bold mt-2">{totalInterviews}</p>
              </div>
              <div className="bg-gray-900 border border-gray-800 p-6 rounded-xl">
                <p className="text-sm text-gray-400 font-semibold uppercase">Average Score</p>
                <p className={`text-4xl font-bold mt-2 ${avgScore >= 80 ? 'text-green-500' : avgScore >= 60 ? 'text-yellow-500' : 'text-red-500'}`}>
                  {avgScore}
                </p>
              </div>
              <div className="bg-gray-900 border border-gray-800 p-6 rounded-xl">
                <p className="text-sm text-gray-400 font-semibold uppercase">Highest Score</p>
                <p className="text-4xl font-bold mt-2 text-blue-500">
                  {Math.max(...history.map(s => s.score || 0))}
                </p>
              </div>
              <div className="bg-gray-900 border border-gray-800 p-6 rounded-xl">
                <p className="text-sm text-gray-400 font-semibold uppercase">Recent Topic</p>
                <p className="text-xl font-bold mt-2 text-purple-400 truncate">
                  {history[history.length - 1]?.type || "General"}
                </p>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Score Trend Chart */}
              <div className="bg-gray-900 border border-gray-800 p-6 rounded-xl h-96">
                <h2 className="text-lg font-semibold mb-6">Score Trend</h2>
                <ResponsiveContainer width="100%" height="85%">
                  <LineChart data={scoreTrendData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                    <XAxis dataKey="name" stroke="#9CA3AF" />
                    <YAxis stroke="#9CA3AF" domain={[0, 100]} />
                    <Tooltip 
                      contentStyle={{ backgroundColor: '#1F2937', border: 'none', borderRadius: '8px' }} 
                      itemStyle={{ color: '#60A5FA' }}
                    />
                    <Line 
                      type="monotone" 
                      dataKey="score" 
                      stroke="#3B82F6" 
                      strokeWidth={3}
                      dot={{ fill: '#3B82F6', r: 4 }}
                      activeDot={{ r: 6 }} 
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>

              {/* Topic Breakdown Chart */}
              <div className="bg-gray-900 border border-gray-800 p-6 rounded-xl h-96">
                <h2 className="text-lg font-semibold mb-6">Interviews by Topic</h2>
                <ResponsiveContainer width="100%" height="85%">
                  <BarChart data={topicData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                    <XAxis dataKey="name" stroke="#9CA3AF" />
                    <YAxis stroke="#9CA3AF" allowDecimals={false} />
                    <Tooltip 
                      contentStyle={{ backgroundColor: '#1F2937', border: 'none', borderRadius: '8px' }} 
                      itemStyle={{ color: '#A78BFA' }}
                    />
                    <Bar dataKey="count" fill="#8B5CF6" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}