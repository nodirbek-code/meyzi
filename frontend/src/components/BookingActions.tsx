"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { api, ClientApiError } from "@/lib/client";
import { money } from "@/lib/format";
import type { Installment, PaymentMethod } from "@/lib/types";

function useLeft(until: string) {
  const [left, setLeft] = useState(() => new Date(until).getTime() - Date.now());
  const router = useRouter();
  useEffect(() => {
    const t = setInterval(() => {
      const l = new Date(until).getTime() - Date.now();
      setLeft(l);
      if (l <= 0) {
        clearInterval(t);
        router.refresh();
      }
    }, 1000);
    return () => clearInterval(t);
  }, [until, router]);
  return left;
}

function mmss(ms: number) {
  const m = Math.floor(ms / 60000);
  const s = Math.floor((ms % 60000) / 1000);
  return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}

/** To'lov muddatigacha qolgan vaqt (kichik, matn ichida) */
export function Countdown({ until }: { until: string }) {
  const left = useLeft(until);
  if (left <= 0) return <span>muddat tugadi</span>;
  return <span className="font-mono font-bold">{mmss(left)}</span>;
}

/** To'lov muddati bloki — katta taymer bilan */
export function PaymentDeadline({ until }: { until: string }) {
  const left = useLeft(until);
  const urgent = left < 5 * 60_000;
  return (
    <div className={`flex items-center gap-3 rounded-xl border p-4 ${urgent ? "border-clay-100 bg-clay-50" : "border-sun-200 bg-sun-50"}`}>
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={urgent ? "text-clay-500" : "text-sun-600"} aria-hidden>
        <circle cx="12" cy="12" r="9" />
        <path d="M12 7v5l3 2" />
      </svg>
      <div className="min-w-0 flex-1">
        <p className={`text-sm font-semibold ${urgent ? "text-clay-700" : "text-sun-700"}`}>To&apos;lov muddati</p>
        <p className="text-xs text-ink-soft">
          Shu vaqt ichida to&apos;lov qilinmasa, bron bekor bo&apos;ladi va o&apos;rinlar boshqa sayohatchilarga ochiladi.
        </p>
      </div>
      <span className={`font-mono text-2xl font-extrabold ${urgent ? "text-clay-500" : "text-sun-700"}`}>{left > 0 ? mmss(left) : "00:00"}</span>
    </div>
  );
}

/** To'lov usulini tanlash. Provayderlar ulanmaguncha tugma o'chiq ("tez kunda"). */
export function PaymentChooser({ total, installment, methods }: { total: number; installment: Installment; methods: PaymentMethod[] }) {
  const [choice, setChoice] = useState<"full" | "installment">("full");
  const card = methods.filter((m) => m.code !== "uzum_nasiya");
  const nasiya = methods.find((m) => m.code === "uzum_nasiya");
  const enabled = choice === "full" ? card.some((m) => m.enabled) : !!nasiya?.enabled;

  const option = (key: "full" | "installment", body: React.ReactNode) => (
    <label
      className={`flex cursor-pointer items-start gap-3 rounded-xl border-2 p-4 transition ${
        choice === key ? "border-forest-600 bg-forest-50/50" : "border-sand-200 hover:border-forest-300"
      }`}
    >
      <input type="radio" name="pay" className="mt-1 accent-forest-600" checked={choice === key} onChange={() => setChoice(key)} />
      {body}
    </label>
  );

  return (
    <div className="space-y-3">
      <p className="text-xs font-bold uppercase tracking-[0.15em] text-ink-mute">To&apos;lov usuli</p>
      {option(
        "full",
        <span className="flex flex-1 flex-wrap items-start justify-between gap-2">
          <span>
            <span className="flex items-center gap-2 text-sm font-semibold">
              To&apos;liq to&apos;lash <span className="chip bg-forest-100 px-2 py-0.5 text-[10px] uppercase text-forest-700">Tavsiya etiladi</span>
            </span>
            <span className="mt-0.5 block text-xs text-ink-mute">Karta orqali: {card.map((m) => m.name).join(", ")}</span>
          </span>
          <b className="text-sm">{money(total)}</b>
        </span>,
      )}
      {option(
        "installment",
        <span className="flex flex-1 flex-wrap items-start justify-between gap-2">
          <span>
            <span className="text-sm font-semibold">{installment.months} oyga bo&apos;lib</span>
            <span className="mt-0.5 block text-xs text-ink-mute">{nasiya?.name ?? "Uzum Nasiya"}</span>
          </span>
          <span className="text-right">
            <b className="text-sm">{money(installment.monthly_uzs)}</b>
            <span className="text-xs text-ink-mute">/oy</span>
            <span className="block text-[11px] text-ink-mute">jami {money(installment.total_uzs)}</span>
          </span>
        </span>,
      )}
      <button className="btn-primary w-full py-3.5 text-base" disabled={!enabled}>
        {enabled ? `To'lash — ${money(choice === "full" ? total : installment.monthly_uzs)}` : "Onlayn to'lov — tez kunda"}
      </button>
      {!enabled && (
        <p className="text-center text-xs text-ink-mute">Onlayn to&apos;lov tez orada ishga tushadi. Hozircha operatorimiz siz bilan bog&apos;lanadi.</p>
      )}
    </div>
  );
}

export function CancelBooking({ code, tourSlug }: { code: string; tourSlug?: string }) {
  const router = useRouter();
  const [preview, setPreview] = useState<{ can_cancel: boolean; refund_uzs: number; policy_text: string } | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function open() {
    setError("");
    try {
      setPreview(await api.get(`/bookings/${code}/cancel-preview`));
    } catch (e) {
      setError(e instanceof ClientApiError ? e.message : "Xatolik");
    }
  }
  async function confirm() {
    setBusy(true);
    try {
      await api.post(`/bookings/${code}/cancel`, { reason: "Turist bekor qildi" });
      router.refresh();
      setPreview(null);
    } catch (e) {
      setError(e instanceof ClientApiError ? e.message : "Xatolik");
    } finally {
      setBusy(false);
    }
  }

  if (!preview)
    return (
      <div className="grid grid-cols-2 gap-2">
        {tourSlug && (
          <Link href={`/tours/${tourSlug}`} className="btn-ghost">
            Turni ko&apos;rish
          </Link>
        )}
        <button onClick={open} className={`btn-ghost text-clay-500 hover:border-clay-500 hover:text-clay-700 ${tourSlug ? "" : "col-span-2"}`}>
          Bekor qilish
        </button>
        {error && <p className="col-span-2 text-sm text-clay-700">{error}</p>}
      </div>
    );
  return (
    <div className="rounded-xl border border-clay-100 bg-clay-50 p-4 text-sm">
      {preview.can_cancel ? (
        <>
          <p className="text-ink">
            Bekor qilsangiz, qaytariladigan summa: <b>{money(preview.refund_uzs)}</b>
          </p>
          <p className="mt-1 text-xs text-ink-soft">{preview.policy_text}</p>
          {error && <p className="mt-2 text-clay-700">{error}</p>}
          <div className="mt-3 flex gap-2">
            <button onClick={confirm} disabled={busy} className="btn bg-clay-500 text-white hover:bg-clay-700">
              Ha, bekor qilish
            </button>
            <button onClick={() => setPreview(null)} className="btn-ghost">
              Yo&apos;q
            </button>
          </div>
        </>
      ) : (
        <p>Bu bronni endi bekor qilib bo&apos;lmaydi.</p>
      )}
    </div>
  );
}

export function ReviewForm({ code }: { code: string }) {
  const router = useRouter();
  const [rating, setRating] = useState(5);
  const [text, setText] = useState("");
  const [error, setError] = useState("");
  const [sent, setSent] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    try {
      await api.post("/reviews/my", { booking: code, rating, text });
      setSent(true);
      router.refresh();
    } catch (err) {
      setError(err instanceof ClientApiError ? err.message : "Xatolik");
    }
  }
  if (sent) return <p className="text-sm text-forest-700">Rahmat! Sharhingiz qabul qilindi.</p>;
  return (
    <form onSubmit={submit} className="space-y-3">
      <div className="flex gap-1 text-3xl" role="radiogroup" aria-label="Baho">
        {[1, 2, 3, 4, 5].map((n) => (
          <button type="button" key={n} onClick={() => setRating(n)} aria-label={`${n} yulduz`} className={n <= rating ? "text-sun-500" : "text-sand-300"}>
            ★
          </button>
        ))}
      </div>
      <textarea className="input min-h-24" placeholder="Taassurotlaringiz…" value={text} onChange={(e) => setText(e.target.value)} />
      {error && <p className="text-sm text-clay-700">{error}</p>}
      <button className="btn-primary">Sharh qoldirish</button>
    </form>
  );
}
