"use client";

import { useState } from "react";

import type { TourDetail } from "@/lib/types";

import { Cover } from "./ui";

/** Katta rasm/video + o'q tugmalar, hisoblagich va kichik rasmlar tasmasi. */
export function Gallery({ media, title }: { media: TourDetail["media"]; title: string }) {
  const [i, setI] = useState(0);
  if (!media.length) return <Cover src={null} alt={title} className="aspect-[16/9] w-full rounded-xl2" />;
  const cur = media[i];
  const go = (d: number) => setI((x) => (x + d + media.length) % media.length);
  const arrow =
    "absolute top-1/2 flex h-10 w-10 -translate-y-1/2 items-center justify-center rounded-full bg-white/90 text-lg text-ink shadow-card transition hover:bg-white";

  return (
    <div>
      <div className="relative overflow-hidden rounded-xl2 bg-forest-900">
        {cur.kind === "video" ? (
          <video key={cur.id} src={cur.file} controls className="aspect-[16/9] w-full" />
        ) : (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={cur.file} alt={cur.caption || title} className="aspect-[16/9] w-full object-cover" />
        )}
        {media.length > 1 && (
          <>
            <button onClick={() => go(-1)} className={`${arrow} left-3`} aria-label="Oldingi">
              ‹
            </button>
            <button onClick={() => go(1)} className={`${arrow} right-3`} aria-label="Keyingi">
              ›
            </button>
            <span className="absolute bottom-3 right-3 rounded-full bg-ink/70 px-2.5 py-1 text-xs font-semibold text-white">
              {i + 1} / {media.length}
            </span>
          </>
        )}
      </div>
      {media.length > 1 && (
        <div className="no-scrollbar mt-3 flex gap-2 overflow-x-auto pb-1">
          {media.map((m, idx) => (
            <button
              key={m.id}
              onClick={() => setI(idx)}
              className={`h-16 w-24 shrink-0 overflow-hidden rounded-lg border-2 transition ${idx === i ? "border-forest-600" : "border-transparent opacity-70 hover:opacity-100"}`}
              aria-label={`${idx + 1}-rasm`}
            >
              {m.kind === "video" ? (
                <span className="flex h-full items-center justify-center bg-forest-800 text-white">▶</span>
              ) : (
                // eslint-disable-next-line @next/next/no-img-element
                <img src={m.file} alt="" className="h-full w-full object-cover" />
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
