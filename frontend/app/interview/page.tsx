"use client";

import { useRouter } from "next/navigation";

export default function InterviewPage() {
  const router = useRouter();

  return (
    <div className="flex flex-col items-center justify-center h-screen bg-black text-white gap-6">
      <h1 className="text-3xl font-bold">Choose Interview Type</h1>

      <button
        className="px-6 py-3 bg-blue-600 rounded"
        onClick={() => router.push("/interview/hr")}
      >
        HR Interview
      </button>

      <button
        className="px-6 py-3 bg-green-600 rounded"
        onClick={() => router.push("/interview/dsa")}
      >
        DSA Interview
      </button>
    </div>
  );
}