"use client";

import { useAuth } from "@/context/AuthContext";
import { signOut } from "firebase/auth";
import { auth } from "@/lib/firebase";
import { useRouter } from "next/navigation";

export default function Home() {
  const { user } = useAuth();
  const router = useRouter();

  const logout = async () => {
    await signOut(auth);
  };

  return (
    <div className="flex items-center justify-center h-screen bg-black text-white">
      <div className="p-8 border rounded-xl text-center space-y-4">
        <h1 className="text-3xl font-bold">Interview Prep Platform</h1>

        {user ? (
          <>
            <p>Logged in as: {user.email}</p>

            <button
              className="px-4 py-2 bg-blue-600 rounded"
              onClick={() => router.push("/interview")}
            >
              Start Interview
            </button>

            <button
              className="px-4 py-2 bg-green-600 rounded"
              onClick={() => router.push("/dashboard")}
            >
              Dashboard
            </button>

            <button
              className="px-4 py-2 bg-red-500 rounded"
              onClick={logout}
            >
              Logout
            </button>
          </>
        ) : (
          <button
            className="px-4 py-2 bg-blue-600 rounded"
            onClick={() => router.push("/auth/login")}
          >
            Login
          </button>
        )}
      </div>
    </div>
  );
}