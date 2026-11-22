"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useRef, useState } from "react";

import { api } from "@/lib/client";

import { TelegramPhoneButton } from "./TelegramPhoneLink";

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

export type VerifiedPhone = { phone: string; token: string };

/** Akkauntdagi tasdiqlangan raqamdan olingan qiymat belgisi (backend akkaunt raqamini o'zi tekshiradi). */
const FROM_ACCOUNT = "account";

type Me = { phone: string | null; phone_verified: boolean };

/**
 * Formadagi telefon — faqat akkauntdagi (Telegram bot orqali tasdiqlangan) raqam. Kod so'ralmaydi.
 * - Akkauntda tasdiqlangan raqam bo'lsa — avtomatik qo'yiladi, o'zgartirib bo'lmaydi.
 * - Bo'lmasa — "Telefon raqam qo'shish" botga olib boradi; bot raqamni akkauntga yozgach, maydon o'zi to'ladi.
 * - Kirmagan foydalanuvchiga — "Kirish" havolasi.
 * `trustedPhone` — oldin saqlangan raqam (masalan kabinetdagi mehmonxona raqami): u ham tasdiqlangan hisoblanadi.
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
  const pathname = usePathname();
  const [me, setMe] = useState<Me | null | undefined>(undefined); // undefined — yuklanmoqda, null — kirmagan
  const change = useRef(onChange);
  change.current = onChange;

  useEffect(() => {
    api
      .get<Me>("/auth/me")
      .then(setMe)
      .catch(() => setMe(null));
  }, []);

  const acct = me?.phone && me.phone_verified ? me.phone : null;
  const isTrusted = !!trustedPhone && value.phone === trustedPhone;

  // Akkaunt raqami avtomatik qo'yiladi (oldin saqlangan ishonchli raqam bo'lsa — o'sha qoladi)
  useEffect(() => {
    if (!acct || isTrusted) return;
    if (value.phone !== acct || !value.token) change.current({ phone: acct, token: FROM_ACCOUNT });
  }, [acct, isTrusted, value.phone, value.token]);

  const shown = isTrusted || (!!acct && value.phone === acct) ? value.phone : "";

  return (
    <div className="space-y-2">
      <span className="label">
        {label}
        {required && <span className="text-clay-500"> *</span>}
      </span>
      {me === undefined ? (
        <div className="input animate-pulse text-ink-mute">Yuklanmoqda…</div>
      ) : shown ? (
        <>
          <div className="flex items-center gap-2">
            <div className="input flex-1 select-all bg-sand-50 font-semibold text-ink" aria-readonly>
              {PHONE_PREFIX} {formatDigits(phoneDigits(shown))}
            </div>
            <span className="chip shrink-0 bg-forest-50 text-forest-700">✓ Tasdiqlangan</span>
          </div>
          {acct && shown !== acct ? (
            <button type="button" className="text-xs font-semibold text-sky-700 hover:underline" onClick={() => onChange({ phone: acct, token: FROM_ACCOUNT })}>
              Akkauntimdagi raqamni qo&apos;yish ({acct})
            </button>
          ) : (
            <p className="text-xs text-ink-mute">Akkauntingizdagi tasdiqlangan raqam. Raqamni almashtirish uchun qo&apos;llab-quvvatlashga yozing.</p>
          )}
        </>
      ) : me ? (
        <div className="space-y-2 rounded-xl bg-sky-50 p-3">
          <p className="text-xs text-sky-700">
            Akkauntingizda tasdiqlangan telefon raqam yo&apos;q. Telegram bot orqali qo&apos;shing — raqam shu yerga o&apos;zi
            tushadi.
          </p>
          <TelegramPhoneButton
            onLinked={(phone) => {
              setMe({ phone, phone_verified: true });
              change.current({ phone, token: FROM_ACCOUNT });
            }}
          />
        </div>
      ) : (
        <div className="rounded-xl bg-sky-50 p-3 text-xs text-sky-700">
          Telefon raqam akkauntingizdan olinadi.{" "}
          <Link href={`/login?next=${encodeURIComponent(pathname || "/")}`} className="font-semibold underline">
            Tizimga kiring
          </Link>{" "}
          yoki Telegram orqali ro&apos;yxatdan o&apos;ting.
        </div>
      )}
    </div>
  );
}

/** Forma tayyorligi: raqam to'liq va tasdiqlangan (yoki ishonchli) */
export function phoneReady(v: VerifiedPhone, trustedPhone?: string | null) {
  return isComplete(phoneDigits(v.phone)) && (!!v.token || (!!trustedPhone && v.phone === trustedPhone));
}

export { accountPhone } from "@/lib/phone";
