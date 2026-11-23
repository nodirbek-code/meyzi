import Image from "next/image";
import Link from "next/link";

import { DateStrip, type CalendarDay } from "@/components/DateStrip";
import { HeroSlides, type HeroSlide } from "@/components/HeroSlides";
import { AppIcon } from "@/components/Logo";
import { SearchBar } from "@/components/SearchBar";
import { TourCard } from "@/components/TourCard";
import { Cover, Icon, MoreLink, SectionTitle } from "@/components/ui";
import { apiGet } from "@/lib/api";
import { BRAND } from "@/lib/brand";
import type { ArticleCard, Category, Destination, Features, Paginated, Review, TourCard as Tour } from "@/lib/types";

// Build paytida emas, so'rov kelganda render qilinadi (build vaqtida API hali ishlamasligi mumkin)
export const dynamic = "force-dynamic";

const COIN_STEPS = [
  { title: "Sayohat qiling", text: "Meyzi orqali sayohat turini tanlang va bron qiling." },
  { title: "Coin to'plang", text: "Sayohatingiz yakunlangach, hisobingizga coin qo'shiladi." },
  { title: "Mukofotlarga ega bo'ling", text: "Yig'ilgan coinlar evaziga maxsus imtiyozlarni qo'lga kiriting." },
];

const CARD_STEPS = [
  { title: "A'zolikni qo'lga kiriting", text: "Karta kamida 3 ta sayohat qilgan foydalanuvchilarga beriladi." },
  { title: "Maxsus maqomga ega bo'ling", text: "Karta egasi Meyzi hamjamiyatining faol a'zosi hisoblanadi." },
  { title: "Ko'proq imkoniyatlar", text: "Maxsus takliflar, hamkorlar chegirmalari va a'zolik imtiyozlari." },
  { title: "Coins to'plang", text: "Har bir sayohat orqali Meyzi Coins yig'ishda davom eting." },
];

const CARD_PERKS = [
  "Maxsus a'zolik maqomi",
  "Meyzi Coins bonus tizimi",
  "Hamkorlardan chegirmalar",
  "Faqat karta egalari uchun takliflar",
  "Membership imtiyozlari",
];

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

  // Hero: yo'nalishlar rasmlari almashib turadi — avval admin "asosiy sahifada" deb belgilaganlar, ko'pi bilan 5 ta
  const withCover = destinations.results.filter((d) => d.cover_image);
  const featured = withCover.filter((d) => d.is_featured);
  const heroSlides: HeroSlide[] = (featured.length >= 2 ? featured : withCover).slice(0, 5).map((d) => ({
    src: d.cover_image as string,
    name: d.name,
    href: `/destinations/${d.slug}`,
  }));
  const tourCover = tours.results.find((t) => t.cover)?.cover;
  if (!heroSlides.length && tourCover) heroSlides.push({ src: tourCover, name: "", href: "" });

  return (
    <>
      {/* ---------- Hero ---------- */}
      <section className="relative isolate overflow-hidden">
        <HeroSlides slides={heroSlides} />
        <div className="absolute inset-0 -z-10 bg-gradient-to-b from-forest-900/55 via-forest-900/45 to-forest-900/85" aria-hidden />
        <div className="container-lz pb-24 pt-16 text-center sm:pb-28 sm:pt-24">
          <h1 className="mx-auto max-w-4xl text-4xl leading-tight text-white sm:text-5xl lg:text-6xl">
            O&apos;zbekistonni yangicha kashf eting
          </h1>
          <p className="mx-auto mt-4 max-w-2xl text-base text-forest-50/90 sm:text-lg">
            Unutilmas sayohatlar, betakror manzillar va yangi sarguzashtlar sizni kutmoqda. O&apos;zingizga mos yo&apos;nalishni
            tanlang, sayohat qiling va har bir safaringiz uchun Meyzi Coins to&apos;plang.
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

        {/* Bonus tizimi: Meyzi Coins + Meyzi Membership Card */}
        <div className="mt-5 grid gap-5 lg:grid-cols-2">
          {/* Meyzi Coins */}
          <div className="card flex flex-col overflow-hidden border-sun-200 bg-gradient-to-br from-sun-50 via-white to-white">
            <div className="flex-1 p-6 sm:p-8">
              <div className="flex items-center gap-3">
                <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-sun-300 to-sun-500 text-lg font-extrabold text-white shadow-card" aria-hidden>
                  M
                </span>
                <h3 className="font-sans text-xl font-bold">Meyzi Coins</h3>
              </div>
              <p className="mt-4 text-sm text-ink-soft">
                Meyzi orqali sayohat qilgan sari to&apos;playdigan bonus ballaringiz. Har bir amalga oshirilgan sayohat hisobingizga
                qo&apos;shimcha coin olib keladi. Ularni Meyzi hamkorlarining maxsus takliflari, chegirmalar va boshqa imtiyozlarga
                almashtirishingiz mumkin.
              </p>
              <ol className="mt-5 space-y-3">
                {COIN_STEPS.map((step, i) => (
                  <li key={step.title} className="flex gap-3 rounded-2xl bg-white/80 p-3.5 ring-1 ring-sun-100">
                    <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-sun-100 text-sm font-bold text-sun-700">
                      {i + 1}
                    </span>
                    <span>
                      <span className="block text-sm font-semibold">{step.title}</span>
                      <span className="mt-0.5 block text-xs text-ink-soft">{step.text}</span>
                    </span>
                  </li>
                ))}
              </ol>
              <p className="mt-5 font-display text-lg italic text-sun-700">Har bir sayohat — yangi taassurot va yangi imkoniyat!</p>
            </div>
            <p className="border-t border-sun-100 bg-sun-50/60 px-6 py-3 text-xs text-ink-mute sm:px-8">
              Meyzi Coins — pul emas, platforma ichidagi bonus birliklari. Ularni naqd pulga aylantirib yoki boshqa foydalanuvchiga
              o&apos;tkazib bo&apos;lmaydi.
            </p>
          </div>

          {/* Meyzi Membership Card */}
          <div className="flex flex-col overflow-hidden rounded-xl2 bg-[linear-gradient(150deg,#0d2a47_0%,#06192b_55%,#040f1b_100%)] text-white shadow-lift">
            <div className="flex-1 p-6 sm:p-8">
              <div className="flex flex-col gap-5 sm:flex-row sm:items-center">
                <Image
                  src="/brand/meyzi-card.webp"
                  alt="Meyzi Membership Card"
                  width={640}
                  height={412}
                  className="w-44 shrink-0 -rotate-6 rounded-[0.9rem] shadow-[0_18px_40px_-12px_rgba(0,0,0,0.7)] ring-1 ring-white/10 sm:w-48"
                />
                <div>
                  <h3 className="font-sans text-xl font-bold text-white">Meyzi Membership Card</h3>
                  <p className="mt-2 text-sm text-slate-300">
                    Faol sayohatchilar uchun maxsus a&apos;zolik kartasi: sayohatlar davomida qo&apos;shimcha imtiyozlar, bonuslar va
                    maxsus takliflar.
                  </p>
                </div>
              </div>
              <ol className="mt-6 grid gap-3 sm:grid-cols-2">
                {CARD_STEPS.map((step, i) => (
                  <li key={step.title} className="flex gap-3 rounded-2xl bg-white/[0.06] p-3.5 ring-1 ring-white/10">
                    <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-slate-100 to-slate-400 text-sm font-bold text-[#06192b]">
                      {i + 1}
                    </span>
                    <span>
                      <span className="block text-sm font-semibold text-white">{step.title}</span>
                      <span className="mt-0.5 block text-xs text-slate-300">{step.text}</span>
                    </span>
                  </li>
                ))}
              </ol>
              <ul className="mt-5 flex flex-wrap gap-2">
                {CARD_PERKS.map((perk) => (
                  <li key={perk} className="flex items-center gap-1.5 rounded-full bg-white/10 px-3 py-1 text-xs font-medium text-slate-100">
                    <Icon name="check" size={13} />
                    {perk}
                  </li>
                ))}
              </ul>
            </div>
            <p className="border-t border-white/10 bg-white/[0.04] px-6 py-3 text-xs text-slate-300 sm:px-8">
              Meyzi Card — bu shunchaki karta emas, ko&apos;proq sayohat qiladiganlar uchun alohida imkoniyatlar dunyosi.
            </p>
          </div>
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
          <div className="card flex items-start gap-4 p-6">
            <div className="min-w-0 flex-1">
              <span className="soon-ai">{features.ai_route.status_text}</span>
              <h3 className="mt-3 text-xl">AI marshrut</h3>
              <p className="mt-2 text-sm text-ink-soft">{features.ai_route.description}</p>
            </div>
            <Image
              src="/brand/meyzi-ai.webp"
              alt="Meyzi AI — sun'iy intellekt yordamchisi"
              width={480}
              height={480}
              className="h-24 w-24 shrink-0 rounded-2xl object-cover shadow-card ring-1 ring-sand-200 sm:h-28 sm:w-28"
            />
          </div>
          <div className="card p-6">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <h3 className="text-xl">To&apos;lov usullari</h3>
              {features.payments.some((p) => !p.enabled) && <span className="soon-pay">Tez kunda</span>}
            </div>
            <p className="mt-1 text-sm text-ink-soft">O&apos;zbekistonda har kuni ishlatiladigan xizmatlar orqali.</p>
            <div className="mt-4 grid grid-cols-3 gap-3">
              {features.payments.map((p) => (
                <div key={p.code} className="flex h-16 items-center justify-center rounded-xl border border-sand-200 bg-white px-2 sm:px-3" title={p.name}>
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  {p.logo ? <img src={p.logo} alt={p.name} className="max-h-10 w-auto max-w-full object-contain" /> : <span className="text-sm font-semibold">{p.name}</span>}
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ---------- Mobil ilova (tez kunda) ---------- */}
      <section className="container-lz pt-20">
        <div className="grid items-center overflow-hidden rounded-[1.5rem] bg-[linear-gradient(135deg,#dfe3e4_0%,#d3d7d9_45%,#c3c6ca_100%)] md:grid-cols-2">
          <div className="p-8 sm:p-12">
            <span className="soon-brand">● Tez kunda</span>
            <div className="mt-5 flex items-center gap-3">
              <AppIcon size={52} />
              <span className="font-brand text-3xl font-semibold tracking-[0.04em]" style={{ color: BRAND.ink }}>
                {BRAND.name.charAt(0) + BRAND.name.slice(1).toLowerCase()}
              </span>
            </div>
            <h2 className="mt-5 text-3xl leading-tight sm:text-4xl" style={{ color: BRAND.ink }}>
              O&apos;zbekistonda sayohat topish endi oson
            </h2>
            <p className="mt-3 max-w-md text-ink-soft">
              Turlarni bron qiling, sayohatlaringizni kuzating va real vaqtda bildirishnomalar oling — istalgan vaqt, istalgan joyda.
            </p>
            <div className="mt-6 flex flex-wrap gap-3">
              {[
                ["App Store", "M16.4 12.6c0-2.5 2-3.7 2.1-3.8-1.2-1.7-3-1.9-3.6-2-1.5-.2-3 .9-3.8.9-.8 0-2-.9-3.3-.9-1.7 0-3.3 1-4.2 2.5-1.8 3.1-.5 7.7 1.3 10.2.9 1.2 1.9 2.6 3.2 2.6 1.3-.1 1.8-.8 3.3-.8 1.6 0 2 .8 3.4.8 1.4 0 2.3-1.3 3.1-2.5 1-1.4 1.4-2.8 1.4-2.9 0 0-2.9-1.1-2.9-4.1ZM13.9 5.1c.7-.8 1.2-2 1-3.1-1 0-2.2.7-2.9 1.5-.6.7-1.2 1.9-1 3 1.1.1 2.2-.6 2.9-1.4Z"],
                ["Google Play", "M3.6 2.3c-.3.3-.4.7-.4 1.2v17c0 .5.1.9.4 1.2l9.5-9.7-9.5-9.7Zm10.6 10.8 2.7 2.7-11.4 6.5 8.7-9.2Zm0-2.2L5.5 1.7l11.4 6.5-2.7 2.7Zm5.6-.7 2.6 1.5c.8.5.8 1.2 0 1.7l-2.6 1.5-2.9-2.4 2.9-2.3Z"],
              ].map(([store, d]) => (
                <span key={store} className="flex items-center gap-2.5 rounded-xl bg-ink px-4 py-2.5 text-white opacity-90" title="Tez kunda">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor" aria-hidden>
                    <path d={d} />
                  </svg>
                  <span className="leading-tight">
                    <span className="soon-text block text-[10px]">Tez kunda</span>
                    <span className="block text-sm font-semibold">{store}</span>
                  </span>
                </span>
              ))}
            </div>
          </div>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src="/brand/meyzi-app-mockup.jpg"
            alt={`${BRAND.name} mobil ilovasi`}
            width={1200}
            height={896}
            loading="lazy"
            className="h-full w-full object-cover md:min-h-[26rem] md:[mask-image:linear-gradient(to_right,transparent,black_20%)]"
          />
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
