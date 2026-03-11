"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

import { useAuth } from "@/context/AuthContext";

export default function RegisterPage() {
  const router = useRouter();
  const { registerWithEmail, loginWithGoogle } = useAuth();
  const [name, setName] = useState("");
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
      await registerWithEmail(name, email, password);
      router.push("/");
    } catch (e: unknown) {
      setError(toErrorMessage(e, "Registration failed"));
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
      setError(toErrorMessage(e, "Google sign-up failed"));
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="mx-auto mt-16 max-w-md rounded-xl border p-6">
      <h1 className="mb-5 text-2xl font-semibold">Create Account</h1>
      <form onSubmit={onSubmit} className="grid gap-3">
        <input
          className="rounded border px-3 py-2"
          type="text"
          placeholder="Name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
        />
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
          {loading ? "Please wait..." : "Sign up with Email"}
        </button>
      </form>
      <button
        className="mt-3 w-full rounded border px-4 py-2"
        onClick={onGoogle}
        disabled={loading}
      >
        Sign up with Google
      </button>
      {error ? <p className="mt-3 text-sm text-red-600">{error}</p> : null}
      <p className="mt-4 text-sm">
        Already have an account? <Link className="underline" href="/auth/login">Login</Link>
      </p>
    </main>
  );
}
