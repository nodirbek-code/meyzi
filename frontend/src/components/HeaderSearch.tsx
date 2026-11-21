"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";

import type { DestinationShort } from "@/lib/types";

/** Header'dagi qidiruv: lupa bosilganda kichik oyna — so'z yoki mashhur yo'nalish. */
export function HeaderSearch({ destinations }: { destinations: DestinationShort[] }) {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [q, setQ] = useState("");
  const box = useRef<HTMLDivElement>(null);
  const input = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!open) return;
    input.current?.focus();
    const close = (e: MouseEvent) => {
      if (box.current && !box.current.contains(e.target as Node)) setOpen(false);
    };
    const esc = (e: KeyboardEvent) => e.key === "Escape" && setOpen(false);
    document.addEventListener("mousedown", close);
    document.addEventListener("keydown", esc);
    return () => {
      document.removeEventListener("mousedown", close);
      document.removeEventListener("keydown", esc);
    };
  }, [open]);

  return (
    <div className="relative" ref={box}>
      <button
        onClick={() => setOpen((o) => !o)}
        className="rounded-lg p-2 text-ink-soft transition hover:bg-sand-100 hover:text-forest-700"
        aria-label="Qidirish"
        aria-expanded={open}
      >
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
          <circle cx="11" cy="11" r="7" />
          <path d="m20 20-3.5-3.5" />
        </svg>
      </button>
      {open && (
        <div className="card fixed inset-x-4 top-[4.5rem] z-50 p-3 sm:absolute sm:inset-x-auto sm:right-0 sm:top-12 sm:w-[24rem]">
          <form
            className="flex gap-2"
            onSubmit={(e) => {
              e.preventDefault();
              setOpen(false);
              router.push(q.trim() ? `/tours?search=${encodeURIComponent(q.trim())}` : "/tours");
            }}
          >
            <input
              ref={input}
              className="input py-2"
              placeholder="Tog', Samarqand, Chimyon…"
              value={q}
              onChange={(e) => setQ(e.target.value)}
            />
            <button className="btn-primary shrink-0 px-4 py-2">Qidirish</button>
          </form>
          {destinations.length > 0 && (
            <>
              <p className="mt-3 text-xs font-medium text-ink-mute">Mashhur yo&apos;nalishlar</p>
              <div className="mt-2 flex flex-wrap gap-1.5">
                {destinations.map((d) => (
                  <Link
                    key={d.slug}
                    href={`/tours?destination=${d.slug}`}
                    onClick={() => setOpen(false)}
                    className="chip bg-forest-50 font-medium text-forest-700 hover:bg-forest-100"
                  >
                    {d.name}
                  </Link>
                ))}
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}
