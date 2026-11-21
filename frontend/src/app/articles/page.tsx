import type { Metadata } from "next";
import Link from "next/link";

import { Cover, EmptyState } from "@/components/ui";
import { apiGet } from "@/lib/api";
import { dateLong } from "@/lib/format";
import type { ArticleCard, Paginated } from "@/lib/types";

export const metadata: Metadata = { title: "Qo'llanmalar" };

export default async function ArticlesPage() {
  const data = await apiGet<Paginated<ArticleCard>>("/articles/", { query: { page_size: 30 } });
  return (
    <div className="container-lz py-8 sm:py-10">
      <nav className="mb-2 text-sm text-ink-mute">
        <Link href="/" className="hover:text-forest-700">Bosh sahifa</Link> › Qo&apos;llanmalar
      </nav>
      <h1 className="text-3xl sm:text-4xl">Qo&apos;llanmalar</h1>
      <p className="mt-1 text-ink-soft">Sayohatga chiqishdan oldin bilish foydali bo&apos;lgan narsalar.</p>
      <div className="mt-8">
        {data.results.length ? (
          <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
            {data.results.map((a) => (
              <Link key={a.slug} href={`/articles/${a.slug}`} className="card group overflow-hidden transition hover:-translate-y-0.5 hover:shadow-lift">
                <Cover src={a.cover} alt={a.title} className="aspect-video w-full" />
                <div className="p-5">
                  <p className="text-xs text-ink-mute">
                    {dateLong(a.published_at.slice(0, 10), true)}
                    {a.destination && ` · ${a.destination.name}`}
                  </p>
                  <h2 className="mt-1 font-sans text-lg font-semibold group-hover:text-forest-700">{a.title}</h2>
                  <p className="mt-2 line-clamp-3 text-sm text-ink-soft">{a.excerpt}</p>
                  <span className="mt-3 inline-block text-sm font-semibold text-forest-600">O&apos;qish ›</span>
                </div>
              </Link>
            ))}
          </div>
        ) : (
          <EmptyState title="Qo'llanmalar tez orada" text="Jamoamiz foydali maqolalar tayyorlamoqda." />
        )}
      </div>
    </div>
  );
}
