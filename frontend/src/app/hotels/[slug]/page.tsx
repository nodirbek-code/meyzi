import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { HotelRooms } from "@/components/HotelRooms";
import { ShareButton } from "@/components/ShareButton";
import { Badge, Cover, Icon } from "@/components/ui";
import { apiGet, apiGetOrNull } from "@/lib/api";
import { AMENITIES, dateLong, HOTEL_KIND, time } from "@/lib/format";
import { getUser } from "@/lib/session";
import type { HotelDetail, Paginated, Review } from "@/lib/types";

type Props = { params: Promise<{ slug: string }>; searchParams: Promise<Record<string, string | undefined>> };

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const h = await apiGetOrNull<HotelDetail>(`/hotels/${(await params).slug}/`);
  return h ? { title: h.name } : {};
}

export default async function HotelPage({ params, searchParams }: Props) {
  const { slug } = await params;
  const sp = await searchParams;
  const [h, user] = await Promise.all([apiGetOrNull<HotelDetail>(`/hotels/${slug}/`, { revalidate: 30 }), getUser()]);
  if (!h) notFound();
  const reviews = await apiGet<Paginated<Review>>(`/hotels/${slug}/reviews/`);
  const photos = h.images.filter((i) => i.kind !== "video");
  const videos = h.images.filter((i) => i.kind === "video");
  const map = h.latitude && h.longitude ? `https://yandex.uz/maps/?pt=${h.longitude},${h.latitude}&z=16&l=map` : null;

  return (
    <div className="container-lz py-6 sm:py-8">
      <Link href="/hotels" className="text-sm text-ink-mute hover:text-forest-700">
        ‹ Mehmonxonalar
      </Link>

      {/* Rasmlar mozaikasi */}
      <div className="mt-4 grid gap-3 sm:grid-cols-[2fr_1fr]">
        <Cover src={photos[0]?.image ?? null} alt={h.name} className="aspect-[16/10] w-full overflow-hidden rounded-xl2" />
        <div className="hidden grid-rows-2 gap-3 sm:grid">
          <Cover src={photos[1]?.image ?? null} alt={`${h.name} 2`} className="h-full w-full overflow-hidden rounded-xl2" />
          <Cover src={photos[2]?.image ?? null} alt={`${h.name} 3`} className="h-full w-full overflow-hidden rounded-xl2" />
        </div>
      </div>
      {(photos.length > 3 || videos.length > 0) && (
        <div className="mt-3 flex gap-3 overflow-x-auto pb-1">
          {videos.map((v) => (
            <video key={v.id} src={v.image} controls playsInline preload="metadata" className="h-40 shrink-0 rounded-xl bg-ink" />
          ))}
          {photos.slice(3).map((p) => (
            <Cover key={p.id} src={p.image} alt={p.caption || h.name} className="h-40 w-56 shrink-0 overflow-hidden rounded-xl" />
          ))}
        </div>
      )}

      <div className="mt-8 grid grid-cols-1 gap-8 lg:grid-cols-[1fr_1.1fr] lg:gap-10">
        <div className="min-w-0 space-y-8">
          <div>
            <div className="flex flex-wrap items-center gap-2 text-sm">
              <Badge>{HOTEL_KIND[h.kind]}</Badge>
              {h.stars && <span className="text-sun-500">{"★".repeat(h.stars)}</span>}
              {h.reviews_count > 0 && (
                <span>
                  <b>{Number(h.rating).toFixed(1)}</b> <span className="text-ink-mute">({h.reviews_count} ta sharh)</span>
                </span>
              )}
            </div>
            <div className="mt-2 flex items-start justify-between gap-4">
              <h1 className="text-3xl leading-tight sm:text-4xl">{h.name}</h1>
              <ShareButton title={h.name} />
            </div>
            <p className="mt-2 flex items-center gap-1 text-sm text-ink-soft">
              <Icon name="pin" size={14} className="text-forest-500" />
              {h.address}, {h.destination.name}
              {map && (
                <a href={map} target="_blank" rel="noopener noreferrer" className="ml-2 font-semibold text-sky-700 hover:underline">
                  Xaritada ↗
                </a>
              )}
            </p>
          </div>

          {h.description && <p className="prose-lz whitespace-pre-line">{h.description}</p>}

          <div className="grid gap-3 sm:grid-cols-2">
            <div className="card p-5">
              <span className="label">Kirish</span>
              <p className="text-lg font-bold">{time(h.check_in_time)} dan</p>
            </div>
            <div className="card p-5">
              <span className="label">Chiqish</span>
              <p className="text-lg font-bold">{time(h.check_out_time)} gacha</p>
            </div>
          </div>

          {h.amenities.length > 0 && (
            <section>
              <h2 className="mb-3 text-xl">Qulayliklar</h2>
              <div className="flex flex-wrap gap-2">
                {h.amenities.map((a) => (
                  <span key={a} className="chip bg-forest-50 py-1.5 text-forest-700">
                    ✓ {AMENITIES[a] ?? a}
                  </span>
                ))}
              </div>
            </section>
          )}

          <section>
            <h2 className="mb-3 text-xl">Bekor qilish shartlari</h2>
            <div className="rounded-xl2 border-l-4 border-forest-500 bg-white p-5 text-sm text-ink-soft shadow-card">{h.cancellation_policy_text}</div>
          </section>

          <section>
            <h2 className="mb-3 text-xl">Sharhlar</h2>
            {reviews.results.length ? (
              <div className="space-y-3">
                {reviews.results.map((r) => (
                  <div key={r.id} className="card p-5 text-sm">
                    <div className="flex items-start justify-between gap-3">
                      <span>
                        <b className="block">{r.author}</b>
                        <span className="text-xs text-ink-mute">{dateLong(r.created_at.slice(0, 10), true)}</span>
                      </span>
                      <span className="text-sun-500">{"★".repeat(r.rating)}</span>
                    </div>
                    {r.text && <p className="mt-2 text-ink-soft">{r.text}</p>}
                  </div>
                ))}
              </div>
            ) : (
              <p className="rounded-xl2 bg-sand-100 p-5 text-sm text-ink-mute">Hali sharhlar yo&apos;q.</p>
            )}
          </section>
        </div>

        <div className="min-w-0">
          <h2 className="mb-3 text-xl">Xonalar</h2>
          <HotelRooms slug={h.slug} user={user} initial={{ check_in: sp.check_in ?? "", check_out: sp.check_out ?? "", guests: sp.guests ?? "2" }} />
        </div>
      </div>
    </div>
  );
}
