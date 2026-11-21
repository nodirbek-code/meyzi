"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import type { Category, DestinationShort } from "@/lib/types";

import { Icon } from "./ui";

/** Bosh sahifa qidiruvi: qayerga / qachon / turi. */
export function SearchBar({
  destinations,
  categories,
}: {
  destinations: DestinationShort[];
  categories: Pick<Category, "slug" | "name">[];
}) {
  const router = useRouter();
  const [destination, setDestination] = useState("");
  const [date, setDate] = useState("");
  const [category, setCategory] = useState("");
  const today = new Date().toISOString().slice(0, 10);

  function submit(e: React.FormEvent) {
    e.preventDefault();
    const q = new URLSearchParams();
    if (destination) q.set("destination", destination);
    if (date) q.set("date", date);
    if (category) q.set("category", category);
    router.push(`/tours${q.size ? `?${q}` : ""}`);
  }

  const field = "flex items-center gap-3 rounded-xl px-3 py-2 transition hover:bg-sand-50 sm:px-4";
  const control = "w-full bg-transparent text-sm font-semibold text-ink focus:outline-none";
  return (
    <form
      onSubmit={submit}
      className="grid gap-1 rounded-2xl bg-white p-2 shadow-lift sm:grid-cols-[1fr_1fr_1fr_auto] sm:items-center sm:divide-x sm:divide-sand-200"
    >
      <label className={field}>
        <Icon name="pin" size={20} className="shrink-0 text-forest-500" />
        <span className="w-full">
          <span className="block text-[11px] font-medium text-ink-mute">Qayerga</span>
          <select className={control} value={destination} onChange={(e) => setDestination(e.target.value)}>
            <option value="">Barcha yo&apos;nalishlar</option>
            {destinations.map((d) => (
              <option key={d.slug} value={d.slug}>
                {d.name}
              </option>
            ))}
          </select>
        </span>
      </label>
      <label className={field}>
        <Icon name="calendar" size={20} className="shrink-0 text-forest-500" />
        <span className="w-full">
          <span className="block text-[11px] font-medium text-ink-mute">Qachon</span>
          <input type="date" min={today} className={control} value={date} onChange={(e) => setDate(e.target.value)} />
        </span>
      </label>
      <label className={field}>
        <Icon name="leaf" size={20} className="shrink-0 text-forest-500" />
        <span className="w-full">
          <span className="block text-[11px] font-medium text-ink-mute">Sayohat turi</span>
          <select className={control} value={category} onChange={(e) => setCategory(e.target.value)}>
            <option value="">Hammasi</option>
            {categories.map((c) => (
              <option key={c.slug} value={c.slug}>
                {c.name}
              </option>
            ))}
          </select>
        </span>
      </label>
      <div className="p-1 sm:pl-2">
        <button className="btn-primary h-12 w-full px-7 text-base">
          <Icon name="arrow" size={18} className="hidden sm:block" />
          Qidirish
        </button>
      </div>
    </form>
  );
}
