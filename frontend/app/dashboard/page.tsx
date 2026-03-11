"use client";

import useRequireAuth from "@/hooks/useRequireAuth";

export default function Dashboard() {
  const { user } = useRequireAuth();

  if (!user) return null;

  return (
    <div className="p-10">
      <h1 className="text-3xl font-bold">Dashboard</h1>
      <p>Welcome {user.email}</p>
    </div>
  );
}npm run dev