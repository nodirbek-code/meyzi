import type { Metadata } from "next";
import Link from "next/link";

import { DateStrip, type CalendarDay } from "@/components/DateStrip";
import { Pagination } from "@/components/Pagination";
import { TourCard } from "@/components/TourCard";
import { SortSelect, TourFilters } from "@/components/TourFilters";
import { EmptyState } from "@/components/ui";
import { apiGet } from "@/lib/api";
import { dateLong, money } from "@/lib/format";
import type { Category, Destination, Paginated, TourCard as Tour } from "@/lib/types";

export const metadata: Metadata = { title: "Turlar" };

const PAGE_SIZE = 12;
const KEYS = [
  "search",
  "destination",
  "category",
  "agency",
  "min_price",
  "max_price",
  "min_days",
  "max_days",
  "cancellation_policy",
  "date",
  "ordering",
];

export default async function ToursPage({ searchParams }: { searchParams: Promise<Record<string, string | undefined>> }) {
  const sp = await searchParams;
  const params = Object.fromEntries(KEYS.filter((k) => sp[k]).map((k) => [k, sp[k] as string]));
  const page = Math.max(1, Number(sp.page) || 1);
  const { date, ordering, ...calendarFilters } = params; // sana tasmasi — boshqa filtrlar bo'yicha
  void date;
  void ordering;

  const [tours, categories, destinations, calendar] = await Promise.all([
    apiGet<Paginated<Tour>>("/tours/", { query: { ...params, page, page_size: PAGE_SIZE }, revalidate: 30 }),
    apiGet<Category[]>("/tours/categories/"),
    apiGet<Paginated<Destination>>("/catalog/destinations/", { query: { page_size: 50 } }),
    apiGet<CalendarDay[]>("/tours/calendar/", { query: { ...calendarFilters, days: 60 }, revalidate: 30 }).catch(() => []),
  ]);

  const category = categories.find((c) => c.slug === params.category);
  const destination = destinations.results.find((d) => d.slug === params.destination);
  const title = category ? `${category.name} turlari` : destination ? `${destination.name} turlari` : "Barcha turlar";

  // Faol filtrlar — har birini alohida olib tashlash mumkin
  const without = (...keys: string[]) => {
    const q = new URLSearchParams(Object.entries(params).filter(([k]) => !keys.includes(k)));
    return `/tours${q.size ? `?${q}` : ""}`;
  };
  const chips: { label: string; href: string }[] = [];
  if (params.search) chips.push({ label: `«${params.search}»`, href: without("search") });
  if (destination) chips.push({ label: destination.name, href: without("destination") });
  if (category) chips.push({ label: category.name, href: without("category") });
  if (params.date) chips.push({ label: dateLong(params.date), href: without("date") });
  if (params.min_price || params.max_price)
    chips.push({
      label: `${params.min_price ? money(params.min_price, "") : "0"} – ${params.max_price ? money(params.max_price) : "∞"}`,
      href: without("min_price", "max_price"),
    });
  if (params.min_days || params.max_days)
    chips.push({
      label: params.min_days === params.max_days ? `${params.min_days} kun` : `${params.min_days || 1}${params.max_days ? `–${params.max_days}` : "+"} kun`,
      href: without("min_days", "max_days"),
    });
  if (params.cancellation_policy === "free") chips.push({ label: "Bepul bekor qilish", href: without("cancellation_policy") });

  const baseQuery = new URLSearchParams(Object.entries(params).filter(([k]) => k !== "date")).toString();

  return (
    <div className="container-lz py-8 sm:py-10">
      <nav className="mb-2 text-sm text-ink-mute" aria-label="Yo'l">
        <Link href="/" className="hover:text-forest-700">Bosh sahifa</Link> <span aria-hidden>›</span> <span>Turlar</span>
      </nav>
      <h1 className="text-3xl sm:text-4xl">{title}</h1>

      {/* Tezkor toifalar */}
      <div className="no-scrollbar -mx-4 mt-5 flex gap-2 overflow-x-auto px-4 sm:mx-0 sm:flex-wrap sm:px-0">
        <Link
          href={without("category")}
          className={`chip shrink-0 border px-3.5 py-2 text-sm ${!category ? "border-forest-600 bg-forest-600 text-white" : "border-sand-300 bg-white text-ink-soft hover:border-forest-400"}`}
        >
          Hammasi
        </Link>
        {categories.map((c) => {
          const on = c.slug === params.category;
          const q = new URLSearchParams({ ...params, category: c.slug });
          return (
            <Link
              key={c.slug}
              href={on ? without("category") : `/tours?${q}`}
              className={`chip shrink-0 border px-3.5 py-2 text-sm ${on ? "border-forest-600 bg-forest-600 text-white" : "border-sand-300 bg-white text-ink-soft hover:border-forest-400"}`}
            >
              <span aria-hidden>{c.icon}</span>
              {c.name}
            </Link>
          );
        })}
      </div>

      <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-[280px_1fr] lg:gap-8">
        <aside className="lg:sticky lg:top-24 lg:self-start">
          <TourFilters destinations={destinations.results} categories={categories} />
        </aside>

        <div className="min-w-0 space-y-5">
          <DateStrip calendar={calendar} selected={params.date} days={60} baseQuery={baseQuery} />

          <div className="flex flex-wrap items-center justify-between gap-3">
            <p className="text-sm text-ink-soft">
              <b className="text-ink">{tours.count}</b> ta tur topildi
            </p>
            <SortSelect />
          </div>

          {chips.length > 0 && (
            <div className="flex flex-wrap items-center gap-2">
              {chips.map((c) => (
                <Link key={c.label} href={c.href} className="chip bg-forest-50 py-1.5 text-forest-700 hover:bg-forest-100">
                  {c.label}
                  <span aria-label="olib tashlash" className="text-forest-500">✕</span>
                </Link>
              ))}
              <Link href="/tours" className="text-xs font-semibold text-clay-500 hover:underline">
                Hammasini tozalash
              </Link>
            </div>
          )}

          {tours.results.length ? (
            <div className="grid gap-5 sm:grid-cols-2 xl:grid-cols-3">
              {tours.results.map((t) => (
                <TourCard key={t.id} tour={t} />
              ))}
            </div>
          ) : (
            <EmptyState
              title="Hech narsa topilmadi"
              text="Filtrlarni o'zgartirib ko'ring yoki boshqa sanani tanlang."
              action={<Link href="/tours" className="btn-primary">Barcha turlar</Link>}
            />
          )}
          <Pagination page={page} count={tours.count} pageSize={PAGE_SIZE} basePath="/tours" params={params} />
        </div>
      </div>
    </div>
  );
}
