"use client";

import Link from "next/link";
import { useMemo, useRef, useState } from "react";

const MONTHS = ["yanvar", "fevral", "mart", "aprel", "may", "iyun", "iyul", "avgust", "sentabr", "oktabr", "noyabr", "dekabr"];
const WD = ["Ya", "Du", "Se", "Ch", "Pa", "Ju", "Sh"];

export type CalendarDay = { date: string; tours: number };

function iso(d: Date) {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

/**
 * Gorizontal sana tasmasi: keyingi N kun. Turi bor kunlar faol (nuqta bilan), dam olish kunlari ajratilgan.
 * Kun bosilganda `/tours?date=...` (+ `baseQuery`). "Dam olish kunlari" — faqat shanba/yakshanba.
 */
export function DateStrip({
  calendar,
  selected,
  days = 45,
  baseQuery = "",
}: {
  calendar: CalendarDay[];
  selected?: string;
  days?: number;
  baseQuery?: string;
}) {
  const [weekendsOnly, setWeekendsOnly] = useState(false);
  const scroller = useRef<HTMLDivElement>(null);
  const counts = useMemo(() => new Map(calendar.map((c) => [c.date, c.tours])), [calendar]);

  const list = useMemo(() => {
    const start = new Date();
    start.setHours(0, 0, 0, 0);
    return Array.from({ length: days }, (_, i) => {
      const d = new Date(start);
      d.setDate(start.getDate() + i);
      return d;
    });
  }, [days]);

  const href = (date: string) => {
    const q = new URLSearchParams(baseQuery);
    if (selected === date) q.delete("date");
    else q.set("date", date);
    q.delete("page");
    return `/tours${q.size ? `?${q}` : ""}`;
  };

  const scroll = (dir: number) => scroller.current?.scrollBy({ left: dir * 320, behavior: "smooth" });

  return (
    <div className="card p-4">
      <div className="mb-3 flex items-center justify-between gap-3">
        <span className="text-sm font-semibold">Sanani tanlang</span>
        <button
          onClick={() => setWeekendsOnly((w) => !w)}
          className={`chip border transition ${
            weekendsOnly ? "border-forest-600 bg-forest-600 text-white" : "border-sand-300 bg-white text-ink-soft hover:border-forest-400"
          }`}
        >
          Dam olish kunlari
        </button>
      </div>
      <div className="flex items-center gap-1">
        <button onClick={() => scroll(-1)} className="hidden h-8 w-8 shrink-0 items-center justify-center rounded-full border border-sand-200 text-ink-soft hover:bg-sand-100 sm:flex" aria-label="Oldingi kunlar">
          ‹
        </button>
        <div ref={scroller} className="no-scrollbar flex flex-1 gap-1 overflow-x-auto scroll-smooth">
          {list.map((d, i) => {
            const key = iso(d);
            const count = counts.get(key) ?? 0;
            const weekend = d.getDay() === 0 || d.getDay() === 6;
            const dim = weekendsOnly && !weekend;
            const isSel = selected === key;
            const monthStart = i === 0 || d.getDate() === 1;
            const cell = (
              <span
                className={`flex w-11 flex-col items-center rounded-xl py-1.5 transition ${
                  isSel
                    ? "bg-forest-600 text-white"
                    : count && !dim
                      ? "hover:bg-forest-50"
                      : "opacity-40"
                }`}
              >
                <span className={`text-[10px] font-semibold uppercase ${isSel ? "text-forest-100" : weekend ? "text-clay-500" : "text-ink-mute"}`}>
                  {WD[d.getDay()]}
                </span>
                <span className="text-base font-bold leading-6">{d.getDate()}</span>
                <span className={`h-1 w-1 rounded-full ${count ? (isSel ? "bg-white" : "bg-forest-500") : "bg-transparent"}`} />
              </span>
            );
            return (
              <div key={key} className="flex shrink-0 items-end">
                {monthStart && (
                  <span className="mr-1 self-center pr-1 text-[10px] font-bold uppercase tracking-wide text-ink-mute [writing-mode:vertical-rl] rotate-180">
                    {MONTHS[d.getMonth()].slice(0, 3)}
                  </span>
                )}
                {count && !dim ? (
                  <Link href={href(key)} title={`${count} ta tur`} scroll={false}>
                    {cell}
                  </Link>
                ) : (
                  <span aria-disabled>{cell}</span>
                )}
              </div>
            );
          })}
        </div>
        <button onClick={() => scroll(1)} className="hidden h-8 w-8 shrink-0 items-center justify-center rounded-full border border-sand-200 text-ink-soft hover:bg-sand-100 sm:flex" aria-label="Keyingi kunlar">
          ›
        </button>
      </div>
    </div>
  );
}
