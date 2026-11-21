"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { api, ClientApiError } from "@/lib/client";
import { LANGUAGE_NAMES, money } from "@/lib/format";
import type { DestinationShort, GuideQuote, MeetingPoint, User } from "@/lib/types";

import { accountPhone, phoneReady, VerifiedPhoneField, type VerifiedPhone } from "./PhoneField";

const DURATIONS = [
  ["half_day", "Yarim kun", "4 soat"],
  ["full_day", "To'liq kun", "8 soat"],
  ["multi_day", "Bir necha kun", "2–14 kun"],
] as const;

/**
 * Gidni bron qilish (so'rov). Uchrashuv joyi — faqat gid belgilagan ro'yxatdan (erkin matn yo'q).
 * Telefon — Telegram kodi bilan tasdiqlanadi.
 */
export function GuideRequestForm({
  slug,
  destinations,
  languages,
  maxGroup,
  busyDates,
  meetingPoints,
  user,
}: {
  slug: string;
  destinations: DestinationShort[];
  languages: string[];
  maxGroup: number;
  busyDates: string[];
  meetingPoints: MeetingPoint[];
  user: User | null;
}) {
  const router = useRouter();
  const minDate = new Date(Date.now() + 36 * 3600 * 1000).toISOString().slice(0, 10);
  const trusted = accountPhone(user);
  const [f, setF] = useState({
    duration: "full_day",
    days: 2,
    group_size: 2,
    destination: destinations.find((d) => meetingPoints.some((p) => p.destination === d.slug))?.slug ?? destinations[0]?.slug ?? "",
    language: languages[0] ?? "uz",
    start_date: "",
    start_time: "09:00",
    meeting_point: "",
    contact_name: user ? `${user.first_name} ${user.last_name}`.trim() : "",
    note: "",
  });
  const [phone, setPhone] = useState<VerifiedPhone>({ phone: trusted ?? user?.phone ?? "", token: "" });
  const [quote, setQuote] = useState<GuideQuote | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const set =
    (k: keyof typeof f) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) =>
      setF({ ...f, [k]: e.target.type === "number" ? Number(e.target.value) : e.target.value });

  const points = useMemo(() => meetingPoints.filter((p) => p.destination === f.destination), [meetingPoints, f.destination]);
  useEffect(() => {
    // shahar almashsa — shu shahardagi birinchi joy
    setF((s) => (points.some((p) => String(p.id) === s.meeting_point) ? s : { ...s, meeting_point: points[0] ? String(points[0].id) : "" }));
  }, [points]);

  useEffect(() => {
    const q = new URLSearchParams({
      duration: f.duration,
      days: String(f.duration === "multi_day" ? f.days : 1),
      group_size: String(f.group_size),
    });
    fetch(`/api/proxy/guides/${slug}/quote?${q}`)
      .then((r) => (r.ok ? r.json() : null))
      .then(setQuote)
      .catch(() => setQuote(null));
  }, [slug, f.duration, f.days, f.group_size]);

  const isBusy = !!f.start_date && busyDates.includes(f.start_date);
  const ready = !!f.start_date && !!f.meeting_point && f.contact_name.trim().length >= 2 && phoneReady(phone, trusted) && !isBusy;
  const point = points.find((p) => String(p.id) === f.meeting_point);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!user) return router.push(`/login?next=/guides/${slug}`);
    setBusy(true);
    setError("");
    try {
      await api.post("/guide-bookings", {
        ...f,
        meeting_point: Number(f.meeting_point),
        guide: slug,
        days: f.duration === "multi_day" ? f.days : 1,
        contact_phone: phone.phone,
        phone_token: phone.token,
      });
      router.push("/account?guide=1");
    } catch (err) {
      setError(err instanceof ClientApiError ? err.message : "Xatolik");
      setBusy(false);
    }
  }

  return (
    <form onSubmit={submit} id="bron" className="card scroll-mt-24 space-y-5 p-5">
      <div>
        <h3 className="font-sans text-lg font-semibold">Gidni bron qilish</h3>
        <p className="text-xs text-ink-mute">Gid 24 soat ichida javob beradi. To&apos;lov — gid qabul qilgandan keyin.</p>
      </div>

      <div className="grid grid-cols-3 gap-2">
        {DURATIONS.map(([v, l, h]) => (
          <button
            type="button"
            key={v}
            onClick={() => setF({ ...f, duration: v })}
            className={`rounded-xl border-2 px-2 py-2.5 text-center transition ${
              f.duration === v ? "border-forest-600 bg-forest-50" : "border-sand-200 hover:border-forest-300"
            }`}
          >
            <span className="block text-sm font-semibold">{l}</span>
            <span className="block text-[11px] text-ink-mute">{h}</span>
          </button>
        ))}
      </div>

      <div className="grid grid-cols-2 gap-3">
        {f.duration === "multi_day" && (
          <label>
            <span className="label">Kunlar</span>
            <input className="input" type="number" min={2} max={14} value={f.days} onChange={set("days")} />
          </label>
        )}
        <label>
          <span className="label">Odamlar</span>
          <input className="input" type="number" min={1} max={maxGroup} value={f.group_size} onChange={set("group_size")} />
        </label>
        <label>
          <span className="label">Sana</span>
          <input className="input" type="date" min={minDate} required value={f.start_date} onChange={set("start_date")} />
        </label>
        <label>
          <span className="label">Boshlanish vaqti</span>
          <input className="input" type="time" required value={f.start_time} onChange={set("start_time")} />
        </label>
        <label>
          <span className="label">Shahar</span>
          <select className="input" value={f.destination} onChange={set("destination")}>
            {destinations.map((d) => (
              <option key={d.slug} value={d.slug}>
                {d.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          <span className="label">Til</span>
          <select className="input" value={f.language} onChange={set("language")}>
            {languages.map((l) => (
              <option key={l} value={l}>
                {LANGUAGE_NAMES[l] ?? l}
              </option>
            ))}
          </select>
        </label>
      </div>
      {isBusy && <p className="rounded-xl bg-clay-50 px-3 py-2 text-sm text-clay-700">Gid bu kunda band — boshqa sanani tanlang.</p>}

      {/* Uchrashuv joyi — faqat ro'yxatdan */}
      <div>
        <span className="label">
          Uchrashuv joyi <span className="text-clay-500">*</span>
        </span>
        {points.length ? (
          <div className="space-y-2">
            {points.map((p) => (
              <label
                key={p.id}
                className={`flex cursor-pointer items-start gap-3 rounded-xl border-2 p-3 transition ${
                  String(p.id) === f.meeting_point ? "border-forest-600 bg-forest-50/50" : "border-sand-200 hover:border-forest-300"
                }`}
              >
                <input
                  type="radio"
                  name="meeting_point"
                  className="mt-1 accent-forest-600"
                  checked={String(p.id) === f.meeting_point}
                  onChange={() => setF({ ...f, meeting_point: String(p.id) })}
                />
                <span className="min-w-0 text-sm">
                  <span className="block font-semibold">{p.name}</span>
                  <span className="block text-xs text-ink-mute">{p.address}</span>
                </span>
              </label>
            ))}
            {point && (
              <a
                href={`https://yandex.uz/maps/?pt=${point.longitude},${point.latitude}&z=16&l=map`}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-block text-xs font-semibold text-sky-700 hover:underline"
              >
                Tanlangan joyni xaritada ko&apos;rish ↗
              </a>
            )}
          </div>
        ) : (
          <p className="rounded-xl bg-sand-100 px-3 py-2.5 text-sm text-ink-soft">
            Gid bu shaharda hali uchrashuv joyini belgilamagan — boshqa shaharni tanlang.
          </p>
        )}
        <p className="mt-1.5 text-xs text-ink-mute">Uchrashuv joylarini gid belgilaydi — xavfsizlik uchun boshqa joy tanlab bo&apos;lmaydi.</p>
      </div>

      {user && (
        <div className="space-y-3 border-t border-sand-200 pt-4">
          <label className="block">
            <span className="label">
              Aloqa uchun ism <span className="text-clay-500">*</span>
            </span>
            <input className="input" required value={f.contact_name} onChange={set("contact_name")} />
          </label>
          <VerifiedPhoneField value={phone} onChange={setPhone} trustedPhone={trusted} />
          <label className="block">
            <span className="label">Izoh (ixtiyoriy)</span>
            <textarea className="input min-h-20" placeholder="Qiziqishlaringiz, bolalar bormi va h.k." value={f.note} onChange={set("note")} />
          </label>
        </div>
      )}

      {quote && (
        <div className="space-y-1.5 rounded-xl bg-sand-100 p-4 text-sm">
          <div className="flex justify-between">
            <span className="text-ink-soft">Asosiy narx</span>
            <span>{money(quote.base_uzs)}</span>
          </div>
          {quote.surcharge_uzs > 0 && (
            <div className="flex justify-between text-ink-soft">
              <span>Guruh ustamasi</span>
              <span>+{money(quote.surcharge_uzs)}</span>
            </div>
          )}
          <div className="flex justify-between border-t border-sand-200 pt-2 text-base font-bold">
            <span>Jami</span>
            <span>{money(quote.total_uzs)}</span>
          </div>
        </div>
      )}
      {error && <p className="rounded-xl bg-clay-50 px-3 py-2 text-sm text-clay-700">{error}</p>}
      <button className="btn-primary w-full py-3.5 text-base" disabled={busy || (!!user && !ready)}>
        {user ? (busy ? "Yuborilmoqda…" : "So'rov yuborish") : "Kirish va so'rov yuborish"}
      </button>
      {!user && (
        <p className="text-center text-xs">
          <Link href="/register" className="font-semibold text-forest-600">
            Ro&apos;yxatdan o&apos;tish
          </Link>
        </p>
      )}
    </form>
  );
}
