import type { Metadata } from "next";
import Link from "next/link";

import { AgencyApplyForm } from "@/components/AgencyApplyForm";
import { BecomeGuideForm, JoinHotelForm } from "@/components/PartnerForms";
import { Icon } from "@/components/ui";
import { apiGet } from "@/lib/api";
import { BRAND } from "@/lib/brand";
import { accountPhone } from "@/lib/phone";
import { getUser } from "@/lib/session";
import type { Destination, Paginated } from "@/lib/types";

export const metadata: Metadata = {
  title: "Hamkorlik",
  description: `Turagentlik, gid yoki mehmonxona sifatida ${BRAND.name} hamkori bo'ling.`,
};

type Turi = "agentlik" | "gid" | "mehmonxona";

const TYPES: Record<
  Turi,
  { icon: string; title: string; short: string; heading: string; text: string; perks: string[]; steps: string[] }
> = {
  agentlik: {
    icon: "🏢",
    title: "Turagentlik",
    short: "Turlaringizni joylang va bron qabul qiling",
    heading: "Turlaringizni minglab sayohatchilarga ko'rsating",
    text: "Turlar, jo'nash sanalari, joylar va bronlarni bitta kabinetda boshqarasiz.",
    perks: [
      "Turlaringiz sayohatchilar qidiradigan katalogda chiqadi",
      "Onlayn to'lov va muddatli to'lov — mijozga qulay",
      "Tasdiqlangan agentlik belgisi va reyting ishonch beradi",
      "Komissiya faqat sotilgan brondan",
    ],
    steps: ["Ariza yuboring", "Biz STIR va litsenziyani tekshiramiz", "Turlarni qo'shing — tekshiruvdan so'ng saytda"],
  },
  gid: {
    icon: "🧭",
    title: "Gid",
    short: "Shaxsiy gid sifatida buyurtma oling",
    heading: `${BRAND.name} gidi bo'ling`,
    text: "Narxni o'zingiz belgilaysiz, ish kunlaringizni va uchrashuv joylarini o'zingiz tanlaysiz.",
    perks: [
      "Komissiya — 15%, qolgani sizga",
      "To'lov xizmatdan keyin 24 soat ichida",
      "Uchrashuv joylari va band kunlarni o'zingiz belgilaysiz",
      "Profil 48 soat ichida tekshiriladi",
    ],
    steps: ["Rasm, sertifikat va narxlar bilan ariza yuboring", "Profilingiz tekshiriladi", "Buyurtmalarni qabul qiling"],
  },
  mehmonxona: {
    icon: "🏡",
    title: "Mehmonxona",
    short: "Xonalaringizni sayohatchilarga soting",
    heading: `Joyingizni ${BRAND.name}'ga qo'shing`,
    text: "Mehmonxona, mehmon uyi, hostel yoki dam olish maskani — sayohatchilar sizni topsin.",
    perks: [
      "Xona turlari, narxlar va bo'sh xonalarni kabinetda boshqarasiz",
      "20 tagacha rasm va 4 tagacha video",
      "Bronlar to'langandan keyin tasdiqlanadi",
      "Ariza tekshiruvdan so'ng faollashadi",
    ],
    steps: ["Ariza yuboring", "Kabinetda rasm, video va xonalarni qo'shing", "Tekshiruvdan so'ng bron qabul qiling"],
  },
};

const isTuri = (v: string | undefined): v is Turi => !!v && v in TYPES;

export default async function PartnershipPage({ searchParams }: { searchParams: Promise<{ turi?: string }> }) {
  const { turi: raw } = await searchParams;
  const turi = isTuri(raw) ? raw : null;
  const user = await getUser();
  const t = turi ? TYPES[turi] : null;
  const needsDestinations = turi === "gid" || turi === "mehmonxona";
  const destinations = needsDestinations
    ? (await apiGet<Paginated<Destination>>("/catalog/destinations/", { query: { page_size: 50 } })).results
    : [];

  return (
    <>
      {/* Hero */}
      <section className="nature-bg">
        <div className="container-lz py-16 sm:py-20">
          <p className="text-xs font-bold uppercase tracking-[0.3em] text-sun-300">Hamkorlik</p>
          <h1 className="mt-3 max-w-2xl text-4xl leading-tight text-white sm:text-5xl">{BRAND.name} bilan birga ishlang</h1>
          <p className="mt-4 max-w-xl text-lg text-forest-50/90">
            Turagentlik, gid yoki mehmonxona — kim ekaningizni tanlang va ariza yuboring. Tasdiqlangach, o&apos;z kabinetingiz
            ochiladi.
          </p>
        </div>
      </section>

      {/* Turni tanlash */}
      <section className="container-lz -mt-10">
        <div className="grid gap-4 md:grid-cols-3">
          {(Object.keys(TYPES) as Turi[]).map((k) => {
            const on = k === turi;
            return (
              <Link
                key={k}
                href={`/hamkorlik?turi=${k}#ariza`}
                scroll={false}
                aria-current={on ? "true" : undefined}
                className={`card group block p-6 transition hover:-translate-y-0.5 hover:shadow-lift ${on ? "ring-2 ring-forest-600" : ""}`}
              >
                <span className={`flex h-12 w-12 items-center justify-center rounded-2xl text-2xl ${on ? "bg-forest-600" : "bg-forest-50"}`}>{TYPES[k].icon}</span>
                <h2 className="mt-4 text-lg">{TYPES[k].title}</h2>
                <p className="mt-1 text-sm text-ink-soft">{TYPES[k].short}</p>
                <span className="mt-4 inline-block text-sm font-semibold text-forest-600 group-hover:underline">
                  {on ? "✓ Tanlandi" : "Tanlash ›"}
                </span>
              </Link>
            );
          })}
        </div>
      </section>

      {/* Tanlangan tur: afzalliklar + forma */}
      <section id="ariza" className="container-lz scroll-mt-20 py-12 sm:py-16">
        {!t ? (
          <p className="text-center text-ink-soft">Yuqoridan qaysi yo&apos;nalishda ishlashingizni tanlang — shunga mos ariza formasi ochiladi.</p>
        ) : (
          <div className="grid gap-8 lg:grid-cols-[1fr_1.6fr] lg:gap-12">
            <aside className="lg:sticky lg:top-24 lg:self-start">
              <div className="nature-bg rounded-[1.5rem] p-7 text-white sm:p-9">
                <p className="text-xs font-bold uppercase tracking-[0.3em] text-sun-300">
                  {t.icon} {t.title}
                </p>
                <h2 className="mt-3 text-3xl leading-tight text-white">{t.heading}</h2>
                <p className="mt-3 text-forest-50/90">{t.text}</p>
                <ul className="mt-6 space-y-3 text-sm">
                  {t.perks.map((p) => (
                    <li key={p} className="flex gap-3">
                      <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-white/15">
                        <Icon name="check" size={14} />
                      </span>
                      <span className="text-forest-50/90">{p}</span>
                    </li>
                  ))}
                </ul>
                <ol className="mt-6 space-y-2 border-t border-white/15 pt-5 text-sm">
                  {t.steps.map((s, i) => (
                    <li key={s} className="flex gap-3">
                      <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-sun-500 text-xs font-bold">{i + 1}</span>
                      <span className="text-forest-50/90">{s}</span>
                    </li>
                  ))}
                </ol>
              </div>
            </aside>

            <div className="min-w-0">
              {!user ? (
                <div className="card p-8 text-center">
                  <h3 className="text-xl">Ariza yuborish uchun tizimga kiring</h3>
                  <p className="mt-2 text-sm text-ink-soft">
                    Ariza akkauntingizga bog&apos;lanadi — tasdiqlangach shu akkaunt bilan kabinetga kirasiz.
                  </p>
                  <Link href={`/login?next=${encodeURIComponent(`/hamkorlik?turi=${turi}`)}`} className="btn-primary mt-5 px-6 py-3">
                    Kirish yoki ro&apos;yxatdan o&apos;tish
                  </Link>
                </div>
              ) : turi === "agentlik" ? (
                <AgencyApplyForm trustedPhone={accountPhone(user)} />
              ) : turi === "gid" ? (
                <BecomeGuideForm destinations={destinations} trustedPhone={accountPhone(user)} />
              ) : (
                <JoinHotelForm destinations={destinations} trustedPhone={accountPhone(user)} />
              )}
            </div>
          </div>
        )}
      </section>
    </>
  );
}
