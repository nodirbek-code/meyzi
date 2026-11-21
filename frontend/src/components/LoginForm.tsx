"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { api, ClientApiError } from "@/lib/client";

import { Divider, FormError, TermsNote } from "./AuthCard";
import { GoogleButton } from "./GoogleButton";
import { CodeInput, formatDigits, fullPhone, isComplete, PhoneDigitsInput } from "./PhoneField";

function safeNext(next: string | null) {
  // faqat sayt ichidagi yo'llar (ochiq redirect'ning oldini olish)
  return next && next.startsWith("/") && !next.startsWith("//") ? next : "/account";
}

const RESEND = 60;

export function LoginForm() {
  const router = useRouter();
  const next = safeNext(useSearchParams().get("next"));
  const [mode, setMode] = useState<"phone" | "email">("phone");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  // email
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  // telefon
  const [digits, setDigits] = useState("");
  const [code, setCode] = useState("");
  const [codeSent, setCodeSent] = useState(false);
  const [wait, setWait] = useState(0);

  useEffect(() => {
    if (wait <= 0) return;
    const t = setTimeout(() => setWait((w) => w - 1), 1000);
    return () => clearTimeout(t);
  }, [wait]);

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

  const done = useCallback(() => {
    router.push(next);
    router.refresh();
  }, [router, next]);

  const sendCode = () =>
    run(async () => {
      await api.post("/auth/phone/request-code", { phone: fullPhone(digits) });
      setCodeSent(true);
      setCode("");
      setWait(RESEND);
    });

  return (
    <div className="space-y-5">
      <GoogleButton onDone={done} />
      <Divider />

      <div className="grid grid-cols-2 rounded-xl bg-sand-100 p-1 text-sm font-semibold">
        {(["phone", "email"] as const).map((m) => (
          <button
            key={m}
            type="button"
            onClick={() => {
              setMode(m);
              setError("");
            }}
            className={`rounded-lg py-2 transition ${mode === m ? "bg-white text-forest-700 shadow-card" : "text-ink-soft"}`}
          >
            {m === "phone" ? "Telefon (Telegram)" : "Email"}
          </button>
        ))}
      </div>

      {mode === "email" ? (
        <form
          className="space-y-4"
          onSubmit={(e) => {
            e.preventDefault();
            run(async () => {
              await api.auth("login", { email, password });
              done();
            });
          }}
        >
          <label className="block">
            <span className="label">Email</span>
            <input className="input" type="email" autoComplete="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
          </label>
          <label className="block">
            <span className="flex items-center justify-between">
              <span className="label">Parol</span>
              <Link href="/forgot-password" className="mb-1.5 text-xs font-semibold text-forest-600 hover:underline">
                Parolni unutdingizmi?
              </Link>
            </span>
            <input className="input" type="password" autoComplete="current-password" required value={password} onChange={(e) => setPassword(e.target.value)} />
          </label>
          <FormError message={error} />
          <button className="btn-primary w-full py-3" disabled={busy}>
            {busy ? "Kirilmoqda…" : "Kirish"}
          </button>
        </form>
      ) : (
        <form
          className="space-y-4"
          onSubmit={(e) => {
            e.preventDefault();
            if (!codeSent) return sendCode();
            run(async () => {
              await api.auth("phone", { phone: fullPhone(digits), code });
              done();
            });
          }}
        >
          {!codeSent ? (
            <>
              <label className="block">
                <span className="label">Telefon raqam</span>
                <PhoneDigitsInput digits={digits} onChange={setDigits} required />
              </label>
              <p className="flex items-start gap-2 rounded-xl bg-sky-50 px-3 py-2.5 text-xs text-sky-700">
                <span aria-hidden>✈</span>
                <span>
                  Tasdiqlash kodi shu raqamga ulangan <b>Telegram</b> akkauntingizga keladi. Akkaunt bo&apos;lmasa — avtomatik
                  yaratiladi.
                </span>
              </p>
            </>
          ) : (
            <div className="space-y-3">
              <p className="text-sm text-ink-soft">
                Kod <b className="text-ink">+998 {formatDigits(digits)}</b> raqamining Telegram&apos;iga yuborildi.{" "}
                <button
                  type="button"
                  className="font-semibold text-forest-600 hover:underline"
                  onClick={() => {
                    setCodeSent(false);
                    setCode("");
                    setError("");
                  }}
                >
                  Raqamni o&apos;zgartirish
                </button>
              </p>
              <CodeInput value={code} onChange={setCode} autoFocus />
              <p className="text-center text-xs text-ink-mute">
                {wait > 0 ? (
                  <>Kodni qayta yuborish: {wait} s</>
                ) : (
                  <button type="button" className="font-semibold text-forest-600 hover:underline" onClick={sendCode} disabled={busy}>
                    Kodni qayta yuborish
                  </button>
                )}
              </p>
            </div>
          )}
          <FormError message={error} />
          <button className="btn-primary w-full py-3" disabled={busy || (!codeSent ? !isComplete(digits) : code.length !== 6)}>
            {busy ? "Kuting…" : codeSent ? "Kirish" : "Telegram'ga kod yuborish"}
          </button>
        </form>
      )}
      <TermsNote />
    </div>
  );
}
