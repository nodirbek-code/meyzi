import type { Metadata } from "next";
import Link from "next/link";

import { SimpleFilters } from "@/components/SimpleFilters";
import { Cover, EmptyState, Icon } from "@/components/ui";
import { apiGet } from "@/lib/api";
import { AMENITIES, HOTEL_KIND, money } from "@/lib/format";
import type { Destination, HotelCard, Paginated } from "@/lib/types";

export const metadata: Metadata = { title: "Mehmonxonalar" };
const KEYS = ["destination", "check_in", "check_out", "guests", "stars"];

export default async function HotelsPage({ searchParams }: { searchParams: Promise<Record<string, string | undefined>> }) {
  const sp = await searchParams;
  const query = Object.fromEntries(KEYS.filter((k) => sp[k]).map((k) => [k, sp[k] as string]));
  const hasDates = query.check_in && query.check_out;
  const [hotels, destinations] = await Promise.all([
    apiGet<Paginated<HotelCard>>("/hotels/", {
      query: hasDates ? { ...query, page_size: 30 } : { destination: query.destination, stars: query.stars, page_size: 30 },
      revalidate: 30,
    }).catch(() => null),
    apiGet<Paginated<Destination>>("/catalog/destinations/", { query: { page_size: 50 } }),
  ]);
  const today = new Date().toISOString().slice(0, 10);
  const stay = hasDates ? `?check_in=${query.check_in}&check_out=${query.check_out}&guests=${query.guests ?? 2}` : "";

  return (
    <div className="container-lz py-8 sm:py-10">
      <nav className="mb-2 text-sm text-ink-mute">
        <Link href="/" className="hover:text-forest-700">Bosh sahifa</Link> › Mehmonxonalar
      </nav>
      <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl sm:text-4xl">Qayerda qolasiz?</h1>
          <p className="mt-1 text-ink-soft">Tog&apos; etagidagi mehmon uylaridan shahar mehmonxonalarigacha.</p>
        </div>
      </div>
      <SimpleFilters
        fields={[
          { name: "destination", label: "Shahar", type: "select", options: [["", "Barchasi"], ...destinations.results.map((d) => [d.slug, d.name] as [string, string])] },
          { name: "check_in", label: "Kirish", type: "date", min: today },
          { name: "check_out", label: "Chiqish", type: "date", min: today },
          { name: "guests", label: "Mehmonlar", type: "number", placeholder: "2" },
          { name: "stars", label: "Yulduz", type: "select", options: [["", "Istalgan"], ["3", "3+"], ["4", "4+"], ["5", "5"]] },
        ]}
      />
      {!hotels && (
        <p className="mt-4 rounded-xl bg-clay-50 px-3 py-2 text-sm text-clay-700">
          Sanalar noto&apos;g&apos;ri: chiqish kirishdan keyin bo&apos;lishi kerak (30 kechagacha).
        </p>
      )}
      {hotels && (
        <p className="mt-6 text-sm text-ink-soft">
          <b className="text-ink">{hotels.count}</b> ta joy topildi
        </p>
      )}
      <div className="mt-4">
        {hotels?.results.length ? (
          <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {hotels.results.map((h) => {
              const href = `/hotels/${h.slug}${stay}`;
              return (
                <article key={h.slug} className="card group flex flex-col overflow-hidden transition hover:-translate-y-0.5 hover:shadow-lift">
                  <Link href={href} className="relative block overflow-hidden" tabIndex={-1}>
                    <Cover src={h.cover} alt={h.name} className="aspect-[4/3] w-full transition duration-500 group-hover:scale-[1.04]" />
                    <span className="chip absolute left-3 top-3 bg-white/95 text-forest-700">{HOTEL_KIND[h.kind]}</span>
                    {h.stars && <span className="chip absolute right-3 top-3 bg-ink/70 text-sun-300">{"★".repeat(h.stars)}</span>}
                  </Link>
                  <div className="flex flex-1 flex-col p-4">
                    <p className="flex items-center gap-1 truncate text-xs text-ink-mute">
                      <Icon name="pin" size={13} className="shrink-0 text-forest-500" />
                      {h.destination.name}
                    </p>
                    <h2 className="mt-1.5 font-sans text-[15px] font-semibold leading-snug">
                      <Link href={href} className="hover:text-forest-700">
                        {h.name}
                      </Link>
                    </h2>
                    <p className="mt-1 line-clamp-1 text-xs text-ink-soft">{h.amenities.slice(0, 4).map((a) => AMENITIES[a] ?? a).join(" · ")}</p>
                    {h.reviews_count > 0 && (
                      <p className="mt-1 text-xs">
                        <span className="text-sun-500">★</span> <b>{Number(h.rating).toFixed(1)}</b> <span className="text-ink-mute">({h.reviews_count})</span>
                      </p>
                    )}
                    <div className="mt-auto pt-4">
                      {h.min_price_uzs ? (
                        <div className="flex items-baseline gap-1">
                          <span className="text-xl font-extrabold">{money(h.min_price_uzs, "")}</span>
                          <span className="text-xs text-ink-mute">so&apos;m / kechadan</span>
                        </div>
                      ) : (
                        <span className="text-sm text-ink-mute">Narx tez orada</span>
                      )}
                      <Link href={href} className="btn-primary mt-3 w-full">
                        Xonalarni ko&apos;rish
                      </Link>
                    </div>
                  </div>
                </article>
              );
            })}
          </div>
        ) : hotels ? (
          <EmptyState
            title="Mos joy topilmadi"
            text={hasDates ? "Bu sanalarda bo'sh xona yo'q — boshqa sanalarni tanlang." : "Boshqa shaharni tanlab ko'ring."}
          />
        ) : null}
      </div>
    </div>
  );
}
