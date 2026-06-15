"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { setToken } from "@/components/admin-auth";
import { Button } from "@/components/ui/button";
import { adminLogin, UnauthorizedError } from "@/lib/api";

export default function AdminLoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const token = await adminLogin(username, password);
      setToken(token);
      router.push("/admin");
    } catch (err) {
      setError(
        err instanceof UnauthorizedError ? "Invalid username or password" : "Login failed",
      );
      setBusy(false);
    }
  }

  const field = "w-full border border-zinc-300 px-3 py-2 text-sm";

  return (
    <main className="flex min-h-screen items-center justify-center bg-[#FAFAF8] px-6 text-[#1A1A1A]">
      <form onSubmit={handleSubmit} className="w-full max-w-sm space-y-5">
        <h1 className="text-3xl font-bold tracking-tight">Admin</h1>
        <div>
          <label className="mb-1 block text-sm font-medium">Username</label>
          <input className={field} value={username} onChange={(e) => setUsername(e.target.value)} required />
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium">Password</label>
          <input
            type="password"
            className={field}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>
        {error && <p className="text-sm text-red-600">{error}</p>}
        <Button type="submit" disabled={busy} className="w-full bg-lime-400 text-[#1A1A1A] hover:bg-lime-500">
          {busy ? "Signing in…" : "Sign in"}
        </Button>
      </form>
    </main>
  );
}
