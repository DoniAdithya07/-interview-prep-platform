"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

import { useAuth } from "@/context/AuthContext";

export default function LoginPage() {
  const router = useRouter();
  const { loginWithEmail, loginWithGoogle } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const toErrorMessage = (value: unknown, fallback: string) =>
    value instanceof Error ? value.message : fallback;

  const onSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError("");
    setLoading(true);
    try {
      await loginWithEmail(email, password);
      router.push("/");
    } catch (e: unknown) {
      setError(toErrorMessage(e, "Login failed"));
    } finally {
      setLoading(false);
    }
  };

  const onGoogle = async () => {
    setError("");
    setLoading(true);
    try {
      await loginWithGoogle();
      router.push("/");
    } catch (e: unknown) {
      setError(toErrorMessage(e, "Google login failed"));
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="mx-auto mt-16 max-w-md rounded-xl border p-6">
      <h1 className="mb-5 text-2xl font-semibold">Login</h1>
      <form onSubmit={onSubmit} className="grid gap-3">
        <input
          className="rounded border px-3 py-2"
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
        <input
          className="rounded border px-3 py-2"
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
        <button className="rounded bg-black px-4 py-2 text-white" disabled={loading}>
          {loading ? "Please wait..." : "Login with Email"}
        </button>
      </form>
      <button
        className="mt-3 w-full rounded border px-4 py-2"
        onClick={onGoogle}
        disabled={loading}
      >
        Login with Google
      </button>
      {error ? <p className="mt-3 text-sm text-red-600">{error}</p> : null}
      <p className="mt-4 text-sm">
        No account? <Link className="underline" href="/auth/register">Register</Link>
      </p>
    </main>
  );
}
