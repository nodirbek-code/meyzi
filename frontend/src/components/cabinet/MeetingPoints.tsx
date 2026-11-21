"use client";

import { useState } from "react";

import { api } from "@/lib/client";
import type { Destination, Paginated } from "@/lib/types";

import { ErrorText, Loading, Panel } from "./Bits";
import { useAction, useData } from "./useData";

type Point = {
  id: number;
  destination: string;
  name: string;
  address: string;
  latitude: string;
  longitude: string;
  is_active: boolean;
};

/** "41.311151, 69.279737" yoki Yandex/Google havolasidan koordinatalarni ajratib olish */
export function parseCoords(raw: string): { latitude: string; longitude: string } | null {
  const s = raw.trim();
  // Yandex: ?pt=lon,lat yoki ll=lon,lat
  const y = s.match(/[?&](?:pt|ll)=(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)/);
  if (y) return { latitude: Number(y[2]).toFixed(6), longitude: Number(y[1]).toFixed(6) };
  // Google: @lat,lon yoki oddiy "lat, lon"
  const g = s.match(/(-?\d{1,2}\.\d+)\s*,\s*(-?\d{1,3}\.\d+)/);
  if (g) return { latitude: Number(g[1]).toFixed(6), longitude: Number(g[2]).toFixed(6) };
  return null;
}

/**
 * Gidning uchrashuv joylari. Turist bron qilganda faqat shulardan tanlaydi.
 * Bronlarda ishlatilgan joy o'chirilmaydi — nofaol bo'ladi.
 */
export function MeetingPoints({ cities }: { cities: string[] }) {
  const points = useData<Point[]>("/cabinet/guide/meeting-points");
  const all = useData<Paginated<Destination>>("/catalog/destinations?page_size=50");
  const act = useAction();
  const names = Object.fromEntries((all.data?.results ?? []).map((d) => [d.slug, d.name]));
  const [f, setF] = useState({ destination: cities[0] ?? "", name: "", address: "", coords: "" });
  const coords = parseCoords(f.coords);

  async function add(e: React.FormEvent) {
    e.preventDefault();
    if (!coords) return act.setError("Koordinatani kiriting: masalan 39.654167, 66.959722 yoki xarita havolasi.");
    const ok = await act.run(() =>
      api.post("/cabinet/guide/meeting-points", { destination: f.destination || cities[0], name: f.name, address: f.address, ...coords }),
    );
    if (ok) {
      setF({ ...f, name: "", address: "", coords: "" });
      points.reload();
    }
  }

  const active = points.data?.filter((p) => p.is_active) ?? [];

  return (
    <Panel title="Uchrashuv joylarim">
      <p className="mb-4 text-sm text-ink-soft">
        Turistlar bron qilganda faqat shu ro&apos;yxatdan tanlaydi. Har bir shahar uchun kamida bitta joy qo&apos;shing — aks holda
        shu shaharga bron qilib bo&apos;lmaydi.
      </p>
      {points.loading && <Loading />}
      {cities.some((c) => !active.some((p) => p.destination === c)) && !points.loading && (
        <p className="mb-4 rounded-xl bg-sun-50 px-3 py-2 text-sm text-sun-700">
          Joy belgilanmagan shaharlar: {cities.filter((c) => !active.some((p) => p.destination === c)).map((c) => names[c] ?? c).join(", ")}
        </p>
      )}
      <div className="space-y-2">
        {points.data?.map((p) => (
          <div key={p.id} className={`flex flex-wrap items-center gap-3 rounded-xl border p-3 ${p.is_active ? "border-sand-200" : "border-dashed border-sand-300 opacity-60"}`}>
            <span className="text-sky-500" aria-hidden>
              📍
            </span>
            <div className="min-w-0 flex-1 text-sm">
              <p className="font-semibold">
                {p.name} <span className="font-normal text-ink-mute">· {names[p.destination] ?? p.destination}</span>
              </p>
              <p className="text-xs text-ink-soft">{p.address}</p>
              <a
                href={`https://yandex.uz/maps/?pt=${p.longitude},${p.latitude}&z=16&l=map`}
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs text-sky-700 hover:underline"
              >
                {p.latitude}, {p.longitude} ↗
              </a>
            </div>
            <button
              className="text-xs font-semibold text-ink-soft hover:text-forest-700"
              disabled={act.busy}
              onClick={() => act.run(async () => { await api.patch(`/cabinet/guide/meeting-points/${p.id}`, { is_active: !p.is_active }); points.reload(); })}
            >
              {p.is_active ? "Nofaol qilish" : "Faollashtirish"}
            </button>
            <button
              className="text-xs font-semibold text-clay-500 hover:text-clay-700"
              disabled={act.busy}
              onClick={() => act.run(async () => { await api.del(`/cabinet/guide/meeting-points/${p.id}`); points.reload(); })}
            >
              O&apos;chirish
            </button>
          </div>
        ))}
        {points.data && !points.data.length && <p className="text-sm text-ink-mute">Hali joy qo&apos;shilmagan.</p>}
      </div>

      <form onSubmit={add} className="mt-5 grid gap-3 rounded-xl bg-sand-100 p-4 sm:grid-cols-2">
        <p className="text-sm font-semibold sm:col-span-2">Yangi joy qo&apos;shish</p>
        <label>
          <span className="label">Shahar</span>
          <select className="input" value={f.destination} onChange={(e) => setF({ ...f, destination: e.target.value })}>
            {cities.map((c) => (
              <option key={c} value={c}>
                {names[c] ?? c}
              </option>
            ))}
          </select>
        </label>
        <label>
          <span className="label">Nomi</span>
          <input className="input" required placeholder="Registon maydoni, asosiy kirish" value={f.name} onChange={(e) => setF({ ...f, name: e.target.value })} />
        </label>
        <label className="sm:col-span-2">
          <span className="label">Manzil</span>
          <input className="input" required placeholder="Registon ko'chasi, Samarqand" value={f.address} onChange={(e) => setF({ ...f, address: e.target.value })} />
        </label>
        <label className="sm:col-span-2">
          <span className="label">Xaritadagi joyi</span>
          <input
            className="input"
            required
            placeholder="39.654167, 66.959722 — yoki Yandex/Google xarita havolasini qo'ying"
            value={f.coords}
            onChange={(e) => setF({ ...f, coords: e.target.value })}
          />
          <span className="mt-1 block text-xs text-ink-mute">
            {coords ? (
              <>
                ✓ Aniqlandi: {coords.latitude}, {coords.longitude} ·{" "}
                <a className="text-sky-700 hover:underline" target="_blank" rel="noopener noreferrer" href={`https://yandex.uz/maps/?pt=${coords.longitude},${coords.latitude}&z=16&l=map`}>
                  tekshirish ↗
                </a>
              </>
            ) : (
              "Xaritada joyni bosing va koordinatani nusxalang yoki havolani qo'ying."
            )}
          </span>
        </label>
        <ErrorText text={act.error} />
        <button className="btn-primary sm:col-span-2" disabled={act.busy || !cities.length}>
          Joy qo&apos;shish
        </button>
      </form>
    </Panel>
  );
}
