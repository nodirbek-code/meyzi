"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const TABS = [
  { href: "/account", label: "Bronlarim", match: (p: string) => p === "/account" || p.startsWith("/account/bookings") },
  { href: "/account/profile", label: "Profil", match: (p: string) => p.startsWith("/account/profile") },
];

export function AccountTabs() {
  const path = usePathname();
  return (
    <nav className="flex rounded-xl bg-sand-100 p-1 text-sm font-semibold">
      {TABS.map((t) => (
        <Link
          key={t.href}
          href={t.href}
          className={`rounded-lg px-4 py-2 transition ${t.match(path) ? "bg-white text-forest-700 shadow-card" : "text-ink-soft hover:text-forest-700"}`}
        >
          {t.label}
        </Link>
      ))}
    </nav>
  );
}
