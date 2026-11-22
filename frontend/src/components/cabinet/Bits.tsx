"use client";

import type { ReactNode } from "react";

export function Panel({ title, action, children }: { title: string; action?: ReactNode; children: ReactNode }) {
  return (
    <section className="card p-5 sm:p-6">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-lg">{title}</h2>
        {action}
      </div>
      {children}
    </section>
  );
}

export function ErrorText({ text }: { text: string }) {
  return text ? (
    <p className="rounded-xl bg-clay-50 px-3 py-2 text-sm text-clay-700" role="alert">
      {text}
    </p>
  ) : null;
}

export function Loading() {
  return (
    <div className="flex items-center justify-center gap-2 py-8 text-sm text-ink-mute">
      <span className="h-4 w-4 animate-spin rounded-full border-2 border-forest-200 border-t-forest-600" aria-hidden />
      Yuklanmoqda…
    </div>
  );
}

export function Stat({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="card p-5">
      <div className="text-xs font-semibold text-ink-mute">{label}</div>
      <div className="mt-1.5 text-2xl font-extrabold text-ink">{value}</div>
    </div>
  );
}

/** Ro'yxatdagi string'larni (kiradi/kirmaydi) qator-qator tahrirlash */
export function LinesInput({ value, onChange, placeholder }: { value: string[]; onChange: (v: string[]) => void; placeholder?: string }) {
  return (
    <textarea
      className="input min-h-24"
      placeholder={placeholder ?? "Har birini yangi qatorga yozing"}
      value={value.join("\n")}
      onChange={(e) => onChange(e.target.value.split("\n").map((s) => s.trimStart()))}
      onBlur={() => onChange(value.map((s) => s.trim()).filter(Boolean))}
    />
  );
}

/**
 * Moderatsiya holati: saytga chiqadigan hamma narsa admin tasdig'idan keyin ko'rinadi.
 * `state`: "approved" | "pending" | "rejected" | "suspended". Qaytarilganda — admin izohi.
 */
export function ModerationBanner({ state, note, what = "Profil" }: { state: string; note?: string; what?: string }) {
  if (state === "rejected")
    return (
      <div className="rounded-xl border border-clay-100 bg-clay-50 p-4 text-sm text-clay-700">
        <b>↩️ {what} qaytarildi — tuzatish kerak.</b>
        {note && (
          <p className="mt-2 whitespace-pre-line rounded-lg bg-white/70 p-3 text-ink">
            <span className="text-xs font-semibold uppercase text-clay-700">Admin izohi</span>
            <br />
            {note}
          </p>
        )}
        <p className="mt-2 text-xs">Kamchiliklarni tuzatib saqlang — o&apos;zgarishlar qayta tekshiruvga yuboriladi.</p>
      </div>
    );
  if (state === "pending")
    return (
      <div className="rounded-xl border border-sun-200 bg-sun-50 p-4 text-sm text-ink">
        <b>⏳ Tekshiruvda.</b> Admin tasdiqlagach saytda ko&apos;rinadi. Natija haqida email va Telegram orqali xabar olasiz.
      </div>
    );
  if (state === "approved")
    return (
      <p className="text-xs text-ink-mute">
        ✅ Saytda ko&apos;rinmoqda. Diqqat: har qanday o&apos;zgarish (ma&apos;lumot, rasm, video, xona va h.k.) qayta
        tekshiruvga yuboriladi va admin tasdiqlaguncha saytda yashiriladi.
      </p>
    );
  return null;
}
