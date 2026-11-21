import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { apiGetOrNull } from "@/lib/api";
import { dateLong } from "@/lib/format";
import type { Page } from "@/lib/types";

type Props = { params: Promise<{ slug: string }> };

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const p = await apiGetOrNull<Page>(`/pages/${(await params).slug}/`);
  return p ? { title: p.title } : {};
}

export default async function StaticPage({ params }: Props) {
  const p = await apiGetOrNull<Page>(`/pages/${(await params).slug}/`);
  if (!p) notFound();
  return (
    <div className="container-lz py-8 sm:py-10">
      <div className="mx-auto max-w-3xl">
        <nav className="mb-2 text-sm text-ink-mute">
          <Link href="/" className="hover:text-forest-700">Bosh sahifa</Link> › {p.title}
        </nav>
        <h1 className="text-3xl sm:text-4xl">{p.title}</h1>
        <p className="mt-2 text-sm text-ink-mute">Oxirgi yangilanish: {dateLong(p.updated_at.slice(0, 10), true)}</p>
        <div className="card prose-lz mt-8 whitespace-pre-line p-6 text-base sm:p-8">{p.body}</div>
      </div>
    </div>
  );
}
