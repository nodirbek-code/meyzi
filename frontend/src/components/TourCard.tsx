import Link from "next/link";

import { dateLong, money } from "@/lib/format";
import type { TourCard as Tour } from "@/lib/types";

import { Cover, Icon } from "./ui";

/** Katalog kartasi: rasm (toifa, davomiylik), joylashuv, nom, keyingi sana + qolgan joy, narx + oylik, tugma. */
export function TourCard({ tour }: { tour: Tour }) {
  const nd = tour.next_departure;
  const category = tour.categories[0];
  const href = `/tours/${tour.slug}`;
  return (
    <article className="card group flex flex-col overflow-hidden transition hover:-translate-y-0.5 hover:shadow-lift">
      <Link href={href} className="relative block overflow-hidden" tabIndex={-1}>
        <Cover src={tour.cover} alt={tour.title} className="aspect-[4/3] w-full transition duration-500 group-hover:scale-[1.04]" />
        {category && (
          <span className="chip absolute left-3 top-3 bg-white/95 text-forest-700 shadow-sm">{category.name}</span>
        )}
        <span className="chip absolute right-3 top-3 bg-ink/70 text-white backdrop-blur">
          <Icon name="clock" size={12} />
          {tour.duration_days} kun
        </span>
        {tour.agency.is_platform && (
          <span className="chip absolute bottom-3 left-3 bg-sun-500 text-forest-900">★ Tavsiya</span>
        )}
      </Link>
      <div className="flex flex-1 flex-col p-4">
        <p className="flex items-center gap-1 truncate text-xs text-ink-mute">
          <Icon name="pin" size={13} className="shrink-0 text-forest-500" />
          {tour.destination.name}
        </p>
        <h3 className="mt-1.5 line-clamp-2 min-h-[2.75rem] font-sans text-[15px] font-semibold leading-snug">
          <Link href={href} className="hover:text-forest-700">
            {tour.title}
          </Link>
        </h3>
        <div className="mt-2 flex flex-wrap items-center gap-1.5 text-xs">
          {nd ? (
            <>
              <span className="inline-flex items-center gap-1 text-ink-soft">
                <Icon name="calendar" size={13} className="text-forest-500" />
                Keyingi: {dateLong(nd.date)}
              </span>
              <span className="chip bg-forest-50 px-2 py-0.5 text-forest-700">{nd.seats_left} ta o&apos;rin qoldi</span>
            </>
          ) : (
            <span className="text-ink-mute">Sana tez orada</span>
          )}
        </div>
        <div className="mt-auto pt-4">
          <div className="flex items-baseline gap-1">
            <span className="text-xl font-extrabold text-ink">{money(tour.price_uzs, "")}</span>
            <span className="text-xs text-ink-mute">so&apos;m</span>
            {tour.reviews_count > 0 && (
              <span className="ml-auto inline-flex items-center gap-0.5 text-xs font-semibold">
                <span className="text-sun-500">★</span>
                {Number(tour.rating).toFixed(1)}
              </span>
            )}
          </div>
          <span className="chip mt-1 bg-sun-100 px-2 py-0.5 font-medium text-sun-700">
            {money(tour.installment.monthly_uzs, "")} so&apos;m/oy
          </span>
          <Link href={href} className="btn-primary mt-3 w-full">
            Turni ko&apos;rish
          </Link>
        </div>
      </div>
    </article>
  );
}
