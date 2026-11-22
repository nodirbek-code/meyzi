import type { Metadata } from "next";
import Link from "next/link";

import { GuideCard } from "@/components/GuideCard";
import { SimpleFilters } from "@/components/SimpleFilters";
import { EmptyState } from "@/components/ui";
import { apiGet } from "@/lib/api";
import { LANGUAGE_NAMES, SPECIALIZATIONS } from "@/lib/format";
import type { Destination, GuideCard as Guide, Paginated } from "@/lib/types";

export const metadata: Metadata = { title: "Gidlar" };
const KEYS = ["destination", "language", "specialization", "date", "max_price"];

export default async function GuidesPage({ searchParams }: { searchParams: Promise<Record<string, string | undefined>> }) {
  const sp = await searchParams;
  const query = Object.fromEntries(KEYS.filter((k) => sp[k]).map((k) => [k, sp[k] as string]));
  const [guides, destinations] = await Promise.all([
    apiGet<Paginated<Guide>>("/guides/", { query: { ...query, page_size: 30 }, revalidate: 30 }),
    apiGet<Paginated<Destination>>("/catalog/destinations/", { query: { page_size: 50 } }),
  ]);
  const today = new Date().toISOString().slice(0, 10);

  return (
    <div className="container-lz py-8 sm:py-10">
      <nav className="mb-2 text-sm text-ink-mute">
        <Link href="/" className="hover:text-forest-700">Bosh sahifa</Link> › Gidlar
      </nav>
      <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl sm:text-4xl">Shaxsiy gidlar</h1>
          <p className="mt-1 text-ink-soft">Sertifikatlangan mahalliy gidlar — yarim kun, to&apos;liq kun yoki bir necha kunga.</p>
        </div>
        <Link href="/hamkorlik?turi=gid" className="btn-ghost">
          Gid bo&apos;lmoqchimisiz? ›
        </Link>
      </div>
      <SimpleFilters
        fields={[
          { name: "destination", label: "Shahar", type: "select", options: [["", "Barchasi"], ...destinations.results.map((d) => [d.slug, d.name] as [string, string])] },
          { name: "language", label: "Til", type: "select", options: [["", "Istalgan"], ...Object.entries(LANGUAGE_NAMES)] },
          { name: "specialization", label: "Yo'nalish", type: "select", options: [["", "Istalgan"], ...Object.entries(SPECIALIZATIONS)] },
          { name: "date", label: "Bo'sh sana", type: "date", min: today },
          { name: "max_price", label: "Kunlik narx (maks.)", type: "number", placeholder: "so'm" },
        ]}
      />
      <p className="mt-6 text-sm text-ink-soft">
        <b className="text-ink">{guides.count}</b> ta gid topildi
      </p>
      <div className="mt-4">
        {guides.results.length ? (
          <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {guides.results.map((g) => (
              <GuideCard key={g.slug} guide={g} />
            ))}
          </div>
        ) : (
          <EmptyState title="Gid topilmadi" text="Boshqa sana yoki shaharni tanlab ko'ring." />
        )}
      </div>
    </div>
  );
}
