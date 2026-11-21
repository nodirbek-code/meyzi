import type { Metadata } from "next";

import { AgencyApplyForm } from "@/components/AgencyApplyForm";
import { Icon, SectionTitle } from "@/components/ui";
import { BRAND } from "@/lib/brand";
import { accountPhone } from "@/lib/phone";
import { getUser } from "@/lib/session";

export const metadata: Metadata = { title: "Agentliklar uchun" };

const BENEFITS = [
  {
    icon: "users",
    title: "Ko'proq mijozlarga yeting",
    text: `Turlaringiz sayohatchilar tur qidiradigan ${BRAND.name} katalogida chiqadi — qo'shimcha marketing xarajatisiz.`,
  },
  {
    icon: "calendar",
    title: "Oson boshqaruv",
    text: "Turlar, sanalar, joylar va bronlarni qulay kabinetda boshqaring. Hamma narsa bir joyda — tez va oddiy.",
  },
  {
    icon: "shield",
    title: "Ishonchli platforma",
    text: "Tasdiqlangan agentlik belgisi mijozlar ishonchini oshiradi. Sharhlar va reyting obro'ingizni ko'rsatadi.",
  },
] as const;

const STEPS = [
  { title: "Ariza yuboring", text: "Quyidagi formani to'ldiring: agentlik haqida asosiy ma'lumotlar." },
  { title: "Tasdiqdan o'ting", text: "Biz bog'lanamiz, hujjatlarni (STIR, litsenziya) ko'rib chiqamiz va hisobingizni faollashtiramiz." },
  { title: "Turlarni qo'shing", text: "Turlaringizni joylang va birinchi bronlarni qabul qiling." },
];

export default async function AgenciesPage() {
  const user = await getUser();
  return (
    <>
      {/* Hero */}
      <section className="nature-bg">
        <div className="container-lz py-20 sm:py-28">
          <p className="text-xs font-bold uppercase tracking-[0.3em] text-sun-300">Hamkorlik</p>
          <h1 className="mt-3 max-w-2xl text-4xl leading-tight text-white sm:text-5xl">Sayohat biznesingizni {BRAND.name} bilan rivojlantiring</h1>
          <p className="mt-4 max-w-xl text-lg text-forest-50/90">
            Turlaringizni sayohatchilar qidiradigan joyga joylang, bronlarni boshqaring va agentligingizni o&apos;stiring.
          </p>
          <a href="#ariza" className="btn-light mt-8 px-6 py-3 text-base">
            Ariza berish ↓
          </a>
        </div>
      </section>

      {/* Afzalliklar */}
      <section className="container-lz pt-20">
        <SectionTitle center eyebrow="Nima uchun biz" title="Platforma siz uchun nima beradi" />
        <div className="grid gap-5 md:grid-cols-3">
          {BENEFITS.map((b) => (
            <div key={b.title} className="card p-6">
              <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-forest-50 text-forest-600">
                <Icon name={b.icon} size={24} />
              </span>
              <h3 className="mt-4 font-sans text-base font-semibold">{b.title}</h3>
              <p className="mt-2 text-sm text-ink-soft">{b.text}</p>
            </div>
          ))}
        </div>
      </section>

      {/* 3 qadam */}
      <section className="container-lz pt-20">
        <SectionTitle center eyebrow="Qanday ishlaydi" title="3 qadamda boshlang" />
        <ol className="relative grid gap-8 md:grid-cols-3">
          <span className="absolute left-[16.7%] right-[16.7%] top-6 hidden h-0.5 bg-forest-100 md:block" aria-hidden />
          {STEPS.map((s, i) => (
            <li key={s.title} className="relative text-center">
              <span className="relative mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-forest-600 text-sm font-extrabold text-white ring-8 ring-sand-50">
                0{i + 1}
              </span>
              <h3 className="mt-4 font-sans text-base font-semibold">{s.title}</h3>
              <p className="mx-auto mt-1 max-w-xs text-sm text-ink-soft">{s.text}</p>
            </li>
          ))}
        </ol>
      </section>

      {/* Ariza */}
      <section id="ariza" className="container-lz scroll-mt-20 pt-20">
        <SectionTitle center eyebrow="Ariza" title="Hamkor bo'lishni istaysizmi?" text="Formani to'ldiring — biz 24 soat ichida siz bilan bog'lanamiz." />
        <div className="mx-auto max-w-2xl">
          <AgencyApplyForm trustedPhone={accountPhone(user)} />
        </div>
      </section>
    </>
  );
}
