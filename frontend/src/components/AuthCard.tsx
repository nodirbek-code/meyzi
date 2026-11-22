import Link from "next/link";
import type { ReactNode } from "react";

import { BRAND } from "@/lib/brand";

import { Logo } from "./Logo";
import { Icon } from "./ui";

const PERKS = [
  { icon: "shield", text: "Faqat tekshirilgan agentliklar va gidlar" },
  { icon: "calendar", text: "Bronlaringiz va sayohat sanalari bir joyda" },
  { icon: "telegram", text: "Telefon raqam Telegram bot orqali tasdiqlanadi" },
] as const;

/** Kirish sahifalari: chapda tabiat paneli (katta ekranda), o'ngda forma. */
export function AuthCard({ title, subtitle, children }: { title: string; subtitle?: string; children: ReactNode }) {
  return (
    <div className="container-lz py-8 sm:py-14">
      <div className="mx-auto grid max-w-5xl overflow-hidden rounded-[1.5rem] border border-sand-200 bg-white shadow-lift lg:grid-cols-[1fr_1.05fr]">
        <div className="nature-bg relative hidden flex-col justify-between p-10 text-white lg:flex">
          <Link href="/" aria-label="Bosh sahifa">
            <Logo light />
          </Link>
          <div>
            <h2 className="text-3xl leading-tight text-white">{BRAND.tagline}</h2>
            <ul className="mt-6 space-y-3 text-sm text-forest-50/90">
              {PERKS.map((p) => (
                <li key={p.text} className="flex items-center gap-3">
                  <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-white/15">
                    <Icon name={p.icon} size={16} />
                  </span>
                  {p.text}
                </li>
              ))}
            </ul>
          </div>
        </div>
        <div className="p-6 sm:p-10">
          <h1 className="text-2xl sm:text-3xl">{title}</h1>
          {subtitle && <p className="mt-1.5 text-sm text-ink-soft">{subtitle}</p>}
          <div className="mt-7">{children}</div>
        </div>
      </div>
    </div>
  );
}

export function FormError({ message }: { message: string }) {
  if (!message) return null;
  return (
    <p className="rounded-xl bg-clay-50 px-3 py-2 text-sm text-clay-700" role="alert">
      {message}
    </p>
  );
}

export function Divider({ text = "yoki" }: { text?: string }) {
  return (
    <div className="flex items-center gap-3 text-xs text-ink-mute">
      <span className="h-px flex-1 bg-sand-200" />
      {text}
      <span className="h-px flex-1 bg-sand-200" />
    </div>
  );
}

export function TermsNote() {
  return (
    <p className="text-center text-xs text-ink-mute">
      Davom etib, siz{" "}
      <Link href="/pages/terms" className="text-forest-600 hover:underline">
        foydalanish shartlari
      </Link>{" "}
      va{" "}
      <Link href="/pages/privacy" className="text-forest-600 hover:underline">
        maxfiylik siyosati
      </Link>
      ni qabul qilasiz.
    </p>
  );
}
