"use client";

import QuestionCard from "@/components/QuestionCard";
import AnswerBox from "@/components/AnswerBox";

export default function InterviewTypePage() {
  const question = "Explain the QuickSort algorithm.";

  return (
    <div className="flex flex-col items-center justify-center h-screen bg-black text-white p-10 gap-6">
      <QuestionCard question={question} />

      <AnswerBox />
    </div>
  );
}