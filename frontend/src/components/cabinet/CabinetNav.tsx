"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

export type NavGroup = { title: string; links: { href: string; label: string; icon: string; exact?: boolean }[] };

/** Kabinet menyusi: katta ekranda chap panel, telefonda gorizontal tablar. */
export function CabinetNav({ groups }: { groups: NavGroup[] }) {
  const path = usePathname();
  const isActive = (href: string, exact?: boolean) => (exact ? path === href : path === href || path.startsWith(href + "/"));
  const all = groups.flatMap((g) => g.links);

  return (
    <>
      {/* telefon */}
      <nav className="no-scrollbar -mx-4 flex gap-2 overflow-x-auto px-4 lg:hidden">
        {all.map((l) => (
          <Link
            key={l.href}
            href={l.href}
            className={`chip shrink-0 border px-3.5 py-2 text-sm ${isActive(l.href, l.exact) ? "border-forest-600 bg-forest-600 text-white" : "border-sand-300 bg-white text-ink-soft"}`}
          >
            {l.label}
          </Link>
        ))}
      </nav>
      {/* kompyuter */}
      <aside className="hidden lg:block">
        <nav className="card sticky top-24 space-y-4 p-3">
          {groups.map((g) => (
            <div key={g.title}>
              <p className="px-3 pb-1 pt-1 text-[11px] font-bold uppercase tracking-[0.15em] text-ink-mute">{g.title}</p>
              {g.links.map((l) => {
                const on = isActive(l.href, l.exact);
                return (
                  <Link
                    key={l.href}
                    href={l.href}
                    className={`flex items-center gap-2.5 rounded-xl px-3 py-2 text-sm font-medium transition ${on ? "bg-forest-50 text-forest-700" : "text-ink-soft hover:bg-sand-100"}`}
                  >
                    <span className="w-5 text-center" aria-hidden>
                      {l.icon}
                    </span>
                    {l.label}
                  </Link>
                );
              })}
            </div>
          ))}
        </nav>
      </aside>
    </>
  );
}
