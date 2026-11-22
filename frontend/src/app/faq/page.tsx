import type { Metadata } from "next";
import Link from "next/link";

import { apiGet } from "@/lib/api";
import type { Faq } from "@/lib/types";

export const metadata: Metadata = { title: "Savol-javob" };

export default async function FaqPage() {
  const items = await apiGet<Faq[]>("/faq/");
  return (
    <div className="container-lz py-8 sm:py-10">
      <div className="mx-auto max-w-3xl">
        <nav className="mb-2 text-sm text-ink-mute">
          <Link href="/" className="hover:text-forest-700">Bosh sahifa</Link> › Savol-javob
        </nav>
        <h1 className="text-3xl sm:text-4xl">Savol-javob</h1>
        <div className="mt-8 divide-y divide-sand-200 rounded-xl2 border border-sand-200 bg-white shadow-card">
          {items.map((f) => (
            <details key={f.id} className="group px-5 py-4 sm:px-6">
              <summary className="flex cursor-pointer list-none items-center justify-between gap-4 font-semibold [&::-webkit-details-marker]:hidden">
                {f.question}
                <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-forest-50 text-forest-600 transition group-open:rotate-45">
                  +
                </span>
              </summary>
              <p className="mt-3 whitespace-pre-line text-sm leading-relaxed text-ink-soft">{f.answer}</p>
            </details>
          ))}
        </div>
      </div>
    </div>
  );
}
