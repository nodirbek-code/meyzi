"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { api, ClientApiError } from "@/lib/client";

/** Admin kirishi: Django admin email + paroli (faqat adminlar kira oladi). */
export function ControlLogin() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await api.auth("control-login", { email, password });
      router.replace("/control");
      router.refresh();
    } catch (err) {
      setError(err instanceof ClientApiError ? err.message : "Xatolik yuz berdi");
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={submit} className="card w-full max-w-sm space-y-4 p-6 sm:p-8">
      <div>
        <p className="eyebrow">Boshqaruv</p>
        <h1 className="mt-1 text-2xl">Admin paneliga kirish</h1>
        <p className="mt-1 text-sm text-ink-soft">Admin email va parolingizni kiriting.</p>
      </div>
      <label className="block">
        <span className="label">Email</span>
        <input className="input" type="email" autoComplete="username" required value={email} onChange={(e) => setEmail(e.target.value)} />
      </label>
      <label className="block">
        <span className="label">Parol</span>
        <input className="input" type="password" autoComplete="current-password" required value={password} onChange={(e) => setPassword(e.target.value)} />
      </label>
      {error && <p className="rounded-xl bg-clay-50 px-3 py-2 text-sm text-clay-700">{error}</p>}
      <button className="btn-primary w-full py-3" disabled={busy}>{busy ? "Kirilmoqda…" : "Kirish"}</button>
    </form>
  );
}
