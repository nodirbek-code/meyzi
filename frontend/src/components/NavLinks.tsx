"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

export function NavLinks({ items }: { items: { href: string; label: string }[] }) {
  const path = usePathname();
  return (
    <nav className="hidden items-center gap-1 text-sm font-medium lg:flex">
      {items.map((n) => {
        const active = path === n.href || path.startsWith(n.href + "/");
        return (
          <Link
            key={n.href}
            href={n.href}
            className={`relative rounded-lg px-3 py-2 transition ${
              active ? "text-forest-700" : "text-ink-soft hover:text-forest-700"
            }`}
          >
            {n.label}
            {active && <span className="absolute inset-x-3 -bottom-[13px] h-0.5 rounded-full bg-forest-600" />}
          </Link>
        );
      })}
    </nav>
  );
}
