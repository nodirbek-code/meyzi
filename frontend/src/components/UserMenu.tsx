"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";

import { api } from "@/lib/client";
import type { User } from "@/lib/types";

export function UserMenu({ user }: { user: User }) {
  const [open, setOpen] = useState(false);
  const box = useRef<HTMLDivElement>(null);
  const router = useRouter();
  const name = user.full_name || user.first_name || user.email || user.phone || "Profil";

  useEffect(() => {
    if (!open) return;
    const close = (e: MouseEvent) => box.current && !box.current.contains(e.target as Node) && setOpen(false);
    document.addEventListener("mousedown", close);
    return () => document.removeEventListener("mousedown", close);
  }, [open]);

  async function logout() {
    await api.auth("logout");
    router.push("/");
    router.refresh();
  }

  const item = "flex items-center gap-2.5 px-4 py-2.5 hover:bg-sand-100";
  return (
    <div className="relative" ref={box}>
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex items-center gap-2 rounded-xl py-1 pl-1 pr-2 text-left transition hover:bg-sand-100"
        aria-expanded={open}
      >
        <span className="flex h-8 w-8 items-center justify-center rounded-full bg-forest-600 text-sm font-bold text-white">
          {name.slice(0, 1).toUpperCase()}
        </span>
        <span className="hidden leading-tight sm:block">
          <span className="block max-w-[9rem] truncate text-sm font-semibold">{name}</span>
          <span className="block text-xs text-forest-600">Bronlarim</span>
        </span>
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="hidden text-ink-mute sm:block" aria-hidden>
          <path d="m6 9 6 6 6-6" />
        </svg>
      </button>
      {open && (
        <div className="card absolute right-0 z-50 mt-2 w-56 overflow-hidden py-1.5 text-sm" onClick={() => setOpen(false)}>
          <Link href="/account" className={item}>🗓️ Bronlarim</Link>
          <Link href="/account/profile" className={item}>👤 Profil</Link>
          {user.role !== "tourist" && (
            <Link href="/cabinet" className={`${item} font-semibold text-forest-700`}>📊 Boshqaruv paneli</Link>
          )}
          <button onClick={logout} className={`${item} w-full border-t border-sand-200 text-clay-500`}>
            ↩ Chiqish
          </button>
        </div>
      )}
    </div>
  );
}
