"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { api, ClientApiError } from "@/lib/client";
import { AMENITIES, money } from "@/lib/format";
import type { RoomOffer, User } from "@/lib/types";

import { accountPhone, phoneReady, VerifiedPhoneField, type VerifiedPhone } from "./PhoneField";
import { Cover } from "./ui";

export function HotelRooms({
  slug,
  initial,
  user,
}: {
  slug: string;
  initial: { check_in: string; check_out: string; guests: string };
  user: User | null;
}) {
  const router = useRouter();
  const today = new Date().toISOString().slice(0, 10);
  const trusted = accountPhone(user);
  const [q, setQ] = useState(initial);
  const [rooms, setRooms] = useState<RoomOffer[]>([]);
  const [error, setError] = useState("");
  const [picked, setPicked] = useState<RoomOffer | null>(null);
  const [count, setCount] = useState(1);
  const [name, setName] = useState(user ? `${user.first_name} ${user.last_name}`.trim() : "");
  const [phone, setPhone] = useState<VerifiedPhone>({ phone: trusted ?? user?.phone ?? "", token: "" });
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    const p = new URLSearchParams();
    if (q.check_in && q.check_out) {
      p.set("check_in", q.check_in);
      p.set("check_out", q.check_out);
    }
    setError("");
    fetch(`/api/proxy/hotels/${slug}/rooms?${p}`)
      .then(async (r) => (r.ok ? setRooms(await r.json()) : setError("Sanalarni tekshiring: chiqish kirishdan keyin bo'lsin (30 kechagacha).")))
      .catch(() => setError("Xatolik"));
  }, [slug, q.check_in, q.check_out]);

  async function book() {
    if (!user) return router.push(`/login?next=/hotels/${slug}`);
    if (!picked) return;
    setBusy(true);
    setError("");
    try {
      await api.post("/hotel-bookings", {
        room_type: picked.id,
        check_in: q.check_in,
        check_out: q.check_out,
        rooms: count,
        guests: Number(q.guests) || 1,
        contact_name: name.trim(),
        contact_phone: phone.phone,
        phone_token: phone.token,
      });
      router.push("/account?hotel=1");
    } catch (e) {
      setError(e instanceof ClientApiError ? e.message : "Xatolik");
      setBusy(false);
    }
  }

  const dated = !!(q.check_in && q.check_out);
  const ready = name.trim().length >= 2 && phoneReady(phone, trusted);

  return (
    <div className="space-y-4">
      <div className="card grid gap-3 p-4 sm:grid-cols-3">
        <label>
          <span className="label">Kirish</span>
          <input className="input" type="date" min={today} value={q.check_in} onChange={(e) => setQ({ ...q, check_in: e.target.value })} />
        </label>
        <label>
          <span className="label">Chiqish</span>
          <input className="input" type="date" min={q.check_in || today} value={q.check_out} onChange={(e) => setQ({ ...q, check_out: e.target.value })} />
        </label>
        <label>
          <span className="label">Mehmonlar</span>
          <input className="input" type="number" min={1} value={q.guests} onChange={(e) => setQ({ ...q, guests: e.target.value })} />
        </label>
      </div>
      {error && <p className="rounded-xl bg-clay-50 px-3 py-2 text-sm text-clay-700">{error}</p>}
      {!dated && <p className="rounded-xl bg-sky-50 px-3 py-2 text-sm text-sky-700">Bo&apos;sh xonalar va narxni ko&apos;rish uchun sanalarni tanlang.</p>}

      <div className="space-y-3">
        {rooms.map((r) => {
          const soldOut = dated && (r.available_rooms ?? 0) < 1;
          const on = picked?.id === r.id;
          return (
            <div key={r.id} className={`card flex flex-wrap gap-4 p-4 transition ${on ? "ring-2 ring-forest-500" : ""}`}>
              <Cover src={r.image} alt={r.name} className="h-24 w-32 shrink-0 overflow-hidden rounded-xl" />
              <div className="min-w-0 flex-1">
                <h3 className="font-sans text-base font-semibold">{r.name}</h3>
                <p className="text-xs text-ink-mute">
                  👥 {r.capacity} kishigacha{r.beds && ` · ${r.beds}`}
                  {r.size_m2 && ` · ${r.size_m2} m²`}
                </p>
                <p className="mt-1 text-xs text-ink-soft">{r.amenities.map((a) => AMENITIES[a] ?? a).join(" · ")}</p>
                {dated && (
                  <p className={`mt-1 text-xs font-semibold ${soldOut ? "text-clay-500" : "text-forest-600"}`}>
                    {soldOut ? "Bo'sh xona yo'q" : `${r.available_rooms} ta bo'sh xona`}
                  </p>
                )}
              </div>
              <div className="text-right">
                <div className="text-lg font-extrabold">{money(r.price_per_night_uzs)}</div>
                <div className="text-xs text-ink-mute">1 kecha</div>
                {r.stay_total_uzs && (
                  <div className="mt-1 text-xs">
                    {r.nights} kecha: <b>{money(r.stay_total_uzs)}</b>
                  </div>
                )}
                {dated && !soldOut && (
                  <button
                    className={`mt-2 px-4 py-1.5 text-xs ${on ? "btn-primary" : "btn-ghost"}`}
                    onClick={() => {
                      setPicked(r);
                      setCount(1);
                    }}
                  >
                    {on ? "✓ Tanlandi" : "Tanlash"}
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {picked && dated && (
        <div className="card space-y-4 p-5">
          <h3 className="font-sans text-lg font-semibold">{picked.name} — bron</h3>
          <div className="flex items-center justify-between text-sm">
            <span>Xonalar soni</span>
            <input className="input w-24" type="number" min={1} max={picked.available_rooms ?? 1} value={count} onChange={(e) => setCount(Number(e.target.value))} />
          </div>
          {user && (
            <div className="space-y-3 border-t border-sand-200 pt-4">
              <label className="block">
                <span className="label">
                  Aloqa uchun ism <span className="text-clay-500">*</span>
                </span>
                <input className="input" value={name} onChange={(e) => setName(e.target.value)} />
              </label>
              <VerifiedPhoneField value={phone} onChange={setPhone} trustedPhone={trusted} />
            </div>
          )}
          <div className="flex items-baseline justify-between rounded-xl bg-sand-100 p-4">
            <span className="font-semibold">Jami</span>
            <b className="text-xl">{money((picked.stay_total_uzs ?? 0) * count)}</b>
          </div>
          <button className="btn-primary w-full py-3.5 text-base" disabled={busy || (!!user && !ready)} onClick={book}>
            {user ? (busy ? "Band qilinmoqda…" : "Bron qilish") : "Kirish va bron qilish"}
          </button>
          <p className="text-center text-xs text-ink-mute">Xona 30 daqiqaga siz uchun band qilinadi</p>
        </div>
      )}
    </div>
  );
}
