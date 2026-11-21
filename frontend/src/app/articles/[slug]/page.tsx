import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { ShareButton } from "@/components/ShareButton";
import { TourCard } from "@/components/TourCard";
import { Cover } from "@/components/ui";
import { apiGetOrNull } from "@/lib/api";
import { dateLong } from "@/lib/format";
import type { Article } from "@/lib/types";

type Props = { params: Promise<{ slug: string }> };

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const a = await apiGetOrNull<Article>(`/articles/${(await params).slug}/`);
  return a ? { title: a.title, description: a.excerpt } : {};
}

export default async function ArticlePage({ params }: Props) {
  const a = await apiGetOrNull<Article>(`/articles/${(await params).slug}/`);
  if (!a) notFound();
  return (
    <article className="container-lz py-8 sm:py-10">
      <div className="mx-auto max-w-3xl">
        <Link href="/articles" className="text-sm text-ink-mute hover:text-forest-700">
          ‹ Qo&apos;llanmalar
        </Link>
        <p className="mt-6 text-sm text-ink-mute">
          {dateLong(a.published_at.slice(0, 10), true)}
          {a.destination && (
            <>
              {" · "}
              <Link href={`/destinations/${a.destination.slug}`} className="text-forest-600 hover:underline">
                {a.destination.name}
              </Link>
            </>
          )}
        </p>
        <h1 className="mt-2 text-3xl leading-tight sm:text-4xl">{a.title}</h1>
        {a.excerpt && <p className="mt-4 text-lg text-ink-soft">{a.excerpt}</p>}
        <div className="mt-5">
          <ShareButton title={a.title} />
        </div>
      </div>
      {a.cover && <Cover src={a.cover} alt={a.title} className="mx-auto mt-8 aspect-[2/1] w-full max-w-5xl rounded-xl2" />}
      <div className="prose-lz mx-auto mt-10 max-w-3xl whitespace-pre-line text-base">{a.body}</div>
      {a.tours.length > 0 && (
        <section className="mx-auto mt-16 max-w-5xl">
          <h2 className="mb-5 text-2xl">Maqolada tilga olingan turlar</h2>
          <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {a.tours.map((t) => (
              <TourCard key={t.id} tour={t} />
            ))}
          </div>
        </section>
      )}
    </article>
  );
}
