"use client";

import Link from "next/link";
import { useState } from "react";

import { api, ClientApiError } from "@/lib/client";

import { FormError } from "./AuthCard";

export function ForgotPasswordForm() {
  const [step, setStep] = useState<"email" | "reset" | "done">("email");
  const [email, setEmail] = useState("");
  const [code, setCode] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function run(fn: () => Promise<void>) {
    setBusy(true);
    setError("");
    try {
      await fn();
    } catch (e) {
      setError(e instanceof ClientApiError ? e.message : "Xatolik yuz berdi");
    } finally {
      setBusy(false);
    }
  }

  if (step === "done") {
    return (
      <div className="space-y-4 text-center">
        <p className="text-sm text-ink-soft">Parol yangilandi. Xavfsizlik uchun barcha qurilmalardan chiqarildingiz.</p>
        <Link href="/login" className="btn-primary">Kirish</Link>
      </div>
    );
  }

  return step === "email" ? (
    <form className="space-y-4" onSubmit={(e) => { e.preventDefault(); run(async () => { await api.post("/auth/password/forgot", { email }); setStep("reset"); }); }}>
      <label className="block">
        <span className="label">Email</span>
        <input className="input" type="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
      </label>
      <FormError message={error} />
      <button className="btn-primary w-full py-3" disabled={busy}>Kod yuborish</button>
    </form>
  ) : (
    <form className="space-y-4" onSubmit={(e) => { e.preventDefault(); run(async () => { await api.post("/auth/password/reset", { email, code, new_password: password }); setStep("done"); }); }}>
      <p className="text-sm text-ink-soft">Agar <b>{email}</b> ro&apos;yxatdan o&apos;tgan bo&apos;lsa, unga 6 raqamli kod yuborildi.</p>
      <label className="block">
        <span className="label">Kod</span>
        <input className="input text-center font-mono text-lg tracking-[0.5em]" inputMode="numeric" maxLength={6} required value={code} onChange={(e) => setCode(e.target.value.replace(/\D/g, ""))} />
      </label>
      <label className="block">
        <span className="label">Yangi parol</span>
        <input className="input" type="password" autoComplete="new-password" required value={password} onChange={(e) => setPassword(e.target.value)} />
      </label>
      <FormError message={error} />
      <button className="btn-primary w-full py-3" disabled={busy}>Parolni yangilash</button>
    </form>
  );
}
