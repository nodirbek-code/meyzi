import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { BookingWidget } from "@/components/BookingWidget";
import { Gallery } from "@/components/Gallery";
import { ShareButton } from "@/components/ShareButton";
import { TourCard } from "@/components/TourCard";
import { Badge, Cover, Icon } from "@/components/ui";
import { apiGet, apiGetOrNull } from "@/lib/api";
import { dateLong, duration, HOTEL_KIND, LANGUAGE_NAMES, money, POLICY_LABEL, time } from "@/lib/format";
import { getUser } from "@/lib/session";
import type { Paginated, Review, TourCard as Tour, TourDetail } from "@/lib/types";

type Props = { params: Promise<{ slug: string }> };

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const tour = await apiGetOrNull<TourDetail>(`/tours/${(await params).slug}/`);
  return tour ? { title: tour.title, description: tour.short_description || tour.description.slice(0, 160) } : {};
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section>
      <h2 className="mb-4 text-xl sm:text-2xl">{title}</h2>
      {children}
    </section>
  );
}

function CheckList({ items, kind }: { items: string[]; kind: "yes" | "no" | "dot" }) {
  const mark = {
    yes: <span className="mt-0.5 text-forest-600">✓</span>,
    no: <span className="mt-0.5 text-clay-500">✕</span>,
    dot: <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-sun-500" />,
  }[kind];
  return (
    <ul className="space-y-2">
      {items.map((it) => (
        <li key={it} className="flex gap-2.5 text-sm text-ink-soft">
          {mark}
          <span>{it}</span>
        </li>
      ))}
    </ul>
  );
}

function mapUrl(t: TourDetail) {
  if (t.meeting_map_url) return t.meeting_map_url;
  if (t.meeting_latitude && t.meeting_longitude)
    return `https://yandex.uz/maps/?pt=${t.meeting_longitude},${t.meeting_latitude}&z=16&l=map`;
  return null;
}

export default async function TourPage({ params }: Props) {
  const { slug } = await params;
  const [tour, user] = await Promise.all([apiGetOrNull<TourDetail>(`/tours/${slug}/`, { revalidate: 30 }), getUser()]);
  if (!tour) notFound();
  const empty = { count: 0, next: null, previous: null, results: [] };
  const [reviews, similar] = await Promise.all([
    apiGet<Paginated<Review>>("/reviews/", { query: { tour: slug, page_size: 6 } }).catch(() => empty as Paginated<Review>),
    apiGet<Paginated<Tour>>("/tours/", { query: { category: tour.categories[0]?.slug, page_size: 5 } }).catch(
      () => empty as Paginated<Tour>,
    ),
  ]);
  const others = similar.results.filter((t) => t.id !== tour.id).slice(0, 4);
  const map = mapUrl(tour);
  const nextDate = tour.departures.find((d) => d.is_bookable);

  return (
    <div className="container-lz pb-24 pt-6 sm:pt-8 lg:pb-8">
      <Link href="/tours" className="inline-flex items-center gap-1 text-sm text-ink-mute hover:text-forest-700">
        ‹ Turlar
      </Link>

      <div className="mt-4 grid grid-cols-1 gap-8 lg:grid-cols-[1fr_380px] lg:gap-10">
        <div className="min-w-0 space-y-10">
          <Gallery media={tour.media} title={tour.title} />

          {/* Sarlavha */}
          <div>
            <div className="flex flex-wrap items-center gap-2 text-sm">
              {tour.categories.map((c) => (
                <Badge key={c.slug}>{c.name}</Badge>
              ))}
              <Link href={`/destinations/${tour.destination.slug}`} className="inline-flex items-center gap-1 text-ink-soft hover:text-forest-700">
                <Icon name="pin" size={14} className="text-forest-500" />
                {tour.destination.name}
              </Link>
            </div>
            <div className="mt-3 flex items-start justify-between gap-4">
              <h1 className="text-3xl leading-tight sm:text-4xl">{tour.title}</h1>
              <ShareButton title={tour.title} />
            </div>
            <div className="mt-4 flex flex-wrap gap-x-5 gap-y-2 text-sm text-ink-soft">
              <span className="inline-flex items-center gap-1.5">
                <Icon name="clock" size={15} className="text-forest-500" />
                {duration(tour.duration_days, tour.duration_nights)}
              </span>
              <span className="inline-flex items-center gap-1.5">
                <Icon name="users" size={15} className="text-forest-500" />
                Maks. {tour.max_group_size} kishi
              </span>
              {tour.departure_time && (
                <span className="inline-flex items-center gap-1.5">
                  <Icon name="calendar" size={15} className="text-forest-500" />
                  Ketish vaqti {time(tour.departure_time)}
                  {tour.return_time && ` — ${time(tour.return_time)}`}
                </span>
              )}
              {tour.reviews_count > 0 && (
                <span>
                  <span className="text-sun-500">★★★★★</span> <b className="text-ink">{Number(tour.rating).toFixed(1)}</b> ({tour.reviews_count} ta sharh)
                </span>
              )}
            </div>
          </div>

          {/* Uchrashuv joyi */}
          {tour.meeting_point && (
            <div className="flex gap-4 rounded-xl2 border border-sky-100 bg-sky-50 p-5">
              <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-white text-sky-500 shadow-card">
                <Icon name="pin" size={22} />
              </span>
              <div className="min-w-0">
                <p className="text-sm font-semibold text-sky-700">Uchrashuv joyi</p>
                <p className="mt-0.5 text-sm text-ink">{tour.meeting_point}</p>
                {map && (
                  <a href={map} target="_blank" rel="noopener noreferrer" className="mt-2 inline-flex items-center gap-1 text-sm font-semibold text-sky-700 hover:underline">
                    Xaritada ochish ↗
                  </a>
                )}
              </div>
            </div>
          )}

          {tour.description && (
            <Section title="Bu tur haqida">
              <div className="prose-lz whitespace-pre-line">{tour.description}</div>
            </Section>
          )}

          {tour.itinerary.length > 0 && (
            <Section title="Dastur">
              <div className="space-y-4">
                {tour.itinerary.map((day) => (
                  <div key={day.day_number} className="card p-5">
                    <h3 className="mb-4 flex items-center gap-2 font-sans text-base font-semibold">
                      <span className="rounded-lg bg-forest-600 px-2.5 py-0.5 text-xs text-white">{day.day_number}-kun</span>
                      {day.title !== `${day.day_number}-kun` && day.title}
                    </h3>
                    {day.description && <p className="text-sm text-ink-soft">{day.description}</p>}
                    {day.items.length > 0 && (
                      <ol className="relative space-y-4 border-l-2 border-forest-100 pl-5">
                        {day.items.map((it, i) => (
                          <li key={i} className="relative">
                            <span className="absolute -left-[27px] top-1 h-3 w-3 rounded-full border-2 border-white bg-forest-500 ring-2 ring-forest-100" />
                            <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
                              {it.start_time && (
                                <span className="text-xs font-bold text-forest-700">
                                  {time(it.start_time)}
                                  {it.end_time && `–${time(it.end_time)}`}
                                </span>
                              )}
                              <span className="text-sm font-medium">{it.title}</span>
                              {it.is_extra_cost && <Badge tone="gold">o&apos;z hisobidan</Badge>}
                            </div>
                            {it.description && <p className="mt-1 text-sm text-ink-soft">{it.description}</p>}
                          </li>
                        ))}
                      </ol>
                    )}
                  </div>
                ))}
              </div>
            </Section>
          )}

          {tour.guides.length > 0 && (
            <Section title={tour.guides.length > 1 ? "Gidlar" : "Gid"}>
              <div className="grid gap-3 sm:grid-cols-2">
                {tour.guides.map((g) => (
                  <Link key={g.slug} href={`/guides/${g.slug}`} className="card flex items-center gap-4 p-4 transition hover:shadow-lift">
                    <Cover src={g.photo} alt={g.display_name} className="h-14 w-14 shrink-0 overflow-hidden rounded-full" />
                    <div className="min-w-0">
                      <div className="flex items-center gap-1.5 font-semibold">
                        <span className="truncate">{g.display_name}</span>
                        {g.is_certified && <Badge tone="green">sertifikat</Badge>}
                      </div>
                      <p className="mt-0.5 text-xs text-ink-soft">
                        {g.languages.map((l) => LANGUAGE_NAMES[l] ?? l).join(", ")}
                        {g.experience_years > 0 && ` · ${g.experience_years} yil tajriba`}
                        {Number(g.rating) > 0 && ` · ★ ${Number(g.rating).toFixed(1)}`}
                      </p>
                    </div>
                  </Link>
                ))}
              </div>
            </Section>
          )}

          {tour.hotels.length > 0 && (
            <Section title="Qayerda tunaysiz">
              <div className="grid gap-3 sm:grid-cols-2">
                {tour.hotels.map((h) => (
                  <Link key={h.slug} href={`/hotels/${h.slug}`} className="card flex items-center gap-4 overflow-hidden p-0 transition hover:shadow-lift">
                    <Cover src={h.cover} alt={h.name} className="h-20 w-28 shrink-0" />
                    <div className="min-w-0 py-3 pr-4">
                      <div className="truncate font-semibold">{h.name}</div>
                      <p className="mt-0.5 text-xs text-ink-soft">
                        {h.stars ? `${"★".repeat(h.stars)} · ` : ""}
                        {HOTEL_KIND[h.kind] ?? h.kind} · {h.destination}
                      </p>
                    </div>
                  </Link>
                ))}
              </div>
            </Section>
          )}

          {(tour.included.length > 0 || tour.not_included.length > 0) && (
            <div className="grid gap-6 sm:grid-cols-2">
              {tour.included.length > 0 && (
                <div>
                  <h3 className="mb-3 font-sans text-base font-semibold">Narxga kiradi</h3>
                  <CheckList items={tour.included} kind="yes" />
                </div>
              )}
              {tour.not_included.length > 0 && (
                <div>
                  <h3 className="mb-3 font-sans text-base font-semibold">Narxga kirmaydi</h3>
                  <CheckList items={tour.not_included} kind="no" />
                </div>
              )}
            </div>
          )}

          {tour.what_to_bring.length > 0 && (
            <Section title="Nima olib borish kerak">
              <div className="rounded-xl2 bg-sun-50 p-5">
                <div className="grid gap-x-6 sm:grid-cols-2">
                  <CheckList items={tour.what_to_bring} kind="dot" />
                </div>
              </div>
            </Section>
          )}

          <Section title="Bekor qilish shartlari">
            <div className={`rounded-xl2 border-l-4 bg-white p-5 text-sm text-ink-soft shadow-card ${tour.cancellation_policy === "non_refundable" ? "border-clay-500" : "border-forest-500"}`}>
              <b className="text-ink">{POLICY_LABEL[tour.cancellation_policy]}.</b> {tour.cancellation_policy_text}
            </div>
          </Section>

          {/* Sharhlar */}
          <Section title="Sharhlar">
            {reviews.results.length ? (
              <>
                <div className="mb-4 flex items-center gap-3">
                  <span className="text-4xl font-extrabold">{Number(tour.rating).toFixed(1)}</span>
                  <span>
                    <span className="block text-sun-500">★★★★★</span>
                    <span className="text-sm text-ink-mute">{tour.reviews_count} ta sharh</span>
                  </span>
                </div>
                <div className="grid gap-4 md:grid-cols-2">
                  {reviews.results.map((r) => (
                    <div key={r.id} className="card p-5">
                      <div className="flex items-start justify-between gap-3">
                        <div className="flex items-center gap-3">
                          <span className="flex h-9 w-9 items-center justify-center rounded-full bg-forest-50 text-sm font-bold text-forest-700">
                            {r.author.slice(0, 1)}
                          </span>
                          <span>
                            <b className="block text-sm">{r.author}</b>
                            <span className="text-xs text-ink-mute">{dateLong(r.created_at.slice(0, 10), true)}</span>
                          </span>
                        </div>
                        <span className="text-sm text-sun-500">
                          {"★".repeat(r.rating)}
                          <span className="text-sand-300">{"★".repeat(5 - r.rating)}</span>
                        </span>
                      </div>
                      {r.text && <p className="mt-3 text-sm text-ink-soft">{r.text}</p>}
                      {r.agency_reply && (
                        <p className="mt-3 rounded-xl bg-sand-100 p-3 text-xs text-ink-soft">
                          <b className="text-ink">Tashkilotchi javobi:</b> {r.agency_reply}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              </>
            ) : (
              <p className="rounded-xl2 bg-sand-100 p-5 text-sm text-ink-mute">Hali sharhlar yo&apos;q. Sayohatdan keyin birinchi bo&apos;lib fikr qoldiring.</p>
            )}
          </Section>

          {/* Tashkilotchi */}
          <Section title="Tashkilotchi">
            <div className="card flex flex-wrap items-center gap-4 p-5">
              {tour.agency.logo ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img src={tour.agency.logo} alt={tour.agency.name} className="h-14 w-14 rounded-xl object-contain" />
              ) : (
                <span className="flex h-14 w-14 items-center justify-center rounded-xl bg-forest-50 text-xl font-bold text-forest-700">
                  {tour.agency.name.slice(0, 1)}
                </span>
              )}
              <div className="min-w-0 flex-1">
                <p className="flex items-center gap-1.5 font-semibold">
                  {tour.agency.name}
                  {tour.agency.is_verified && (
                    <span className="flex h-4 w-4 items-center justify-center rounded-full bg-forest-600 text-[10px] text-white" title="Tekshirilgan">
                      ✓
                    </span>
                  )}
                </p>
                {tour.agency.reviews_count > 0 ? (
                  <p className="text-sm text-ink-soft">
                    <span className="text-sun-500">★</span> {Number(tour.agency.rating).toFixed(1)} · {tour.agency.reviews_count} ta sharh
                  </p>
                ) : (
                  <p className="text-sm text-ink-mute">{tour.agency.is_verified ? "Tekshirilgan agentlik" : "Agentlik"}</p>
                )}
              </div>
              <Link href={`/tours?agency=${tour.agency.slug}`} className="btn-ghost">
                Agentlik turlari ›
              </Link>
            </div>
          </Section>
        </div>

        <aside className="min-w-0 lg:sticky lg:top-24 lg:self-start">
          <BookingWidget
            slug={tour.slug}
            departures={tour.departures}
            maxGroup={tour.max_group_size}
            user={user}
            price={tour.price_uzs}
            departureTime={tour.departure_time}
            returnTime={tour.return_time}
            rating={tour.rating}
            reviewsCount={tour.reviews_count}
            policy={tour.cancellation_policy}
          />
          {tour.price_note && <p className="mt-2 px-1 text-xs text-ink-mute">* {tour.price_note}</p>}
        </aside>
      </div>

      {/* O'xshash turlar */}
      {others.length > 0 && (
        <section className="mt-16">
          <h2 className="mb-5 text-2xl">O&apos;xshash turlar</h2>
          <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
            {others.map((t) => (
              <TourCard key={t.id} tour={t} />
            ))}
          </div>
        </section>
      )}

      {/* Mobil: pastki bron paneli */}
      <div className="fixed inset-x-0 bottom-0 z-30 border-t border-sand-200 bg-white/95 px-4 py-3 backdrop-blur lg:hidden" style={{ paddingBottom: "max(0.75rem, env(safe-area-inset-bottom))" }}>
        <div className="flex items-center justify-between gap-3">
          <div>
            <div className="text-lg font-extrabold">{money(nextDate?.price_uzs ?? tour.price_uzs)}</div>
            <div className="text-xs text-ink-mute">{nextDate ? `Keyingi: ${dateLong(nextDate.date)}` : "1 kishi uchun"}</div>
          </div>
          <a href="#bron" className="btn-primary px-6">
            Bron qilish
          </a>
        </div>
      </div>
    </div>
  );
}
