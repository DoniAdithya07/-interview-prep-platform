export default function QuestionCard({ question }: { question: string }) {
  return (
    <div className="p-6 border rounded-lg">
      <h2 className="text-xl font-semibold">Question</h2>
      <p className="mt-2">{question}</p>
    </div>
  );
}