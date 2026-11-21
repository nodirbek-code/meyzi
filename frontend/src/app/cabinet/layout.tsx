import Link from "next/link";

import { CabinetNav, type NavGroup } from "@/components/cabinet/CabinetNav";
import { getRoles } from "@/lib/roles";
import { requireUser } from "@/lib/session";

const STATUS: Record<string, string> = {
  active: "Faol",
  approved: "Tasdiqlangan",
  pending: "Tekshiruvda",
  rejected: "Rad etilgan",
  suspended: "To'xtatilgan",
};

export default async function CabinetLayout({ children }: { children: React.ReactNode }) {
  await requireUser("/cabinet");
  const roles = await getRoles();
  const groups: NavGroup[] = [];
  if (roles.agency)
    groups.push({
      title: "Agentlik",
      links: [
        { href: "/cabinet/agency", label: "Umumiy", icon: "📊", exact: true },
        { href: "/cabinet/agency/tours", label: "Turlar", icon: "🗺️" },
        { href: "/cabinet/agency/bookings", label: "Bronlar", icon: "🗓️" },
        { href: "/cabinet/agency/reviews", label: "Sharhlar", icon: "★" },
      ],
    });
  if (roles.guide) groups.push({ title: "Gid", links: [{ href: "/cabinet/guide", label: "Gid kabineti", icon: "🧭" }] });
  if (roles.hotel)
    groups.push({
      title: "Mehmonxona",
      links: [
        { href: "/cabinet/hotel", label: "Profil", icon: "🏡", exact: true },
        { href: "/cabinet/hotel/rooms", label: "Xonalar", icon: "🛏️" },
        { href: "/cabinet/hotel/bookings", label: "Bronlar", icon: "🗓️" },
      ],
    });

  const main = roles.agency ?? roles.hotel ?? roles.guide;
  const name = roles.agency?.name || roles.hotel?.name || roles.guide?.display_name || "Kabinet";

  return (
    <div className="container-lz py-8">
      <div className="mb-6 flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="eyebrow">Hamkor kabineti</p>
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
      {groups.length > 0 ? (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-[220px_1fr] lg:gap-8">
          <CabinetNav groups={groups} />
          <div className="min-w-0">{children}</div>
        </div>
      ) : (
        children
      )}
    </div>
  );
}
