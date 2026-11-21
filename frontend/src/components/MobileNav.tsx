"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";

export function MobileNav({ items, loggedIn }: { items: { href: string; label: string }[]; loggedIn: boolean }) {
  const [open, setOpen] = useState(false);
  const path = usePathname();
  useEffect(() => setOpen(false), [path]);

  return (
    <div className="lg:hidden">
      <button
        onClick={() => setOpen(!open)}
        className="rounded-lg p-2 text-ink-soft hover:bg-sand-100"
        aria-label="Menyu"
        aria-expanded={open}
      >
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
          {open ? <path d="M6 6l12 12M18 6L6 18" /> : <path d="M4 7h16M4 12h16M4 17h16" />}
        </svg>
      </button>
      {open && (
        <nav className="card absolute inset-x-4 top-[4.25rem] z-40 flex flex-col p-2">
          {[...items, { href: "/articles", label: "Qo'llanmalar" }].map((n) => (
            <Link
              key={n.href}
              href={n.href}
              className={`rounded-lg px-4 py-3 font-medium ${path.startsWith(n.href) ? "bg-forest-50 text-forest-700" : "hover:bg-sand-100"}`}
            >
              {n.label}
            </Link>
          ))}
          {!loggedIn && (
            <div className="mt-2 grid grid-cols-2 gap-2 border-t border-sand-200 p-2 pt-3">
              <Link href="/login" className="btn-ghost">Kirish</Link>
              <Link href="/register" className="btn-primary">Ro&apos;yxatdan o&apos;tish</Link>
            </div>
          )}
        </nav>
      )}
    </div>
  );
}
