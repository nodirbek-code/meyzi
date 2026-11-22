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
      ["/hamkorlik?turi=agentlik", "Turagentliklar uchun"],
      ["/hamkorlik?turi=gid", "Gid bo'lish"],
      ["/hamkorlik?turi=mehmonxona", "Mehmonxonani qo'shish"],
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
        </div>
      </div>
    </footer>
  );
}
