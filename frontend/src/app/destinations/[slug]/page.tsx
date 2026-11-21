import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { TourCard } from "@/components/TourCard";
import { Cover, EmptyState, SectionTitle } from "@/components/ui";
import { apiGet, apiGetOrNull } from "@/lib/api";
import { money } from "@/lib/format";
import type { Destination, Paginated, TourCard as Tour } from "@/lib/types";

type Props = { params: Promise<{ slug: string }> };
type Place = {
  id: number;
  name: string;
  slug: string;
  category_display: string;
  short_description: string;
  entry_fee_uzs: number;
  is_free: boolean;
};

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const d = await apiGetOrNull<Destination>(`/catalog/destinations/${(await params).slug}/`);
  return d ? { title: d.name, description: d.short_description } : {};
}

export default async function DestinationPage({ params }: Props) {
  const { slug } = await params;
  const d = await apiGetOrNull<Destination>(`/catalog/destinations/${slug}/`);
  if (!d) notFound();
  const [tours, places] = await Promise.all([
    apiGet<Paginated<Tour>>("/tours/", { query: { destination: slug, page_size: 12 } }),
    apiGet<Paginated<Place>>("/catalog/places/", { query: { destination: slug, page_size: 30 } }),
  ]);
  const minPrice = tours.results.length ? Math.min(...tours.results.map((t) => t.price_uzs)) : null;

  return (
    <>
      <section className="relative isolate overflow-hidden">
        <Cover src={d.cover_image} alt="" className="absolute inset-0 -z-20 h-full w-full" />
        <div className="absolute inset-0 -z-10 bg-gradient-to-t from-forest-900/90 via-forest-900/40 to-forest-900/30" aria-hidden />
        <div className="container-lz py-20 sm:py-28">
          <nav className="mb-4 text-sm text-forest-50/70">
            <Link href="/destinations" className="hover:text-white">‹ Yo&apos;nalishlar</Link>
          </nav>
          <p className="text-xs font-bold uppercase tracking-[0.3em] text-sun-300">{d.region}</p>
          <h1 className="mt-2 text-4xl text-white sm:text-5xl">{d.name}</h1>
          <p className="mt-3 max-w-2xl text-lg text-forest-50/90">{d.short_description}</p>
          <div className="mt-5 flex flex-wrap gap-2 text-sm">
            <span className="chip bg-white/15 py-1.5 text-white backdrop-blur">{tours.count} ta tur</span>
            {minPrice !== null && <span className="chip bg-white/15 py-1.5 text-white backdrop-blur">{money(minPrice)} dan</span>}
            {places.count > 0 && <span className="chip bg-white/15 py-1.5 text-white backdrop-blur">{places.count} ta diqqatga sazovor joy</span>}
          </div>
        </div>
      </section>

      <div className="container-lz space-y-16 py-12">
        {d.description && <p className="prose-lz max-w-3xl whitespace-pre-line text-base">{d.description}</p>}

        <section>
          <SectionTitle eyebrow="Turlar" title={`${d.name} turlari`} />
          {tours.results.length ? (
            <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
              {tours.results.map((t) => (
                <TourCard key={t.id} tour={t} />
              ))}
            </div>
          ) : (
            <EmptyState title="Hozircha tur yo'q" text="Tez orada yangi turlar qo'shiladi." />
          )}
        </section>

        {places.results.length > 0 && (
          <section>
            <SectionTitle eyebrow="Diqqatga sazovor joylar" title="Nimani ko'rish kerak" />
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {places.results.map((p) => (
                <div key={p.id} className="card p-5">
                  <span className="chip bg-sky-50 text-sky-700">{p.category_display}</span>
                  <h3 className="mt-2 font-sans text-base font-semibold">{p.name}</h3>
                  {p.short_description && <p className="mt-1 text-sm text-ink-soft">{p.short_description}</p>}
                  <p className="mt-3 text-xs text-ink-mute">Kirish: {p.is_free ? "bepul" : money(p.entry_fee_uzs)}</p>
                </div>
              ))}
            </div>
          </section>
        )}
      </div>
    </>
  );
}
