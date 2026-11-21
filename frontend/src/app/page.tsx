import Link from "next/link";

import { DateStrip, type CalendarDay } from "@/components/DateStrip";
import { SearchBar } from "@/components/SearchBar";
import { TourCard } from "@/components/TourCard";
import { Cover, Icon, MoreLink, SectionTitle } from "@/components/ui";
import { apiGet } from "@/lib/api";
import { BRAND } from "@/lib/brand";
import type { ArticleCard, Category, Destination, Features, Paginated, Review, TourCard as Tour } from "@/lib/types";

export const revalidate = 60;

const TRUST = [
  { icon: "shield", title: "Tekshirilgan agentliklar", text: "Har bir hamkor hujjatlari tekshirilgandan keyingina platformaga qo'shiladi." },
  { icon: "leaf", title: "Mahalliy tajriba", text: "Turlarni o'z yurtini yaxshi biladigan tajribali gidlar va tashkilotchilar olib boradi." },
  { icon: "lock", title: "Xavfsiz bron", text: "Narx, dastur va bekor qilish shartlari to'lovdan oldin ochiq ko'rinadi." },
] as const;

/** Toifa plitkalari uchun tabiat ranglari (navbat bilan) */
const TILE_TONES = [
  "from-forest-500 to-forest-800",
  "from-sun-500 to-clay-500",
  "from-sky-500 to-forest-700",
  "from-clay-500 to-clay-700",
  "from-forest-400 to-sky-700",
  "from-sun-600 to-forest-700",
];

async function safe<T>(p: Promise<T>, fallback: T): Promise<T> {
  try {
    return await p;
  } catch {
    return fallback;
  }
}

export default async function HomePage() {
  const empty = { count: 0, next: null, previous: null, results: [] };
  const [tours, categories, destinations, features, articles, calendar, reviews] = await Promise.all([
    apiGet<Paginated<Tour>>("/tours/", { query: { page_size: 8 } }),
    apiGet<Category[]>("/tours/categories/"),
    apiGet<Paginated<Destination>>("/catalog/destinations/", { query: { page_size: 50 } }),
    apiGet<Features>("/features/"),
    safe(apiGet<Paginated<ArticleCard>>("/articles/", { query: { page_size: 3 } }), empty as Paginated<ArticleCard>),
    safe(apiGet<CalendarDay[]>("/tours/calendar/", { query: { days: 45 } }), []),
    safe(apiGet<Paginated<Review>>("/reviews/", { query: { page_size: 6, rating: 5 } }), empty as Paginated<Review>),
  ]);

  // Toifalar bo'yicha bo'limlar (turi bor birinchi 3 ta toifa)
  const topCategories = categories.filter((c) => c.tours_count > 0).slice(0, 3);
  const byCategory = await Promise.all(
    topCategories.map((c) =>
      safe(apiGet<Paginated<Tour>>("/tours/", { query: { category: c.slug, page_size: 4 } }), empty as Paginated<Tour>),
    ),
  );

  const heroImage =
    tours.results.find((t) => t.cover)?.cover ?? destinations.results.find((d) => d.cover_image)?.cover_image ?? null;

  return (
    <>
      {/* ---------- Hero ---------- */}
      <section className="relative isolate overflow-hidden">
        <Cover src={heroImage} alt="" className="absolute inset-0 -z-20 h-full w-full" />
        <div className="absolute inset-0 -z-10 bg-gradient-to-b from-forest-900/55 via-forest-900/45 to-forest-900/85" aria-hidden />
        <div className="container-lz pb-24 pt-16 text-center sm:pb-28 sm:pt-24">
          <p className="text-xs font-bold uppercase tracking-[0.3em] text-sun-300">{BRAND.name}</p>
          <h1 className="mx-auto mt-3 max-w-4xl text-4xl leading-tight text-white sm:text-5xl lg:text-6xl">
            O&apos;zbekiston tabiatini kashf eting
          </h1>
          <p className="mx-auto mt-4 max-w-2xl text-base text-forest-50/90 sm:text-lg">
            Tog&apos; yo&apos;laklari, toza ko&apos;llar va Ipak yo&apos;li shaharlari — tekshirilgan mahalliy agentliklarning
            turlarini toping va onlayn bron qiling.
          </p>
          <div className="mx-auto mt-8 max-w-4xl text-left">
            <SearchBar destinations={destinations.results} categories={categories} />
          </div>
        </div>
        <div className="absolute inset-x-0 bottom-0 border-t border-white/10 bg-forest-900/50 backdrop-blur">
          <div className="container-lz flex flex-wrap justify-center gap-x-8 gap-y-1 py-3 text-xs font-medium text-white sm:text-sm">
            {TRUST.map((t) => (
              <span key={t.title} className="inline-flex items-center gap-1.5">
                <Icon name={t.icon} size={15} className="text-sun-300" />
                {t.title}
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* ---------- Sana tasmasi ---------- */}
      <section className="container-lz relative z-10 mt-8">
        <DateStrip calendar={calendar} />
      </section>

      {/* ---------- Mashhur turlar ---------- */}
      <section className="container-lz pt-14">
        <SectionTitle eyebrow="Siz uchun tanlangan" title="Mashhur turlar" action={<MoreLink href="/tours">Barcha turlar</MoreLink>} />
        {tours.results.length ? (
          <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
            {tours.results.map((t) => (
              <TourCard key={t.id} tour={t} />
            ))}
          </div>
        ) : (
          <p className="text-ink-soft">Turlar tez orada qo&apos;shiladi.</p>
        )}
      </section>

      {/* ---------- Toifalar bo'yicha ---------- */}
      {/* katalog kichik bo'lsa (hammasi yuqorida ko'rinib turibdi) — takrorlamaymiz */}
      {tours.count > tours.results.length &&
        topCategories.map((c, i) =>
        byCategory[i].results.length ? (
          <section key={c.slug} className="container-lz pt-14">
            <div className="mb-5 flex items-end justify-between gap-3">
              <h2 className="flex items-center gap-2 text-xl sm:text-2xl">
                <span aria-hidden>{c.icon}</span>
                {c.name}
              </h2>
              <MoreLink href={`/tours?category=${c.slug}`}>Barcha turlarni ko&apos;rish</MoreLink>
            </div>
            <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
              {byCategory[i].results.map((t) => (
                <TourCard key={t.id} tour={t} />
              ))}
            </div>
          </section>
        ) : null,
      )}

      {/* ---------- Toifa plitkalari ---------- */}
      {categories.length > 0 && (
        <section className="container-lz pt-14">
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
            {categories.map((c, i) => (
              <Link
                key={c.slug}
                href={`/tours?category=${c.slug}`}
                className={`group relative flex min-h-[7.5rem] flex-col justify-end overflow-hidden rounded-xl2 bg-gradient-to-br p-4 text-white shadow-card transition hover:-translate-y-0.5 hover:shadow-lift ${TILE_TONES[i % TILE_TONES.length]}`}
              >
                <span className="absolute right-3 top-3 text-2xl opacity-90 transition group-hover:scale-110" aria-hidden>
                  {c.icon}
                </span>
                <span className="font-display text-base font-bold">{c.name}</span>
                <span className="text-xs text-white/80">{c.tours_count} ta tur</span>
              </Link>
            ))}
          </div>
        </section>
      )}

      {/* ---------- Yo'nalishlar ---------- */}
      {destinations.results.length > 0 && (
        <section className="container-lz pt-20">
          <SectionTitle
            eyebrow="Yo'nalishlar"
            title="Qayerga borasiz?"
            action={<MoreLink href="/destinations">Barcha yo&apos;nalishlar</MoreLink>}
          />
          <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
            {destinations.results.slice(0, 8).map((d, i) => (
              <Link
                key={d.slug}
                href={`/destinations/${d.slug}`}
                className={`group relative overflow-hidden rounded-xl2 shadow-card ${i === 0 ? "col-span-2 md:row-span-2" : ""}`}
              >
                <Cover
                  src={d.cover_image}
                  alt={d.name}
                  className={`w-full transition duration-500 group-hover:scale-105 ${i === 0 ? "h-56 md:h-[29rem]" : "h-48 md:h-56"}`}
                />
                <div className="absolute inset-0 bg-gradient-to-t from-forest-900/90 via-forest-900/10 to-transparent" />
                <div className="absolute bottom-0 p-4">
                  <h3 className={`text-white ${i === 0 ? "text-2xl" : "text-lg"}`}>{d.name}</h3>
                  <p className="line-clamp-2 text-xs text-forest-50/85">{d.short_description}</p>
                </div>
              </Link>
            ))}
          </div>
        </section>
      )}

      {/* ---------- Nima uchun biz ---------- */}
      <section className="container-lz pt-20">
        <SectionTitle
          center
          eyebrow="Nima uchun biz"
          title={`${BRAND.name} haqida`}
          text="O'zbekiston bo'ylab tekshirilgan mahalliy agentliklarning turlarini bir joyga yig'amiz: hafta oxiri tog' sayohatlaridan tortib ko'p kunlik ekspeditsiyalargacha."
        />
        <div className="grid gap-5 md:grid-cols-3">
          {TRUST.map((t) => (
            <div key={t.title} className="card p-6 text-center">
              <span className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-forest-50 text-forest-600">
                <Icon name={t.icon} size={24} />
              </span>
              <h3 className="mt-4 font-sans text-base font-semibold">{t.title}</h3>
              <p className="mt-2 text-sm text-ink-soft">{t.text}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ---------- Sharhlar ---------- */}
      {reviews.results.length > 0 && (
        <section className="container-lz pt-20">
          <SectionTitle center eyebrow="Sharhlar" title="Sayohatchilar fikri" />
          <div className="grid gap-5 md:grid-cols-3">
            {reviews.results.map((r) => (
              <figure key={r.id} className="card flex flex-col p-6">
                <div className="text-sun-500" aria-label={`${r.rating} yulduz`}>{"★".repeat(r.rating)}</div>
                <blockquote className="mt-3 line-clamp-5 flex-1 text-sm text-ink-soft">&ldquo;{r.text}&rdquo;</blockquote>
                <figcaption className="mt-5 flex items-center gap-3">
                  <span className="flex h-9 w-9 items-center justify-center rounded-full bg-forest-50 text-sm font-bold text-forest-700">
                    {r.author.slice(0, 1)}
                  </span>
                  <span className="min-w-0">
                    <span className="block text-sm font-semibold">{r.author}</span>
                    {r.tour_title && <span className="block truncate text-xs text-ink-mute">{r.tour_title}</span>}
                  </span>
                </figcaption>
              </figure>
            ))}
          </div>
        </section>
      )}

      {/* ---------- Gidlar va mehmonxonalar ---------- */}
      <section className="container-lz grid gap-5 pt-20 md:grid-cols-2">
        {[
          { href: "/guides", emoji: "🧭", title: "Shaxsiy gid", text: "Sertifikatlangan gidni yarim kun, to'liq kun yoki bir necha kunga bron qiling.", tone: "bg-forest-50" },
          { href: "/hotels", emoji: "🏡", title: "Mehmonxonalar", text: "Tog' etagidagi mehmon uylaridan shahar mehmonxonalarigacha — bo'sh xonalar va narxlar.", tone: "bg-sun-50" },
        ].map((b) => (
          <Link key={b.href} href={b.href} className={`group flex items-center gap-5 rounded-xl2 border border-sand-200 p-6 transition hover:shadow-lift ${b.tone}`}>
            <span className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl bg-white text-3xl shadow-card">{b.emoji}</span>
            <span>
              <span className="block font-display text-xl font-bold group-hover:text-forest-700">{b.title}</span>
              <span className="mt-1 block text-sm text-ink-soft">{b.text}</span>
            </span>
          </Link>
        ))}
      </section>

      {/* ---------- Qo'llanmalar ---------- */}
      {articles.results.length > 0 && (
        <section className="container-lz pt-20">
          <SectionTitle eyebrow="Qo'llanmalar" title="Sayohatga tayyorgarlik" action={<MoreLink href="/articles">Hammasi</MoreLink>} />
          <div className="grid gap-5 md:grid-cols-3">
            {articles.results.map((a) => (
              <Link key={a.slug} href={`/articles/${a.slug}`} className="card group overflow-hidden">
                <Cover src={a.cover} alt={a.title} className="aspect-video w-full" />
                <div className="p-5">
                  <h3 className="font-sans text-base font-semibold group-hover:text-forest-700">{a.title}</h3>
                  <p className="mt-1 line-clamp-2 text-sm text-ink-soft">{a.excerpt}</p>
                </div>
              </Link>
            ))}
          </div>
        </section>
      )}

      {/* ---------- Tez kunda: AI marshrut va to'lov usullari ---------- */}
      <section className="container-lz pt-20">
        <div className="grid gap-5 md:grid-cols-2">
          <div className="card p-6">
            <span className="chip bg-sun-100 text-sun-700">{features.ai_route.status_text}</span>
            <h3 className="mt-3 text-xl">AI marshrut</h3>
            <p className="mt-2 text-sm text-ink-soft">{features.ai_route.description}</p>
          </div>
          <div className="card p-6">
            <h3 className="text-xl">To&apos;lov usullari</h3>
            <p className="mt-1 text-sm text-ink-soft">O&apos;zbekistonda har kuni ishlatiladigan xizmatlar orqali.</p>
            <div className="mt-4 flex flex-wrap gap-3">
              {features.payments.map((p) => (
                <div key={p.code} className="flex items-center gap-2 rounded-xl border border-sand-200 px-4 py-2.5">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  {p.logo ? <img src={p.logo} alt={p.name} className="h-6" /> : <span className="font-semibold">{p.name}</span>}
                  {!p.enabled && <span className="text-xs text-ink-mute">{p.status_text}</span>}
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ---------- Savolingiz bormi? ---------- */}
      <section className="container-lz pt-20">
        <div className="flex flex-col gap-6 rounded-xl2 bg-forest-900 p-8 text-white md:flex-row md:items-center md:justify-between md:p-10">
          <div>
            <h2 className="text-2xl text-white">Savolingiz bormi?</h2>
            <p className="mt-2 text-forest-100/80">To&apos;lashdan oldin so&apos;rang — jamoamiz javob beradi.</p>
            <p className="mt-1 text-sm text-forest-100/60">{BRAND.email}</p>
          </div>
          <div className="flex flex-wrap gap-3">
            <a href={`tel:${BRAND.phone.replace(/\s/g, "")}`} className="btn-light">
              <Icon name="phone" size={16} />
              {BRAND.phone}
            </a>
            <a href={BRAND.telegram} target="_blank" rel="noreferrer" className="btn bg-sky-500 text-white hover:bg-sky-700">
              <Icon name="telegram" size={16} />
              Telegramda yozish
            </a>
          </div>
        </div>
      </section>

      {/* ---------- CTA ---------- */}
      <section className="nature-bg mt-20 -mb-20">
        <div className="container-lz py-16 text-center sm:py-20">
          <h2 className="text-3xl text-white sm:text-4xl">Sayohatga tayyormisiz?</h2>
          <p className="mx-auto mt-3 max-w-xl text-forest-50/90">Mahalliy agentliklarning turlarini ko&apos;ring va bir necha daqiqada onlayn bron qiling.</p>
          <Link href="/tours" className="btn-light mt-7 px-8 py-3 text-base">
            Barcha turlar
          </Link>
        </div>
      </section>
    </>
  );
}
