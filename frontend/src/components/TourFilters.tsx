"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";

import { LANGUAGE_NAMES } from "@/lib/format";
import type { Category, DestinationShort } from "@/lib/types";

const FIELDS = ["search", "destination", "category", "language", "min_price", "max_price", "min_days", "max_days", "cancellation_policy"] as const;
type Values = Record<(typeof FIELDS)[number], string>;

const DAYS = [
  { label: "1 kun", min: "1", max: "1" },
  { label: "2–3 kun", min: "2", max: "3" },
  { label: "4+ kun", min: "4", max: "" },
];

const read = (p: URLSearchParams): Values => Object.fromEntries(FIELDS.map((f) => [f, p.get(f) ?? ""])) as Values;

/** Katalog filtrlari (chap panel). Sana va saralash — alohida (sana tasmasi, yuqoridagi saralash). */
export function TourFilters({ destinations, categories }: { destinations: DestinationShort[]; categories: Category[] }) {
  const router = useRouter();
  const pathname = usePathname();
  const params = useSearchParams();
  const [v, setV] = useState<Values>(() => read(params));
  const [open, setOpen] = useState(false);
  useEffect(() => setV(read(params)), [params]);

  const set = (k: keyof Values) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
    setV((s) => ({ ...s, [k]: e.target.value }));

  function go(next: Values) {
    const q = new URLSearchParams();
    for (const [k, val] of Object.entries(next)) if (val) q.set(k, val);
    for (const keep of ["date", "ordering"]) {
      const val = params.get(keep);
      if (val) q.set(keep, val);
    }
    router.push(`${pathname}${q.size ? `?${q}` : ""}`);
    setOpen(false);
  }

  const activeCount = FIELDS.filter((f) => params.get(f)).length + (params.get("date") ? 1 : 0);
  const digits = (s: string) => s.replace(/\D/g, "");

  return (
    <div>
      <button type="button" onClick={() => setOpen((o) => !o)} className="btn-ghost w-full lg:hidden" aria-expanded={open}>
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
          <path d="M4 6h16M7 12h10M10 18h4" />
        </svg>
        Filtrlar{activeCount > 0 && <span className="chip bg-forest-600 px-2 py-0 text-white">{activeCount}</span>}
      </button>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          go(v);
        }}
        className={`card mt-3 space-y-5 p-5 lg:mt-0 lg:block ${open ? "block" : "hidden"}`}
      >
        <h2 className="font-sans text-base font-semibold">Filtrlar</h2>

        <label className="block">
          <span className="label">Qidirish</span>
          <input className="input" placeholder="Tog', Samarqand…" value={v.search} onChange={set("search")} />
        </label>

        <label className="block">
          <span className="label">Joylashuv</span>
          <select className="input" value={v.destination} onChange={set("destination")}>
            <option value="">Barcha yo&apos;nalishlar</option>
            {destinations.map((d) => (
              <option key={d.slug} value={d.slug}>
                {d.name}
              </option>
            ))}
          </select>
        </label>

        <label className="block">
          <span className="label">Kategoriya</span>
          <select className="input" value={v.category} onChange={set("category")}>
            <option value="">Barcha kategoriyalar</option>
            {categories.map((c) => (
              <option key={c.slug} value={c.slug}>
                {c.name} ({c.tours_count})
              </option>
            ))}
          </select>
        </label>

        <label className="block">
          <span className="label">Gid tili</span>
          <select className="input" value={v.language} onChange={set("language")}>
            <option value="">Istalgan til</option>
            {Object.entries(LANGUAGE_NAMES).map(([code, name]) => (
              <option key={code} value={code}>
                {name}
              </option>
            ))}
          </select>
        </label>

        <div>
          <span className="label">Narx (so&apos;m)</span>
          <div className="grid grid-cols-2 gap-2">
            <input className="input" inputMode="numeric" placeholder="0" value={v.min_price} onChange={(e) => setV({ ...v, min_price: digits(e.target.value) })} />
            <input className="input" inputMode="numeric" placeholder="3 000 000" value={v.max_price} onChange={(e) => setV({ ...v, max_price: digits(e.target.value) })} />
          </div>
        </div>

        <div>
          <span className="label">Davomiyligi</span>
          <div className="grid grid-cols-3 gap-1.5">
            {DAYS.map((d) => {
              const on = v.min_days === d.min && v.max_days === d.max;
              return (
                <button
                  key={d.label}
                  type="button"
                  onClick={() => setV({ ...v, min_days: on ? "" : d.min, max_days: on ? "" : d.max })}
                  className={`rounded-lg border px-2 py-2 text-xs font-semibold transition ${
                    on ? "border-forest-600 bg-forest-600 text-white" : "border-sand-300 bg-white text-ink-soft hover:border-forest-400"
                  }`}
                >
                  {d.label}
                </button>
              );
            })}
          </div>
        </div>

        <label className="flex cursor-pointer items-center justify-between gap-3 rounded-xl bg-forest-50 px-3 py-2.5">
          <span className="text-sm font-medium text-forest-800">Faqat bepul bekor qilish</span>
          <input
            type="checkbox"
            className="h-4 w-4 accent-forest-600"
            checked={v.cancellation_policy === "free"}
            onChange={(e) => setV({ ...v, cancellation_policy: e.target.checked ? "free" : "" })}
          />
        </label>

        <div className="flex gap-2 pt-1">
          <button className="btn-primary flex-1">Qo&apos;llash</button>
          <button
            type="button"
            onClick={() => {
              const empty = Object.fromEntries(FIELDS.map((f) => [f, ""])) as Values;
              setV(empty);
              router.push(pathname);
              setOpen(false);
            }}
            className="btn-ghost"
          >
            Tozalash
          </button>
        </div>
      </form>
    </div>
  );
}

/** Natijalar ustidagi saralash */
export function SortSelect() {
  const router = useRouter();
  const pathname = usePathname();
  const params = useSearchParams();
  return (
    <label className="flex items-center gap-2 text-sm">
      <span className="hidden text-ink-mute sm:inline">Saralash:</span>
      <select
        className="input w-auto py-2 pr-8"
        value={params.get("ordering") ?? ""}
        onChange={(e) => {
          const q = new URLSearchParams(params);
          if (e.target.value) q.set("ordering", e.target.value);
          else q.delete("ordering");
          q.delete("page");
          router.push(`${pathname}${q.size ? `?${q}` : ""}`);
        }}
      >
        <option value="">Tavsiya etilgan</option>
        <option value="price_uzs">Arzonidan</option>
        <option value="-price_uzs">Qimmatidan</option>
        <option value="-rating">Reyting bo&apos;yicha</option>
        <option value="duration_days">Qisqasidan</option>
      </select>
    </label>
  );
}
