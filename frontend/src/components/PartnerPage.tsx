import type { ReactNode } from "react";

import { Icon } from "./ui";

/** Hamkorlik sahifalari (gid bo'lish, mehmonxona qo'shish): chapda afzalliklar, o'ngda forma. */
export function PartnerPage({
  eyebrow = "Hamkorlik",
  title,
  text,
  perks,
  children,
}: {
  eyebrow?: string;
  title: string;
  text: string;
  perks: string[];
  children: ReactNode;
}) {
  return (
    <div className="container-lz py-8 sm:py-12">
      <div className="grid gap-8 lg:grid-cols-[1fr_1.6fr] lg:gap-12">
        <aside className="lg:sticky lg:top-24 lg:self-start">
          <div className="nature-bg rounded-[1.5rem] p-7 text-white sm:p-9">
            <p className="text-xs font-bold uppercase tracking-[0.3em] text-sun-300">{eyebrow}</p>
            <h1 className="mt-3 text-3xl leading-tight text-white">{title}</h1>
            <p className="mt-3 text-forest-50/90">{text}</p>
            <ul className="mt-6 space-y-3 text-sm">
              {perks.map((p) => (
                <li key={p} className="flex gap-3">
                  <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-white/15">
                    <Icon name="check" size={14} />
                  </span>
                  <span className="text-forest-50/90">{p}</span>
                </li>
              ))}
            </ul>
          </div>
        </aside>
        <div className="min-w-0">{children}</div>
      </div>
    </div>
  );
}
