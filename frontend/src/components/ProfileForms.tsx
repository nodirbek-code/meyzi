"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { api, ClientApiError } from "@/lib/client";
import type { User } from "@/lib/types";

import { CodeInput, fullPhone, isComplete, PhoneDigitsInput } from "./PhoneField";

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

export function VerifyEmail() {
  const router = useRouter();
  const [sent, setSent] = useState(false);
  const [code, setCode] = useState("");
  const { busy, error, run } = useRun();
  return sent ? (
    <form className="flex flex-wrap gap-2" onSubmit={(e) => { e.preventDefault(); run(async () => { await api.post("/auth/email/verify", { code }); router.refresh(); }); }}>
      <input className="input w-40 text-center font-mono tracking-[0.4em]" maxLength={6} inputMode="numeric" placeholder="Kod" value={code} onChange={(e) => setCode(e.target.value.replace(/\D/g, ""))} />
      <button className="btn-primary" disabled={busy}>Tasdiqlash</button>
      {error && <p className="w-full text-sm text-clay-700">{error}</p>}
    </form>
  ) : (
    <div>
      <button className="btn-ghost" disabled={busy} onClick={() => run(async () => { await api.post("/auth/email/send-code"); setSent(true); })}>
        Tasdiqlash kodini yuborish
      </button>
      {error && <p className="mt-2 text-sm text-clay-700">{error}</p>}
    </div>
  );
}

export function AttachPhone({ current }: { current?: string | null }) {
  const router = useRouter();
  const [digits, setDigits] = useState("");
  const [code, setCode] = useState("");
  const [sent, setSent] = useState(false);
  const { busy, error, run } = useRun();
  const phone = fullPhone(digits);
  return (
    <form
      className="space-y-3"
      onSubmit={(e) => {
        e.preventDefault();
        run(async () => {
          if (!sent) {
            await api.post("/auth/me/phone/request-code", { phone });
            setSent(true);
          } else {
            await api.post("/auth/me/phone/verify", { phone, code });
            setSent(false);
            setDigits("");
            setCode("");
            router.refresh();
          }
        });
      }}
    >
      <span className="label">{current ? "Raqamni almashtirish" : "Telefon ulash"}</span>
      <div className="flex flex-wrap gap-2">
        <div className="w-full sm:w-64">
          <PhoneDigitsInput digits={digits} onChange={(d) => { setDigits(d); setSent(false); }} disabled={sent} required />
        </div>
        {sent && (
          <div className="w-40">
            <CodeInput value={code} onChange={setCode} autoFocus />
          </div>
        )}
        <button className="btn-primary" disabled={busy || !isComplete(digits) || (sent && code.length !== 6)}>
          {sent ? "Tasdiqlash" : "Telegram'ga kod yuborish"}
        </button>
      </div>
      {sent && <p className="text-xs text-sky-700">Kod Telegram&apos;ga yuborildi — Telegram ilovangizni oching.</p>}
      {error && <p className="text-sm text-clay-700">{error}</p>}
    </form>
  );
}
