"use client";

import { useState } from "react";

export default function AnswerBox() {
  const [answer, setAnswer] = useState("");

  const handleSubmit = () => {
    console.log("User answer:", answer);
    alert("Answer submitted! (Next step: send to AI)");
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
        className="mt-3 px-4 py-2 bg-blue-600 text-white rounded"
        onClick={handleSubmit}
      >
        Submit Answer
      </button>
    </div>
  );
}