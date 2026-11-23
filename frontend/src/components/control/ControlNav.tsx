"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import type { QueueCard, StaffRole } from "@/lib/control";

/** Admin paneli menyusi: dashboard, tekshiruv bo'limlari (kutayotganlar soni bilan), Django admin. */
export function ControlNav({ queue, role }: { queue: QueueCard[]; role: StaffRole }) {
  const admin = role === "admin";
  const path = usePathname();
  const links = [
    { href: "/control", label: "Dashboard", icon: "📊", count: 0, exact: true },
    ...(admin
      ? [
          { href: "/control/manage", label: "Boshqarish", icon: "⚙️", count: 0, exact: false },
          { href: "/control/media", label: "Media (ZIP)", icon: "🖼️", count: 0, exact: false },
        ]
      : []),
    ...queue.map((q) => ({ href: `/control/queue/${q.kind}`, label: q.title, icon: q.icon, count: q.count, exact: false })),
  ];
  const active = (href: string, exact: boolean) => (exact ? path === href : path === href || path.startsWith(href + "/"));

  const item = (l: (typeof links)[number], mobile = false) => (
    <Link
      key={l.href}
      href={l.href}
      className={
        mobile
          ? `chip shrink-0 border px-3.5 py-2 text-sm ${active(l.href, l.exact) ? "border-forest-600 bg-forest-600 text-white" : "border-sand-300 bg-white text-ink-soft"}`
          : `flex items-center gap-2 rounded-xl px-3 py-2 text-sm transition ${active(l.href, l.exact) ? "bg-forest-600 font-semibold text-white" : "text-ink-soft hover:bg-sand-100"}`
      }
    >
      <span>{l.icon}</span>
      <span className="flex-1">{l.label}</span>
      {l.count > 0 && (
        <span className={`rounded-full px-2 text-xs font-bold ${active(l.href, l.exact) ? "bg-white/25" : "bg-sun-100 text-sun-700"}`}>{l.count}</span>
      )}
    </Link>
  );

  return (
    <>
      <nav className="no-scrollbar -mx-4 flex gap-2 overflow-x-auto px-4 lg:hidden">{links.map((l) => item(l, true))}</nav>
      <aside className="hidden lg:block">
        <nav className="card sticky top-24 space-y-1 p-3">
          {links.slice(0, admin ? 2 : 1).map((l) => item(l))}
          <p className="px-3 pb-1 pt-3 text-xs font-semibold uppercase tracking-wide text-ink-mute">Tekshiruv</p>
          {links.slice(admin ? 2 : 1).map((l) => item(l))}
          {admin && <div className="mt-3 border-t border-sand-200 pt-3">
            <a href="/control/admin" target="_blank" className="flex items-center gap-2 rounded-xl px-3 py-2 text-sm text-ink-soft hover:bg-sand-100">
              <span>🛠️</span>
              <span className="flex-1">Django admin ↗</span>
            </a>
          </div>}
        </nav>
      </aside>
    </>
  );
}
