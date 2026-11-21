"use client";

import Link from "next/link";

import { Badge } from "@/components/ui";
import { duration, money } from "@/lib/format";
import type { Paginated } from "@/lib/types";

import { ErrorText, Loading } from "./Bits";
import { useData } from "./useData";

type Row = { slug: string; title: string; status: string; price_uzs: number; duration_days: number; duration_nights: number; moderation_note: string };
export const TOUR_STATUS: Record<string, { label: string; tone: "gray" | "gold" | "green" | "red" | "blue" }> = {
  draft: { label: "Qoralama", tone: "gray" },
  pending_review: { label: "Moderatsiyada", tone: "gold" },
  published: { label: "E'lon qilingan", tone: "green" },
  rejected: { label: "Rad etilgan", tone: "red" },
  archived: { label: "Arxivda", tone: "gray" },
};

export function AgencyTours() {
  const { data, error, loading } = useData<Paginated<Row>>("/cabinet/tours?page_size=100");
  return (
    <div className="space-y-4">
      <div className="flex justify-end"><Link href="/cabinet/agency/tours/new" className="btn-gold">+ Yangi tur</Link></div>
      <ErrorText text={error} />
      {loading && <Loading />}
      {data && !data.results.length && <p className="card p-8 text-center text-sm text-ink-soft">Hali tur yo&apos;q. Birinchi turingizni yarating.</p>}
      {data?.results.map((t) => (
        <Link key={t.slug} href={`/cabinet/agency/tours/${t.slug}`} className="card flex flex-wrap items-center justify-between gap-3 p-4 transition hover:shadow-lg">
          <div>
            <div className="font-semibold">{t.title}</div>
            <div className="text-sm text-ink-soft">{duration(t.duration_days, t.duration_nights)} · {money(t.price_uzs)}</div>
            {t.status === "rejected" && t.moderation_note && <div className="mt-1 text-xs text-clay-700">Moderator: {t.moderation_note}</div>}
          </div>
          <Badge tone={TOUR_STATUS[t.status]?.tone ?? "gray"}>{TOUR_STATUS[t.status]?.label ?? t.status}</Badge>
        </Link>
      ))}
    </div>
  );
}
