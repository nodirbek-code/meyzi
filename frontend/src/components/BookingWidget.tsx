"use client";

import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";

import { api, ClientApiError } from "@/lib/client";
import { money, POLICY_LABEL, time } from "@/lib/format";
import type { Departure, User } from "@/lib/types";

import { accountPhone, phoneReady, VerifiedPhoneField, type VerifiedPhone } from "./PhoneField";
import { Icon } from "./ui";

const MARKUP = 1.44; // muddatli to'lov (backend bilan bir xil: settings.MEYZI_INSTALLMENT_MARKUP)
const MONTHS = 12;
const MON = ["yan", "fev", "mar", "apr", "may", "iyn", "iyl", "avg", "sen", "okt", "noy", "dek"];
const WD = ["Yak", "Dush", "Sesh", "Chor", "Pay", "Jum", "Shan"];
const ICONS_MAX = 10;

function parts(iso: string) {
  const [y, m, d] = iso.split("-").map(Number);
  const dt = new Date(y, m - 1, d);
  return { wd: WD[dt.getDay()], day: d, mon: MON[m - 1] };
}

export function BookingWidget({
  slug,
  departures,
  maxGroup,
  user,
  price,
  departureTime,
  returnTime,
  rating,
  reviewsCount,
  policy,
}: {
  slug: string;
  departures: Departure[];
  maxGroup: number;
  user: User | null;
  price: number;
  departureTime: string | null;
  returnTime: string | null;
  rating: string;
  reviewsCount: number;
  policy: string;
}) {
  const router = useRouter();
  const bookable = departures.filter((d) => d.is_bookable);
  const [depId, setDepId] = useState<number | null>(bookable[0]?.id ?? null);
  const [seats, setSeats] = useState(1);
  const fullName = user ? `${user.first_name} ${user.last_name}`.trim() : "";
  const [travelers, setTravelers] = useState<string[]>([fullName]);
  const [name, setName] = useState(fullName);
  const trusted = accountPhone(user);
  const [phone, setPhone] = useState<VerifiedPhone>({ phone: trusted ?? user?.phone ?? "", token: "" });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const dep = bookable.find((d) => d.id === depId) ?? null;
  const unit = dep?.price_uzs ?? price;
  const maxSeats = Math.max(1, Math.min(dep?.seats_left ?? 1, maxGroup, 20));
  const total = unit * seats;
  const monthly = useMemo(() => Math.round((total * MARKUP) / MONTHS), [total]);

  function changeSeats(n: number) {
    const next = Math.max(1, Math.min(maxSeats, n));
    setSeats(next);
    setTravelers((t) => Array.from({ length: next }, (_, i) => t[i] ?? ""));
  }

  const travelersOk = travelers.every((t) => t.trim().length >= 2);
  const ready = !!dep && name.trim().length >= 2 && phoneReady(phone, trusted) && travelersOk;

  async function book() {
    if (!user) {
      router.push(`/login?next=/tours/${slug}`);
      return;
    }
    if (!dep) return;
    setBusy(true);
    setError("");
    try {
      const b = await api.post<{ code: string }>("/bookings", {
        departure: dep.id,
        seats,
        contact_name: name.trim(),
        contact_phone: phone.phone,
        phone_token: phone.token,
        travelers: travelers.map((t) => ({ full_name: t.trim() })),
      });
      router.push(`/account/bookings/${b.code}`);
    } catch (e) {
      setError(e instanceof ClientApiError ? e.message : "Xatolik yuz berdi");
      setBusy(false);
    }
  }

  return (
    <div id="bron" className="card scroll-mt-24 space-y-5 p-5">
      {/* Narx */}
      <div>
        <div className="flex items-baseline gap-1.5">
          <span className="text-3xl font-extrabold">{money(unit)}</span>
          <span className="text-sm text-ink-mute">/ kishi</span>
        </div>
        <div className="mt-1.5 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-ink-soft">
          {departureTime && (
            <span className="inline-flex items-center gap-1">
              <Icon name="clock" size={13} />
              {time(departureTime)}
              {returnTime && ` — ${time(returnTime)}`}
            </span>
          )}
          {reviewsCount > 0 && (
            <span>
              <span className="text-sun-500">★</span> <b className="text-ink">{Number(rating).toFixed(1)}</b> ({reviewsCount})
            </span>
          )}
          <span className={policy === "non_refundable" ? "text-clay-500" : "text-forest-600"}>
            {policy === "non_refundable" ? "✕" : "✓"} {POLICY_LABEL[policy]}
          </span>
        </div>
      </div>

      {!bookable.length ? (
        <p className="rounded-xl bg-sand-100 p-4 text-sm text-ink-soft">
          Hozircha bo&apos;sh sana yo&apos;q. Tez orada yangi sanalar qo&apos;shiladi.
        </p>
      ) : (
        <>
          <h3 className="font-sans text-base font-semibold">Turni bron qilish</h3>

          {/* Sanalar */}
          <div>
            <span className="label">Ketish sanasi</span>
            <div className="no-scrollbar -mx-1 flex gap-2 overflow-x-auto px-1 pb-1">
              {bookable.map((d) => {
                const p = parts(d.date);
                const on = d.id === depId;
                return (
                  <button
                    key={d.id}
                    onClick={() => {
                      setDepId(d.id);
                      changeSeats(Math.min(seats, d.seats_left));
                    }}
                    className={`flex w-[4.5rem] shrink-0 flex-col items-center rounded-xl border-2 px-1 py-2 transition ${
                      on ? "border-forest-600 bg-forest-50" : "border-sand-200 bg-white hover:border-forest-300"
                    }`}
                  >
                    <span className="text-[10px] font-semibold uppercase text-ink-mute">{p.wd}</span>
                    <span className="text-xl font-extrabold leading-6">
                      {p.day}
                      <span className="ml-0.5 text-xs font-medium text-ink-soft">{p.mon}</span>
                    </span>
                    <span className="mt-1 rounded-full bg-forest-100 px-1.5 text-[10px] font-bold text-forest-700">{d.seats_left} ✓</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* O'rinlar soni */}
          <div>
            <span className="label">O&apos;rinlar soni</span>
            <div className="flex items-center justify-between">
              <button
                className="flex h-10 w-10 items-center justify-center rounded-full border border-sand-300 text-lg hover:border-forest-400 disabled:opacity-40"
                onClick={() => changeSeats(seats - 1)}
                disabled={seats <= 1}
                aria-label="Kamaytirish"
              >
                −
              </button>
              <span className="text-3xl font-extrabold">{seats}</span>
              <button
                className="flex h-10 w-10 items-center justify-center rounded-full border border-sand-300 text-lg hover:border-forest-400 disabled:opacity-40"
                onClick={() => changeSeats(seats + 1)}
                disabled={seats >= maxSeats}
                aria-label="Ko'paytirish"
              >
                +
              </button>
            </div>
            <div className="mt-3 flex items-center gap-1" aria-hidden>
              {Array.from({ length: Math.min(maxSeats, ICONS_MAX) }, (_, i) => (
                <svg key={i} width="18" height="18" viewBox="0 0 24 24" className={i < seats ? "text-forest-600" : "text-sand-300"} fill="currentColor">
                  <circle cx="12" cy="7" r="4" />
                  <path d="M4 21c.5-4.5 3.8-7 8-7s7.5 2.5 8 7Z" />
                </svg>
              ))}
              {maxSeats > ICONS_MAX && <span className="ml-1 text-xs text-ink-mute">+{maxSeats - ICONS_MAX} ta</span>}
            </div>
          </div>

          {user && (
            <>
              {/* Sayohatchilar */}
              <div>
                <span className="label">Sayohatchilar</span>
                <div className="space-y-2">
                  {travelers.map((t, i) => (
                    <div key={i} className="flex items-center gap-2">
                      <span className="w-5 shrink-0 text-right text-xs font-semibold text-ink-mute">{i + 1}</span>
                      <input
                        className="input py-2"
                        placeholder="Ism va familiya"
                        value={t}
                        onChange={(e) => setTravelers((arr) => arr.map((x, j) => (j === i ? e.target.value : x)))}
                      />
                    </div>
                  ))}
                </div>
                <p className="mt-1.5 text-xs text-ink-mute">Har bir o&apos;rin uchun ism va familiya — gid ro&apos;yxatni shu bo&apos;yicha oladi.</p>
              </div>

              {/* Aloqa */}
              <div className="space-y-3 border-t border-sand-200 pt-4">
                <label className="block">
                  <span className="label">
                    Aloqa uchun ism <span className="text-clay-500">*</span>
                  </span>
                  <input className="input" value={name} onChange={(e) => setName(e.target.value)} />
                </label>
                <VerifiedPhoneField value={phone} onChange={setPhone} trustedPhone={trusted} />
              </div>
            </>
          )}

          <div className="flex justify-between border-t border-sand-200 pt-4 text-sm">
            <span className="text-ink-soft">
              {seats} × {money(unit)}
            </span>
            <b className="text-lg">{money(total)}</b>
          </div>

          {error && <p className="rounded-xl bg-clay-50 px-3 py-2 text-sm text-clay-700">{error}</p>}
          <button className="btn-primary w-full py-3.5 text-base" onClick={book} disabled={busy || (!!user && !ready)}>
            {busy ? "Band qilinmoqda…" : user ? "Bron qilish" : "Kirish va bron qilish"}
          </button>
          <p className="flex items-center justify-between gap-2 rounded-xl bg-sun-50 px-3 py-2 text-xs text-sun-700">
            <span>
              Bo&apos;lib to&apos;lash: <b>{money(monthly)}</b> × {MONTHS} oy
            </span>
            <span className="text-ink-mute">tez kunda</span>
          </p>
          <p className="text-center text-xs text-ink-mute">O&apos;rinlar 30 daqiqaga siz uchun band qilinadi</p>
        </>
      )}
    </div>
  );
}
