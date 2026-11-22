"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useCallback, useState } from "react";

import { api, ClientApiError } from "@/lib/client";

import { Divider, FormError, TermsNote } from "./AuthCard";
import { GoogleButton } from "./GoogleButton";
import { fullPhone, isComplete, PhoneDigitsInput } from "./PhoneField";
import { botUrl, TelegramButton, useTelegramLogin } from "./TelegramButton";

function safeNext(next: string | null) {
  // faqat sayt ichidagi yo'llar (ochiq redirect'ning oldini olish)
  return next && next.startsWith("/") && !next.startsWith("//") ? next : "/account";
}

/**
 * Ro'yxatdan o'tish — 2 usul: Telegram bot (telefon, ism-familiya, parol) yoki Google.
 * Kirish — 2 usul: Google yoki telefon raqam + parol.
 */
export function LoginForm({ mode = "login" }: { mode?: "login" | "register" }) {
  const router = useRouter();
  const next = safeNext(useSearchParams().get("next"));
  const register = mode === "register";

  const done = useCallback(() => {
    router.push(register ? "/account/profile?welcome=1" : next);
    router.refresh();
  }, [router, next, register]);

  if (register) {
    return (
      <div className="space-y-5">
        <TelegramButton label="Telegram orqali ro'yxatdan o'tish" />
        <Divider />
        <GoogleButton onDone={done} label="signup_with" />
        <TermsNote />
      </div>
    );
  }

  return (
    <div className="space-y-5">
      <GoogleButton onDone={done} label="signin_with" />
      <Divider />
      <PhonePasswordForm onDone={done} />
      <TermsNote />
    </div>
  );
}

function PhonePasswordForm({ onDone }: { onDone: () => void }) {
  const telegram = useTelegramLogin();
  const resetUrl = botUrl(telegram, "parol");
  const [digits, setDigits] = useState("");
  const [password, setPassword] = useState("");
  const [show, setShow] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await api.auth("phone-login", { phone: fullPhone(digits), password });
      onDone();
    } catch (err) {
      setError(err instanceof ClientApiError ? err.message : "Xatolik yuz berdi");
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className="space-y-4" onSubmit={submit}>
      <label className="block">
        <span className="label">Telefon raqam</span>
        <PhoneDigitsInput digits={digits} onChange={setDigits} required />
      </label>
      <label className="block">
        <span className="flex items-center justify-between">
          <span className="label">Parol</span>
          {resetUrl && (
            <a
              href={resetUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="mb-1.5 text-xs font-semibold text-forest-600 hover:underline"
              title="Telegram botda yangi parol o'rnatasiz"
            >
              Parolni unutdingizmi?
            </a>
          )}
        </span>
        <div className="relative">
          <input
            className="input pr-20"
            type={show ? "text" : "password"}
            autoComplete="current-password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          <button
            type="button"
            onClick={() => setShow((v) => !v)}
            className="absolute inset-y-0 right-3 text-xs font-semibold text-ink-soft hover:text-ink"
            aria-label={show ? "Parolni yashirish" : "Parolni ko'rsatish"}
          >
            {show ? "Yashirish" : "Ko'rsatish"}
          </button>
        </div>
      </label>
      <FormError message={error} />
      <button className="btn-primary w-full py-3" disabled={busy || !isComplete(digits) || !password}>
        {busy ? "Kirilmoqda…" : "Kirish"}
      </button>
    </form>
  );
}
