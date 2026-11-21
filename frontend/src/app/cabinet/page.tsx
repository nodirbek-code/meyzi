import Link from "next/link";
import { redirect } from "next/navigation";

import { BRAND } from "@/lib/brand";
import { getRoles } from "@/lib/roles";
import { requireUser } from "@/lib/session";

export default async function CabinetHome() {
  await requireUser("/cabinet");
  const roles = await getRoles();
  if (roles.agency) redirect("/cabinet/agency");
  if (roles.hotel) redirect("/cabinet/hotel");
  if (roles.guide) redirect("/cabinet/guide");
  return (
    <div>
      <p className="mb-6 text-ink-soft">Siz hali hamkor emassiz. Qaysi yo&apos;nalishda ishlaysiz?</p>
      <div className="grid gap-5 md:grid-cols-3">
        {[
          ["/agencies", "🏢", "Turagentlik", "Turlaringizni joylang va bron qabul qiling."],
          ["/guides/become", "🧭", "Gid", "Shaxsiy gid sifatida buyurtma oling."],
          ["/hotels/join", "🏡", "Mehmonxona", `Xonalaringizni ${BRAND.name} orqali sotish.`],
        ].map(([href, icon, title, text]) => (
          <Link key={href} href={href} className="card group p-6 transition hover:-translate-y-0.5 hover:shadow-lift">
            <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-forest-50 text-2xl">{icon}</span>
            <h2 className="mt-4 text-lg">{title}</h2>
            <p className="mt-1 text-sm text-ink-soft">{text}</p>
            <span className="mt-4 inline-block text-sm font-semibold text-forest-600 group-hover:underline">Ariza berish ›</span>
          </Link>
        ))}
      </div>
    </div>
  );
}
