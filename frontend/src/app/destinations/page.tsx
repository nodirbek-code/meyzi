import type { Metadata } from "next";
import Link from "next/link";

import { Cover } from "@/components/ui";
import { apiGet } from "@/lib/api";
import type { Destination, Paginated } from "@/lib/types";

export const metadata: Metadata = { title: "Yo'nalishlar" };

export default async function DestinationsPage() {
  const data = await apiGet<Paginated<Destination>>("/catalog/destinations/", { query: { page_size: 100 } });
  return (
    <div className="container-lz py-8 sm:py-10">
      <nav className="mb-2 text-sm text-ink-mute">
        <Link href="/" className="hover:text-forest-700">Bosh sahifa</Link> › Yo&apos;nalishlar
      </nav>
      <h1 className="text-3xl sm:text-4xl">Yo&apos;nalishlar</h1>
      <p className="mt-1 text-ink-soft">O&apos;zbekiston bo&apos;ylab — tog&apos;lardan qadimiy shaharlargacha.</p>
      <div className="mt-8 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
        {data.results.map((d) => (
          <Link key={d.slug} href={`/destinations/${d.slug}`} className="group relative overflow-hidden rounded-xl2 shadow-card">
            <Cover src={d.cover_image} alt={d.name} className="aspect-[4/3] w-full transition duration-500 group-hover:scale-105" />
            <div className="absolute inset-0 bg-gradient-to-t from-forest-900/90 via-forest-900/20 to-transparent" />
            <div className="absolute inset-x-0 bottom-0 p-5">
              <p className="text-xs font-semibold uppercase tracking-wide text-sun-300">{d.region}</p>
              <h2 className="mt-0.5 text-2xl text-white">{d.name}</h2>
              <p className="mt-1 line-clamp-2 text-sm text-forest-50/85">{d.short_description}</p>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
