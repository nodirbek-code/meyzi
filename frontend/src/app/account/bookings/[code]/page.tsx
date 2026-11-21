import Link from "next/link";
import { notFound } from "next/navigation";

import { CancelBooking, PaymentChooser, PaymentDeadline, ReviewForm } from "@/components/BookingActions";
import { Badge, Cover, Icon } from "@/components/ui";
import { apiGet, apiGetOrNull } from "@/lib/api";
import { BOOKING_STATUS, dateLong, dateTime, money, phone, POLICY_LABEL, weekday } from "@/lib/format";
import { requireUser } from "@/lib/session";
import type { Booking, Features } from "@/lib/types";

const WEEKDAY_FULL: Record<string, string> = {
  Ya: "yakshanba",
  Du: "dushanba",
  Se: "seshanba",
  Ch: "chorshanba",
  Pa: "payshanba",
  Ju: "juma",
  Sh: "shanba",
};

/**
 * Bron sahifasi. Bron kodi (LZ…) foydalanuvchiga ko'rsatilmaydi — faqat sahifa manzilida (texnik identifikator).
 */
export default async function BookingPage({ params }: { params: Promise<{ code: string }> }) {
  const { code } = await params;
  await requireUser(`/account/bookings/${code}`);
  const b = await apiGetOrNull<Booking>(`/bookings/${code}/`, { auth: true });
  if (!b) notFound();
  const features = await apiGet<Features>("/features/");
  const st = BOOKING_STATUS[b.status];
  const pending = b.status === "pending_payment";
  const active = pending || b.status === "confirmed";
  const t = b.tour;
  const map =
    t.meeting_map_url ||
    (t.meeting_latitude && t.meeting_longitude ? `https://yandex.uz/maps/?pt=${t.meeting_longitude},${t.meeting_latitude}&z=16&l=map` : null);

  return (
    <div className="mx-auto max-w-xl space-y-4">
      <Link href="/account" className="inline-flex items-center gap-1 text-sm text-ink-mute hover:text-forest-700">
        ‹ Mening bronlarim
      </Link>

      <Cover src={t.cover} alt={t.title} className="aspect-[16/8] w-full rounded-xl2" />

      <div className="flex items-start justify-between gap-3">
        <div>
          <h2 className="text-2xl leading-tight">
            <Link href={`/tours/${t.slug}`} className="hover:text-forest-700">
              {t.title}
            </Link>
          </h2>
          <p className="mt-1 text-sm text-ink-soft">
            {dateLong(b.departure_date, true)}, {WEEKDAY_FULL[weekday(b.departure_date)]}
          </p>
        </div>
        <Badge tone={st.tone}>{st.label}</Badge>
      </div>

      {b.status === "confirmed" && (
        <div className="flex gap-3 rounded-xl2 border border-forest-100 bg-forest-50 p-4 text-sm text-forest-800">
          <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-forest-600 text-xs text-white">✓</span>
          <span>Bron tasdiqlandi. Jo&apos;nash vaqtida uchrashuv joyiga keling — tashkilotchi siz bilan bog&apos;lanadi.</span>
        </div>
      )}

      <div className="card space-y-4 p-5">
        <div className="flex justify-between text-sm">
          <span className="text-ink-soft">O&apos;rinlar</span>
          <b>{b.seats}</b>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-ink-soft">Narx (1 kishi)</span>
          <span>{money(b.unit_price_uzs)}</span>
        </div>
        <div className="flex items-baseline justify-between border-t border-sand-200 pt-4">
          <span className="font-semibold">Jami</span>
          <b className="text-2xl">{money(b.total_uzs)}</b>
        </div>
        <dl className="space-y-1.5 border-t border-sand-200 pt-4 text-xs text-ink-mute">
          <div className="flex justify-between">
            <dt>Jo&apos;nash</dt>
            <dd className="text-ink-soft">{dateTime(b.departure_at)}</dd>
          </div>
          <div className="flex justify-between">
            <dt>Bron sanasi</dt>
            <dd className="text-ink-soft">{dateLong(b.created_at.slice(0, 10), true)}</dd>
          </div>
          <div className="flex justify-between">
            <dt>Bekor qilish sharti</dt>
            <dd className="text-ink-soft">{POLICY_LABEL[b.cancellation_policy]}</dd>
          </div>
        </dl>

        {pending && b.expires_at && <PaymentDeadline until={b.expires_at} />}
        {pending && <PaymentChooser total={b.total_uzs} installment={b.installment} methods={features.payments} />}
        {active && <CancelBooking code={code} tourSlug={t.slug} />}
        {!active && (
          <Link href={`/tours/${t.slug}`} className="btn-ghost w-full">
            Turni ko&apos;rish
          </Link>
        )}
      </div>

      {b.status === "cancelled" && (
        <div className="rounded-xl2 bg-sand-100 p-4 text-sm text-ink-soft">
          Bu bron bekor qilindi.
          {b.cancel_reason && <> Sabab: {b.cancel_reason}.</>}
          {b.refund_uzs > 0 && (
            <>
              {" "}Qaytariladigan summa: <b className="text-ink">{money(b.refund_uzs)}</b>.
            </>
          )}
        </div>
      )}
      {b.status === "expired" && (
        <div className="rounded-xl2 bg-sand-100 p-4 text-sm text-ink-soft">
          To&apos;lov muddati tugadi va o&apos;rinlar bo&apos;shatildi. Sana hali ochiq bo&apos;lsa, qaytadan bron qilishingiz mumkin.
        </div>
      )}

      {/* Uchrashuv joyi */}
      {t.meeting_point && (
        <div className="flex gap-3 rounded-xl2 border border-sky-100 bg-sky-50 p-4">
          <Icon name="pin" size={20} className="mt-0.5 shrink-0 text-sky-500" />
          <div className="text-sm">
            <p className="font-semibold text-sky-700">Uchrashuv joyi</p>
            <p className="text-ink">{t.meeting_point}</p>
            {map && (
              <a href={map} target="_blank" rel="noopener noreferrer" className="mt-1 inline-block font-semibold text-sky-700 hover:underline">
                Xaritada ochish ↗
              </a>
            )}
          </div>
        </div>
      )}

      {/* Sayohatchilar va aloqa */}
      <div className="card p-5 text-sm">
        {b.travelers.length > 0 && (
          <>
            <p className="mb-2 text-xs font-bold uppercase tracking-[0.15em] text-ink-mute">Sayohatchilar</p>
            <ol className="mb-4 space-y-1.5">
              {b.travelers.map((tr, i) => (
                <li key={i} className="flex gap-2">
                  <span className="w-4 text-right text-ink-mute">{i + 1}</span>
                  {tr.full_name}
                </li>
              ))}
            </ol>
          </>
        )}
        <p className="mb-2 text-xs font-bold uppercase tracking-[0.15em] text-ink-mute">Aloqa</p>
        <p>
          {b.contact_name}, {phone(b.contact_phone)}
        </p>
        <p className="mt-3 text-xs text-ink-mute">Tashkilotchi: {b.agency.name}</p>
      </div>

      {b.status === "completed" && !b.has_review && (
        <div className="card p-5">
          <h3 className="mb-3 text-lg">Sayohat qanday o&apos;tdi?</h3>
          <ReviewForm code={code} />
        </div>
      )}
    </div>
  );
}
