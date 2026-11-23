"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { Cover, Icon } from "@/components/ui";

export type HeroSlide = { src: string; name: string; href: string };

const SHOW_MS = 7500; // har bir rasm turadigan vaqt
const FADE_MS = 1500; // ohista almashish

/**
 * Bosh sahifa hero foni: yo'nalishlar rasmlari sekin almashadi (crossfade).
 * - Birinchi rasm darhol yuklanadi, qolganlari sahifa ochilgandan keyin (tezlik uchun).
 * - "Harakatni kamaytirish" yoqilgan bo'lsa yoki tab ko'rinmasa — almashmaydi.
 */
export function HeroSlides({ slides }: { slides: HeroSlide[] }) {
  const [active, setActive] = useState(0);
  const [loadRest, setLoadRest] = useState(false);
  const many = slides.length > 1;

  useEffect(() => {
    if (!many) return;
    const t = window.setTimeout(() => setLoadRest(true), 1200);
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return () => window.clearTimeout(t);
    const id = window.setInterval(() => {
      if (!document.hidden) setActive((i) => (i + 1) % slides.length);
    }, SHOW_MS);
    return () => {
      window.clearTimeout(t);
      window.clearInterval(id);
    };
  }, [many, slides.length]);

  if (!slides.length) return <Cover src={null} alt="" className="absolute inset-0 -z-20 h-full w-full" />;

  const current = slides[active];
  return (
    <>
      <div className="absolute inset-0 -z-20" aria-hidden>
        {slides.map((s, i) =>
          i === 0 || loadRest ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              key={s.src}
              src={s.src}
              alt=""
              loading={i === 0 ? "eager" : "lazy"}
              fetchPriority={i === 0 ? "high" : "low"}
              className="absolute inset-0 h-full w-full object-cover transition-opacity ease-in-out motion-reduce:transition-none"
              style={{ opacity: i === active ? 1 : 0, transitionDuration: `${FADE_MS}ms` }}
            />
          ) : null,
        )}
      </div>

      {current.href && (
        <Link
          href={current.href}
          key={current.href}
          className="absolute bottom-16 right-4 z-10 inline-flex items-center gap-1.5 rounded-full bg-forest-900/50 px-3 py-1.5 text-xs font-medium text-white backdrop-blur transition hover:bg-forest-900/70 sm:right-6 sm:text-sm"
        >
          <Icon name="pin" size={14} className="text-sun-300" />
          {current.name}
        </Link>
      )}

      {many && (
        <div className="absolute bottom-[4.25rem] left-1/2 z-10 hidden -translate-x-1/2 gap-1.5 sm:flex" aria-hidden>
          {slides.map((s, i) => (
            <span
              key={s.src}
              className={`h-1 rounded-full bg-white transition-all duration-500 ${i === active ? "w-6 opacity-90" : "w-2 opacity-40"}`}
            />
          ))}
        </div>
      )}
    </>
  );
}
