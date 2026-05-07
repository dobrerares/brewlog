import { type FormEvent, useState } from "react";
import { useNavigate } from "react-router";

import { useAuth } from "@/hooks/useAuth";

export default function Login() {
  const { login } = useAuth();
  const nav = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await login(email, password);
      nav("/dashboard");
    } catch {
      setError("Invalid credentials");
    }
  }

  return (
    <form onSubmit={submit} className="mx-auto mt-12 max-w-sm space-y-3">
      <h1 className="text-2xl font-semibold">Log in</h1>
      <input className="w-full rounded border p-2" type="email" placeholder="email"
             value={email} onChange={(e) => setEmail(e.target.value)} required />
      <input className="w-full rounded border p-2" type="password" placeholder="password"
             value={password} onChange={(e) => setPassword(e.target.value)} required />
      <button className="w-full rounded bg-amber-700 p-2 text-white" type="submit">Log in</button>
      {error && <p className="text-sm text-red-600">{error}</p>}
      <p className="text-sm">No account? <a href="/register" className="underline">Register</a></p>
    </form>
  );
}
