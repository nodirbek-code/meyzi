"use client";

import { useEffect, useRef, useState } from "react";

/** Platforma tillari (backend: settings.LANGUAGES). Hozircha faqat o'zbekcha ishlaydi — rus va ingliz "tez kunda". */
const LANGUAGES = [
  { code: "uz", short: "UZ", name: "O'zbekcha", ready: true },
  { code: "ru", short: "RU", name: "Русский", ready: false },
  { code: "en", short: "EN", name: "English", ready: false },
] as const;

function Globe() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
      <circle cx="12" cy="12" r="9" />
      <path d="M3 12h18M12 3c2.5 2.7 2.5 15.3 0 18M12 3c-2.5 2.7-2.5 15.3 0 18" />
    </svg>
  );
}

export function LanguageSwitcher() {
  const [open, setOpen] = useState(false);
  const box = useRef<HTMLDivElement>(null);
  const current = LANGUAGES[0];

  useEffect(() => {
    if (!open) return;
    const onClick = (e: MouseEvent) => {
      if (box.current && !box.current.contains(e.target as Node)) setOpen(false);
    };
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setOpen(false);
    document.addEventListener("mousedown", onClick);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onClick);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  return (
    <div ref={box} className="relative">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-haspopup="menu"
        aria-expanded={open}
        aria-label="Tilni tanlash"
        className="inline-flex items-center gap-1 rounded-lg px-2 py-1.5 text-xs font-semibold text-ink-soft transition hover:bg-sand-100 hover:text-forest-700"
      >
        <Globe />
        {current.short}
        <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" aria-hidden className={`transition ${open ? "rotate-180" : ""}`}>
          <path d="m6 9 6 6 6-6" />
        </svg>
      </button>
      {open && (
        <div role="menu" className="absolute right-0 top-full z-50 mt-2 w-48 overflow-hidden rounded-xl border border-sand-200 bg-white py-1 shadow-lift">
          {LANGUAGES.map((l) => (
            <button
              key={l.code}
              type="button"
              role="menuitemradio"
              aria-checked={l.code === current.code}
              disabled={!l.ready}
              onClick={() => setOpen(false)}
              title={l.ready ? undefined : "Tez kunda"}
              className="flex w-full items-center justify-between gap-2 px-3 py-2 text-left text-sm enabled:hover:bg-sand-50 disabled:cursor-not-allowed"
            >
              <span className={l.ready ? "font-semibold text-ink" : "text-ink-mute"}>
                <span className="mr-2 inline-block w-6 text-xs font-bold text-ink-mute">{l.short}</span>
                {l.name}
              </span>
              {l.code === current.code ? (
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" className="text-forest-600" aria-hidden>
                  <path d="m5 12.5 4.5 4.5L19 7.5" />
                </svg>
              ) : (
                !l.ready && <span className="rounded-full bg-sand-100 px-2 py-0.5 text-[10px] font-semibold text-ink-mute">tez kunda</span>
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
