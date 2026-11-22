import Link from "next/link";
import { redirect } from "next/navigation";

import { CabinetNav, type NavGroup } from "@/components/cabinet/CabinetNav";
import { getRoles, isPartner } from "@/lib/roles";
import { requireUser } from "@/lib/session";

const STATUS: Record<string, string> = {
  active: "Faol",
  approved: "Tasdiqlangan",
  pending: "Tekshiruvda",
  rejected: "Qaytarilgan",
  suspended: "To'xtatilgan",
};

/**
 * Hamkor kabineti — faqat agentlik, gid va mehmonxonalar uchun (oddiy foydalanuvchi /account ga qaytariladi).
 * Har bir rol o'z bo'limlarini ko'radi; bir nechta rol bo'lsa — hammasi menyuda.
 */
export default async function CabinetLayout({ children }: { children: React.ReactNode }) {
  await requireUser("/cabinet");
  const roles = await getRoles();
  if (!isPartner(roles)) redirect("/account");

  const groups: NavGroup[] = [];
  if (roles.agency)
    groups.push({
      title: "Turagentlik",
      links: [
        { href: "/cabinet/agency", label: "Umumiy", icon: "📊", exact: true },
        { href: "/cabinet/agency/tours", label: "Turlar", icon: "🗺️" },
        { href: "/cabinet/agency/bookings", label: "Bronlar", icon: "🗓️" },
        { href: "/cabinet/agency/reviews", label: "Sharhlar", icon: "★" },
      ],
    });
  if (roles.guide)
    groups.push({
      title: "Gid",
      links: [
        { href: "/cabinet/guide", label: "So'rovlar va bronlar", icon: "🗓️", exact: true },
        { href: "/cabinet/guide/profile", label: "Profil", icon: "🧑‍💼" },
        { href: "/cabinet/guide/meeting-points", label: "Uchrashuv joylari", icon: "📍" },
        { href: "/cabinet/guide/schedule", label: "Band kunlar", icon: "⛔" },
        { href: "/cabinet/guide/reviews", label: "Sharhlar", icon: "★" },
      ],
    });
  if (roles.hotel)
    groups.push({
      title: "Mehmonxona",
      links: [
        { href: "/cabinet/hotel", label: "Profil", icon: "🏡", exact: true },
        { href: "/cabinet/hotel/media", label: "Rasm va video", icon: "🖼️" },
        { href: "/cabinet/hotel/rooms", label: "Xonalar", icon: "🛏️" },
        { href: "/cabinet/hotel/bookings", label: "Bronlar", icon: "🗓️" },
        { href: "/cabinet/hotel/reviews", label: "Sharhlar", icon: "★" },
      ],
    });

  const [kind, main, name] = roles.agency
    ? ["Turagentlik kabineti", roles.agency, roles.agency.name]
    : roles.hotel
      ? ["Mehmonxona kabineti", roles.hotel, roles.hotel.name]
      : ["Gid kabineti", roles.guide, roles.guide?.display_name ?? ""];
  const eyebrow = groups.length > 1 ? "Hamkor kabineti" : kind;

  return (
    <div className="container-lz py-8">
      <div className="mb-6 flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="eyebrow">{eyebrow}</p>
          <h1 className="mt-1 flex flex-wrap items-center gap-3 text-2xl sm:text-3xl">
            {name}
            {main?.status && (
              <span className={`chip text-xs ${main.status === "approved" || main.status === "active" ? "bg-forest-50 text-forest-700" : "bg-sun-100 text-sun-700"}`}>
                {STATUS[main.status] ?? main.status}
              </span>
            )}
          </h1>
        </div>
        <Link href="/account" className="text-sm font-semibold text-forest-600 hover:underline">
          ‹ Shaxsiy kabinet
        </Link>
      </div>
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[220px_1fr] lg:gap-8">
        <CabinetNav groups={groups} />
        <div className="min-w-0">{children}</div>
      </div>
    </div>
  );
}
