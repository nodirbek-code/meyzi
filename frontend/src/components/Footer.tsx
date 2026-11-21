import Link from "next/link";

import { BRAND } from "@/lib/brand";

import { Logo } from "./Logo";
import { Icon } from "./ui";

const COLS = [
  {
    title: "Sayohat",
    links: [
      ["/tours", "Barcha turlar"],
      ["/destinations", "Yo'nalishlar"],
      ["/guides", "Gidlar"],
      ["/hotels", "Mehmonxonalar"],
    ],
  },
  {
    title: "Hamkorlik",
    links: [
      ["/agencies", "Agentliklar uchun"],
      ["/guides/become", "Gid bo'lish"],
      ["/hotels/join", "Mehmonxonani qo'shish"],
    ],
  },
  {
    title: "Ma'lumot",
    links: [
      ["/articles", "Qo'llanmalar"],
      ["/faq", "Savol-javob"],
      ["/pages/terms", "Foydalanish shartlari"],
      ["/pages/privacy", "Maxfiylik siyosati"],
    ],
  },
];

const icon = "flex h-9 w-9 items-center justify-center rounded-full bg-white/10 text-forest-100 transition hover:bg-white/20";

export function Footer() {
  return (
    <footer className="mt-20 bg-forest-900 text-forest-100" style={{ paddingBottom: "env(safe-area-inset-bottom, 0px)" }}>
      <div className="container-lz grid gap-10 py-14 sm:grid-cols-2 lg:grid-cols-5">
        <div className="lg:col-span-2">
          <Logo light />
          <p className="mt-3 text-xs font-bold uppercase tracking-[0.2em] text-sun-300">{BRAND.tagline}</p>
          <ul className="mt-5 space-y-2 text-sm">
            <li>
              <a href={`tel:${BRAND.phone.replace(/\s/g, "")}`} className="inline-flex items-center gap-2 hover:text-white">
                <Icon name="phone" size={15} className="text-sun-300" />
                {BRAND.phone}
              </a>
            </li>
            <li>
              <a href={`mailto:${BRAND.email}`} className="inline-flex items-center gap-2 hover:text-white">
                <Icon name="mail" size={15} className="text-sun-300" />
                {BRAND.email}
              </a>
            </li>
          </ul>
          <div className="mt-5 flex gap-2">
            <a href={BRAND.telegram} className={icon} aria-label="Telegram" target="_blank" rel="noreferrer">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" aria-hidden>
                <path d="M21.5 4.3 2.9 11.5c-1.3.5-1.3 1.2-.2 1.6l4.8 1.5 1.8 5.6c.2.6.1.9.8.9.5 0 .7-.2 1-.5l2.3-2.3 4.9 3.6c.9.5 1.5.2 1.8-.8l3.2-15.1c.3-1.3-.5-1.9-1.8-1.7ZM8.6 14.3l9.3-5.9c.5-.3.9-.1.5.2l-7.9 7.2-.3 3.3-1.6-4.8Z" />
              </svg>
            </a>
            <a href={BRAND.instagram} className={icon} aria-label="Instagram" target="_blank" rel="noreferrer">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
                <rect x="3" y="3" width="18" height="18" rx="5" />
                <circle cx="12" cy="12" r="4" />
                <circle cx="17.5" cy="6.5" r="1" fill="currentColor" />
              </svg>
            </a>
          </div>
        </div>
        {COLS.map((c) => (
          <div key={c.title}>
            <h4 className="mb-4 font-sans text-xs font-bold uppercase tracking-[0.18em] text-white">{c.title}</h4>
            <ul className="space-y-2.5 text-sm">
              {c.links.map(([href, label]) => (
                <li key={href}>
                  <Link href={href} className="text-forest-100/80 transition hover:text-white">
                    {label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
      <div className="border-t border-white/10">
        <div className="container-lz flex flex-wrap justify-between gap-2 py-5 text-xs text-forest-100/60">
          <span>© {new Date().getFullYear()} {BRAND.name}. Barcha huquqlar himoyalangan.</span>
          <span>Toshkent, O&apos;zbekiston</span>
        </div>
      </div>
    </footer>
  );
}
