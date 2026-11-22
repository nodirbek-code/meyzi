"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { api, ClientApiError } from "@/lib/client";
import type { User } from "@/lib/types";

function useRun() {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [ok, setOk] = useState("");
  async function run(fn: () => Promise<string | void>) {
    setBusy(true);
    setError("");
    setOk("");
    try {
      const msg = await fn();
      if (msg) setOk(msg);
    } catch (e) {
      setError(e instanceof ClientApiError ? e.message : "Xatolik");
    } finally {
      setBusy(false);
    }
  }
  return { busy, error, ok, run };
}

export function ProfileForm({ user }: { user: User }) {
  const router = useRouter();
  const [f, setF] = useState({ first_name: user.first_name, last_name: user.last_name });
  const { busy, error, ok, run } = useRun();
  return (
    <form className="space-y-4" onSubmit={(e) => { e.preventDefault(); run(async () => { await api.patch("/auth/me", f); router.refresh(); return "Saqlandi"; }); }}>
      <div className="grid gap-3 sm:grid-cols-2">
        <label><span className="label">Ism</span><input className="input" value={f.first_name} onChange={(e) => setF({ ...f, first_name: e.target.value })} /></label>
        <label><span className="label">Familiya</span><input className="input" value={f.last_name} onChange={(e) => setF({ ...f, last_name: e.target.value })} /></label>
      </div>
      {error && <p className="text-sm text-clay-700">{error}</p>}
      {ok && <p className="text-sm text-forest-700">{ok}</p>}
      <button className="btn-primary" disabled={busy}>Saqlash</button>
    </form>
  );
}

/** Profilga email ulash: email → 6 xonali kod emailga → kod to'g'ri bo'lsa email tasdiqlangan holda yoziladi. */
export function AttachEmail({ current }: { current?: string | null }) {
  const router = useRouter();
  const [email, setEmail] = useState(current ?? "");
  const [code, setCode] = useState("");
  const [sent, setSent] = useState(false);
  const { busy, error, ok, run } = useRun();

  const sendCode = () =>
    run(async () => {
      await api.post("/auth/me/email/request-code", { email });
      setSent(true);
      setCode("");
      return "Kod emailingizga yuborildi. Pochtangizni (va «Spam» papkasini) tekshiring.";
    });

  return (
    <form
      className="space-y-3"
      onSubmit={(e) => {
        e.preventDefault();
        if (!sent) return sendCode();
        run(async () => {
          await api.post("/auth/me/email/verify", { email, code });
          setSent(false);
          router.refresh();
          return "Email ulandi";
        });
      }}
    >
      <span className="label">{current ? "Emailni tasdiqlash" : "Email qo'shish"}</span>
      <div className="flex flex-wrap gap-2">
        <input
          className="input w-full sm:w-72"
          type="email"
          autoComplete="email"
          placeholder="siz@email.com"
          required
          value={email}
          disabled={sent}
          onChange={(e) => setEmail(e.target.value)}
        />
        {sent && (
          <input
            className="input w-40 text-center font-mono tracking-[0.4em]"
            maxLength={6}
            inputMode="numeric"
            autoComplete="one-time-code"
            placeholder="Kod"
            autoFocus
            value={code}
            onChange={(e) => setCode(e.target.value.replace(/\D/g, ""))}
          />
        )}
        <button className="btn-primary" disabled={busy || !email || (sent && code.length !== 6)}>
          {busy ? "Kuting…" : sent ? "Tasdiqlash" : "Kod yuborish"}
        </button>
      </div>
      {sent && (
        <p className="text-xs text-ink-soft">
          <button type="button" className="font-semibold text-forest-600 hover:underline" onClick={() => { setSent(false); setCode(""); }}>
            Emailni o&apos;zgartirish
          </button>
          {" · "}
          <button type="button" className="font-semibold text-forest-600 hover:underline" disabled={busy} onClick={sendCode}>
            Kodni qayta yuborish
          </button>
        </p>
      )}
      {error && <p className="text-sm text-clay-700">{error}</p>}
      {ok && <p className="text-sm text-forest-700">{ok}</p>}
    </form>
  );
}
