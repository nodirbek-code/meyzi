import type { Metadata } from "next";
import Link from "next/link";
import type { ReactNode } from "react";

import { Countdown } from "@/components/BookingActions";
import { Badge, Cover, EmptyState } from "@/components/ui";
import { apiGet } from "@/lib/api";
import { BOOKING_STATUS, dateLong, money, weekday } from "@/lib/format";
import { requireUser } from "@/lib/session";
import type { Booking, Paginated } from "@/lib/types";

export const metadata: Metadata = { title: "Bronlarim" };

type GuideBooking = {
  code: string;
  status: string;
  guide: { display_name: string; photo: string | null };
  start_date: string;
  total_uzs: number;
  duration: string;
  group_size: number;
};
type HotelBooking = {
  code: string;
  status: string;
  hotel: { name: string };
  room_type: string;
  check_in: string;
  check_out: string;
  nights: number;
  total_uzs: number;
};

const GUIDE_STATUS: Record<string, { label: string; tone: "gold" | "green" | "gray" | "red" | "blue" }> = {
  requested: { label: "Gid javobi kutilmoqda", tone: "gold" },
  accepted: { label: "Gid qabul qildi — to'lov kutilmoqda", tone: "gold" },
  confirmed: { label: "Tasdiqlangan", tone: "green" },
  completed: { label: "Yakunlangan", tone: "blue" },
  declined: { label: "Gid rad etdi", tone: "red" },
  expired: { label: "Gid javob bermadi", tone: "gray" },
  cancelled: { label: "Bekor qilingan", tone: "red" },
};
const DURATION: Record<string, string> = { half_day: "yarim kun", full_day: "to'liq kun", multi_day: "bir necha kun" };

/** Bron qatori (kod ko'rsatilmaydi) */
function Row({ href, image, alt, title, sub, total, badge, extra }: {
  href?: string;
  image: string | null;
  alt: string;
  title: string;
  sub: string;
  total: number;
  badge: ReactNode;
  extra?: ReactNode;
}) {
  const body = (
    <>
      <Cover src={image} alt={alt} className="h-16 w-16 shrink-0 rounded-xl sm:h-20 sm:w-24" />
      <div className="min-w-0 flex-1">
        <p className="line-clamp-2 font-semibold leading-snug">{title}</p>
        <p className="mt-0.5 text-sm text-ink-soft">{sub}</p>
        <p className="mt-0.5 text-sm font-semibold">{money(total)}</p>
        {extra}
      </div>
      <div className="shrink-0 self-start">{badge}</div>
    </>
  );
  const cls = "card flex items-center gap-4 p-3 sm:p-4";
  return href ? (
    <Link href={href} className={`${cls} transition hover:shadow-lift`}>
      {body}
    </Link>
  ) : (
    <div className={cls}>{body}</div>
  );
}

export default async function AccountPage() {
  const user = await requireUser("/account");
  const [tours, guides, hotels] = await Promise.all([
    apiGet<Paginated<Booking>>("/bookings/", { auth: true, query: { page_size: 50 } }),
    apiGet<Paginated<GuideBooking>>("/guide-bookings/", { auth: true, query: { page_size: 50 } }),
    apiGet<Paginated<HotelBooking>>("/hotel-bookings/", { auth: true, query: { page_size: 50 } }),
  ]);

  if (!tours.count && !guides.count && !hotels.count) {
    return (
      <EmptyState
        title="Hali bronlaringiz yo'q"
        text="Turlarni ko'rib chiqing — joyni bir necha soniyada band qilasiz."
        action={
          <Link href="/tours" className="btn-primary">
            Turlarni ko&apos;rish
          </Link>
        }
      />
    );
  }

  return (
    <div className="max-w-3xl space-y-10">
      {tours.count > 0 && (
        <section>
          <h2 className="mb-4 text-xl">Turlar</h2>
          <div className="space-y-3">
            {tours.results.map((b) => {
              const st = BOOKING_STATUS[b.status];
              return (
                <Row
                  key={b.code}
                  href={`/account/bookings/${b.code}`}
                  image={b.tour.cover}
                  alt={b.tour.title}
                  title={b.tour.title}
                  sub={`${weekday(b.departure_date)}, ${dateLong(b.departure_date, true)} · ${b.seats} o'rin`}
                  total={b.total_uzs}
                  badge={<Badge tone={st.tone}>{st.label}</Badge>}
                  extra={
                    b.status === "pending_payment" && b.expires_at ? (
                      <p className="mt-1 text-xs text-sun-700">
                        To&apos;lash uchun: <Countdown until={b.expires_at} />
                      </p>
                    ) : undefined
                  }
                />
              );
            })}
          </div>
        </section>
      )}
      {guides.count > 0 && (
        <section>
          <h2 className="mb-4 text-xl">Gidlar</h2>
          <div className="space-y-3">
            {guides.results.map((b) => {
              const st = GUIDE_STATUS[b.status] ?? { label: b.status, tone: "blue" as const };
              return (
                <Row
                  key={b.code}
                  image={b.guide.photo}
                  alt={b.guide.display_name}
                  title={b.guide.display_name}
                  sub={`${dateLong(b.start_date, true)} · ${DURATION[b.duration] ?? b.duration} · ${b.group_size} kishi`}
                  total={b.total_uzs}
                  badge={<Badge tone={st.tone}>{st.label}</Badge>}
                />
              );
            })}
          </div>
        </section>
      )}
      {hotels.count > 0 && (
        <section>
          <h2 className="mb-4 text-xl">Mehmonxonalar</h2>
          <div className="space-y-3">
            {hotels.results.map((b) => (
              <Row
                key={b.code}
                image={null}
                alt={b.hotel.name}
                title={`${b.hotel.name} · ${b.room_type}`}
                sub={`${dateLong(b.check_in)} → ${dateLong(b.check_out, true)} · ${b.nights} kecha`}
                total={b.total_uzs}
                badge={<Badge tone={BOOKING_STATUS[b.status]?.tone ?? "blue"}>{BOOKING_STATUS[b.status]?.label ?? b.status}</Badge>}
              />
            ))}
          </div>
        </section>
      )}
      {["tourist", "admin"].includes(user.role) && (
        <section className="card p-6">
          <h2 className="text-lg">Hamkor bo&apos;lmoqchimisiz?</h2>
          <p className="mt-1 text-sm text-ink-soft">
            Hamkor kabineti faqat agentlik, gid va mehmonxonalar uchun. Ariza yuboring — admin tasdiqlagach kabinet ochiladi.
          </p>
          <div className="mt-4 grid gap-3 sm:grid-cols-3">
            {[
              ["/agencies", "🏢", "Turagentlik", "Turlaringizni joylang"],
              ["/guides/become", "🧭", "Gid", "Shaxsiy gid bo'ling"],
              ["/hotels/join", "🏡", "Mehmonxona", "Xonalaringizni soting"],
            ].map(([href, icon, title, text]) => (
              <Link key={href} href={href} className="rounded-xl border border-sand-200 p-4 transition hover:border-forest-400">
                <span className="text-2xl">{icon}</span>
                <p className="mt-2 font-semibold">{title}</p>
                <p className="text-xs text-ink-mute">{text}</p>
              </Link>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
