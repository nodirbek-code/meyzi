"use client";

import { useState } from "react";

import { api, ClientApiError } from "@/lib/client";

/** O'zbekiston kodi — maydon boshida qotirilgan, foydalanuvchi faqat qolgan 9 raqamni yozadi. */
export const PHONE_PREFIX = "+998";

/** "+998 90 123 45 67" / "901234567" → "901234567" (ko'pi bilan 9 raqam) */
export function phoneDigits(phone: string | null | undefined): string {
  const d = (phone ?? "").replace(/\D/g, "");
  return (d.length > 9 && d.startsWith("998") ? d.slice(3) : d).slice(0, 9);
}

/** "901234567" → "90 123 45 67" */
export function formatDigits(d: string): string {
  return [d.slice(0, 2), d.slice(2, 5), d.slice(5, 7), d.slice(7, 9)].filter(Boolean).join(" ");
}

export const fullPhone = (digits: string) => (digits ? PHONE_PREFIX + digits : "");
export const isComplete = (digits: string) => /^\d{9}$/.test(digits);

/** +998 qotirilgan telefon maydoni (faqat raqam, 9 ta). */
export function PhoneDigitsInput({
  digits,
  onChange,
  disabled,
  required,
  autoFocus,
}: {
  digits: string;
  onChange: (digits: string) => void;
  disabled?: boolean;
  required?: boolean;
  autoFocus?: boolean;
}) {
  return (
    <div className="flex">
      <span className="flex select-none items-center rounded-l-xl border border-r-0 border-sand-300 bg-sand-100 px-3 text-sm font-semibold text-ink-soft">
        {PHONE_PREFIX}
      </span>
      <input
        className="input rounded-l-none"
        type="tel"
        inputMode="numeric"
        autoComplete="tel-national"
        placeholder="90 123 45 67"
        maxLength={12}
        pattern="\d{2} \d{3} \d{2} \d{2}"
        title="+998 dan keyin 9 ta raqam, masalan: 90 123 45 67"
        required={required}
        disabled={disabled}
        autoFocus={autoFocus}
        value={formatDigits(digits)}
        onChange={(e) => onChange(e.target.value.replace(/\D/g, "").slice(0, 9))}
      />
    </div>
  );
}

/** 6 xonali kod maydoni */
export function CodeInput({ value, onChange, autoFocus }: { value: string; onChange: (v: string) => void; autoFocus?: boolean }) {
  return (
    <input
      className="input text-center font-mono text-lg tracking-[0.5em]"
      inputMode="numeric"
      autoComplete="one-time-code"
      maxLength={6}
      placeholder="••••••"
      autoFocus={autoFocus}
      value={value}
      onChange={(e) => onChange(e.target.value.replace(/\D/g, ""))}
    />
  );
}

export type VerifiedPhone = { phone: string; token: string };

/**
 * Telefon + Telegram kod bilan tasdiqlash. Raqam faqat kod to'g'ri kiritilgandan keyin "tasdiqlangan" bo'ladi
 * (`value.token` to'ladi) — formani shu token bilan yuboring.
 * `trustedPhone` — akkauntdagi tasdiqlangan yoki saqlangan (o'zgarmagan) raqam: unga kod so'ralmaydi.
 */
export function VerifiedPhoneField({
  value,
  onChange,
  trustedPhone,
  label = "Telefon raqami",
  required = true,
}: {
  value: VerifiedPhone;
  onChange: (v: VerifiedPhone) => void;
  trustedPhone?: string | null;
  label?: string;
  required?: boolean;
}) {
  const digits = phoneDigits(value.phone);
  const [sent, setSent] = useState(false);
  const [code, setCode] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const verified = !!digits && ((!!trustedPhone && fullPhone(digits) === trustedPhone) || !!value.token);

  function change(d: string) {
    setSent(false);
    setCode("");
    setError("");
    onChange({ phone: fullPhone(d), token: "" });
  }

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

  const sendCode = () =>
    run(async () => {
      await api.post("/auth/phone-check/send-code", { phone: fullPhone(digits) });
      setSent(true);
    });

  const confirm = () =>
    run(async () => {
      const r = await api.post<{ phone: string; phone_token: string }>("/auth/phone-check/verify", {
        phone: fullPhone(digits),
        code,
      });
      setSent(false);
      setCode("");
      onChange({ phone: r.phone, token: r.phone_token });
    });

  return (
    <div className="space-y-2">
      <span className="label">
        {label}
        {required && <span className="text-clay-500"> *</span>}
      </span>
      <div className="flex gap-2">
        <div className="min-w-0 flex-1">
          <PhoneDigitsInput digits={digits} onChange={change} required={required} disabled={busy} />
        </div>
        {verified ? (
          <span className="chip shrink-0 self-center bg-forest-50 text-forest-700">✓ Tasdiqlangan</span>
        ) : (
          isComplete(digits) &&
          !sent && (
            <button type="button" className="btn shrink-0 bg-sky-500 px-3 text-xs text-white hover:bg-sky-700" disabled={busy} onClick={sendCode}>
              {busy ? "…" : "Kod olish"}
            </button>
          )
        )}
      </div>
      {sent && !verified && (
        <div className="space-y-2 rounded-xl bg-sky-50 p-3">
          <p className="text-xs text-sky-700">
            Tasdiqlash kodi <b>Telegram</b>&apos;ga yuborildi — Telegram ilovangizni oching.
          </p>
          <div className="flex gap-2">
            <CodeInput value={code} onChange={setCode} autoFocus />
            <button type="button" className="btn-primary shrink-0 px-4" disabled={busy || code.length !== 6} onClick={confirm}>
              Tasdiqlash
            </button>
          </div>
          <button type="button" className="text-xs font-semibold text-sky-700 hover:underline" disabled={busy} onClick={sendCode}>
            Kodni qayta yuborish
          </button>
        </div>
      )}
      {!verified && isComplete(digits) && !sent && !error && (
        <p className="text-xs text-ink-mute">Raqam Telegram&apos;ga keladigan kod bilan tasdiqlanadi.</p>
      )}
      {error && <p className="text-xs text-clay-700">{error}</p>}
    </div>
  );
}

/** Forma tayyorligi: raqam to'liq va tasdiqlangan (yoki ishonchli) */
export function phoneReady(v: VerifiedPhone, trustedPhone?: string | null) {
  return isComplete(phoneDigits(v.phone)) && (!!v.token || (!!trustedPhone && v.phone === trustedPhone));
}

export { accountPhone } from "@/lib/phone";
