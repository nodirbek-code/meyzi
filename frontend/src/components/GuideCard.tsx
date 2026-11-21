import Link from "next/link";

import { LANGUAGE_NAMES, money, SPECIALIZATIONS } from "@/lib/format";
import type { GuideCard as Guide } from "@/lib/types";

import { Cover, Icon } from "./ui";

export function GuideCard({ guide: g }: { guide: Guide }) {
  const href = `/guides/${g.slug}`;
  return (
    <article className="card group flex flex-col overflow-hidden transition hover:-translate-y-0.5 hover:shadow-lift">
      <div className="nature-bg relative h-20">
        {g.is_certified && (
          <span className="chip absolute right-3 top-3 bg-white/95 text-forest-700">✓ Sertifikatlangan</span>
        )}
      </div>
      <div className="-mt-10 flex flex-1 flex-col px-5 pb-5">
        <Cover src={g.photo} alt={g.display_name} className="relative z-10 h-20 w-20 overflow-hidden rounded-full border-4 border-white shadow-card" />
        <h2 className="mt-3 font-sans text-lg font-semibold">
          <Link href={href} className="hover:text-forest-700">
            {g.display_name}
          </Link>
        </h2>
        <p className="flex items-center gap-1 text-xs text-ink-mute">
          <Icon name="pin" size={13} className="shrink-0 text-forest-500" />
          {g.destinations.map((d) => d.name).join(", ")} · {g.experience_years} yil tajriba
        </p>
        {g.reviews_count > 0 && (
          <p className="mt-1 text-xs">
            <span className="text-sun-500">★</span> <b>{Number(g.rating).toFixed(1)}</b> <span className="text-ink-mute">({g.reviews_count})</span>
          </p>
        )}
        <div className="mt-3 flex flex-wrap gap-1.5">
          {g.languages.map((l) => (
            <span key={l} className="chip bg-sky-50 font-medium text-sky-700">
              {LANGUAGE_NAMES[l] ?? l}
            </span>
          ))}
        </div>
        {g.specializations.length > 0 && (
          <p className="mt-2 line-clamp-2 text-xs text-ink-soft">{g.specializations.map((s) => SPECIALIZATIONS[s] ?? s).join(" · ")}</p>
        )}
        <div className="mt-auto pt-4">
          <div className="flex items-baseline gap-1">
            <span className="text-xl font-extrabold">{money(g.price_full_day_uzs, "")}</span>
            <span className="text-xs text-ink-mute">so&apos;m / to&apos;liq kun</span>
          </div>
          <p className="text-xs text-ink-mute">yarim kun — {money(g.price_half_day_uzs)}</p>
          <Link href={href} className="btn-primary mt-3 w-full">
            Profilni ko&apos;rish
          </Link>
        </div>
      </div>
    </article>
  );
}
