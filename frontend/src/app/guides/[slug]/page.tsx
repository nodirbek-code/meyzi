import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { GuideRequestForm } from "@/components/GuideRequestForm";
import { ShareButton } from "@/components/ShareButton";
import { Badge, Cover, Icon } from "@/components/ui";
import { apiGet, apiGetOrNull } from "@/lib/api";
import { dateLong, LANGUAGE_NAMES, money, SPECIALIZATIONS } from "@/lib/format";
import { getUser } from "@/lib/session";
import type { GuideDetail, Paginated, Review } from "@/lib/types";

type Props = { params: Promise<{ slug: string }> };

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const g = await apiGetOrNull<GuideDetail>(`/guides/${(await params).slug}/`);
  return g ? { title: `${g.display_name} — gid` } : {};
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section>
      <h2 className="mb-4 text-xl sm:text-2xl">{title}</h2>
      {children}
    </section>
  );
}

export default async function GuidePage({ params }: Props) {
  const { slug } = await params;
  const [g, user] = await Promise.all([apiGetOrNull<GuideDetail>(`/guides/${slug}/`, { revalidate: 30 }), getUser()]);
  if (!g) notFound();
  const [busy, reviews] = await Promise.all([
    apiGet<{ busy_dates: string[] }>(`/guides/${slug}/busy-dates/`, { revalidate: false }),
    apiGet<Paginated<Review>>(`/guides/${slug}/reviews/`),
  ]);
  const cityName = Object.fromEntries(g.destinations.map((d) => [d.slug, d.name]));
  const meetingPoints = g.meeting_points ?? [];

  return (
    <div className="container-lz pb-24 pt-6 sm:pt-8 lg:pb-8">
      <Link href="/guides" className="text-sm text-ink-mute hover:text-forest-700">
        ‹ Gidlar
      </Link>

      <div className="mt-4 grid grid-cols-1 gap-8 lg:grid-cols-[1fr_400px] lg:gap-10">
        <div className="min-w-0 space-y-10">
          {/* Sarlavha */}
          <div className="card overflow-hidden">
            <div className="nature-bg h-28" />
            <div className="flex flex-wrap items-start gap-5 px-6 pb-6">
              <Cover src={g.photo} alt={g.display_name} className="relative z-10 -mt-14 h-28 w-28 shrink-0 overflow-hidden rounded-full border-4 border-white shadow-card" />
              <div className="min-w-0 flex-1 pt-3">
                <h1 className="text-3xl">{g.display_name}</h1>
                <p className="mt-1 flex items-center gap-1 text-sm text-ink-soft">
                  <Icon name="pin" size={14} className="text-forest-500" />
                  {g.destinations.map((d) => d.name).join(", ")} · {g.experience_years} yil tajriba
                </p>
                <div className="mt-2 flex flex-wrap items-center gap-2">
                  {g.is_certified && <Badge>✓ Sertifikatlangan</Badge>}
                  {g.reviews_count > 0 && (
                    <span className="text-sm">
                      <span className="text-sun-500">★</span> <b>{Number(g.rating).toFixed(1)}</b>{" "}
                      <span className="text-ink-mute">({g.reviews_count} ta sharh)</span>
                    </span>
                  )}
                </div>
              </div>
              <div className="pt-3">
                <ShareButton title={g.display_name} />
              </div>
            </div>
          </div>

          {g.bio && (
            <Section title="Gid haqida">
              <p className="prose-lz whitespace-pre-line">{g.bio}</p>
            </Section>
          )}

          <div className="grid gap-5 sm:grid-cols-2">
            <div className="card p-5">
              <h3 className="label">Tillar</h3>
              <div className="flex flex-wrap gap-1.5">
                {g.languages.map((l) => (
                  <span key={l} className="chip bg-sky-50 text-sky-700">
                    {LANGUAGE_NAMES[l] ?? l}
                  </span>
                ))}
              </div>
            </div>
            <div className="card p-5">
              <h3 className="label">Yo&apos;nalishlar</h3>
              <p className="text-sm">{g.specializations.map((s) => SPECIALIZATIONS[s] ?? s).join(", ") || "—"}</p>
            </div>
          </div>

          <Section title="Narxlar">
            <div className="grid gap-3 sm:grid-cols-3">
              {(
                [
                  ["Yarim kun", "4 soat", g.price_half_day_uzs],
                  ["To'liq kun", "8 soat", g.price_full_day_uzs],
                  ["Ko'p kunlik", "1 kun uchun", g.price_per_day_uzs],
                ] as const
              ).map(([l, h, v]) => (
                <div key={l} className="card p-5">
                  <div className="text-sm font-semibold">{l}</div>
                  <div className="text-xs text-ink-mute">{h}</div>
                  <div className="mt-2 text-xl font-extrabold">{money(v)}</div>
                </div>
              ))}
            </div>
            <p className="mt-3 text-xs text-ink-mute">
              Guruh 5 kishidan oshsa — +{g.group_surcharge_percent}%. Maksimal guruh: {g.max_group_size} kishi.
            </p>
          </Section>

          {/* Uchrashuv joylari */}
          <Section title="Uchrashuv joylari">
            {meetingPoints.length ? (
              <div className="grid gap-3 sm:grid-cols-2">
                {meetingPoints.map((p) => (
                  <div key={p.id} className="flex gap-3 rounded-xl2 border border-sky-100 bg-sky-50 p-4">
                    <Icon name="pin" size={20} className="mt-0.5 shrink-0 text-sky-500" />
                    <div className="min-w-0 text-sm">
                      <p className="font-semibold">{p.name}</p>
                      <p className="text-xs text-ink-soft">
                        {cityName[p.destination] ?? p.destination} · {p.address}
                      </p>
                      <a
                        href={`https://yandex.uz/maps/?pt=${p.longitude},${p.latitude}&z=16&l=map`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="mt-1 inline-block text-xs font-semibold text-sky-700 hover:underline"
                      >
                        Xaritada ochish ↗
                      </a>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="rounded-xl2 bg-sand-100 p-4 text-sm text-ink-soft">Gid hali uchrashuv joylarini belgilamagan.</p>
            )}
            <p className="mt-2 text-xs text-ink-mute">Bron qilishda shu joylardan birini tanlaysiz.</p>
          </Section>

          <Section title="Bekor qilish shartlari">
            <div className="rounded-xl2 border-l-4 border-forest-500 bg-white p-5 text-sm text-ink-soft shadow-card">
              <ul className="space-y-1.5">
                <li>✓ 48 soatdan oldin — 100% qaytariladi</li>
                <li>✓ 24–48 soat — 50% · 12–24 soat — 25% · 12 soatdan kam — qaytarilmaydi</li>
                <li>✓ Gid bekor qilsa yoki kelmasa — 100% qaytariladi</li>
              </ul>
            </div>
          </Section>

          <Section title="Sharhlar">
            {reviews.results.length ? (
              <div className="grid gap-4 md:grid-cols-2">
                {reviews.results.map((r) => (
                  <div key={r.id} className="card p-5">
                    <div className="flex items-start justify-between gap-3">
                      <span>
                        <b className="block text-sm">{r.author}</b>
                        <span className="text-xs text-ink-mute">{dateLong(r.created_at.slice(0, 10), true)}</span>
                      </span>
                      <span className="text-sm text-sun-500">{"★".repeat(r.rating)}</span>
                    </div>
                    {r.text && <p className="mt-3 text-sm text-ink-soft">{r.text}</p>}
                  </div>
                ))}
              </div>
            ) : (
              <p className="rounded-xl2 bg-sand-100 p-5 text-sm text-ink-mute">Hali sharhlar yo&apos;q.</p>
            )}
          </Section>
        </div>

        <aside className="min-w-0 lg:sticky lg:top-24 lg:self-start">
          <GuideRequestForm
            slug={g.slug}
            destinations={g.destinations}
            languages={g.languages}
            maxGroup={g.max_group_size}
            busyDates={busy.busy_dates}
            meetingPoints={meetingPoints}
            user={user}
          />
        </aside>
      </div>

      <div className="fixed inset-x-0 bottom-0 z-30 border-t border-sand-200 bg-white/95 px-4 py-3 backdrop-blur lg:hidden" style={{ paddingBottom: "max(0.75rem, env(safe-area-inset-bottom))" }}>
        <div className="flex items-center justify-between gap-3">
          <div>
            <div className="text-lg font-extrabold">{money(g.price_full_day_uzs)}</div>
            <div className="text-xs text-ink-mute">to&apos;liq kun</div>
          </div>
          <a href="#bron" className="btn-primary px-6">
            Bron qilish
          </a>
        </div>
      </div>
    </div>
  );
}
