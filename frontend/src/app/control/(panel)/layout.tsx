import type { Metadata } from "next";

import { ControlNav } from "@/components/control/ControlNav";
import type { Dashboard } from "@/lib/control";
import { controlGet, requireStaff } from "@/lib/control-server";

export const metadata: Metadata = { title: "Admin paneli", robots: { index: false, follow: false } };

/** Saytdagi admin paneli — faqat adminlar (is_staff). */
export default async function ControlLayout({ children }: { children: React.ReactNode }) {
  const user = await requireStaff();
  const d = await controlGet<Dashboard>("/dashboard/");
  return (
    <div className="container-lz py-8">
      <div className="mb-6 flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="eyebrow">Boshqaruv paneli</p>
          <h1 className="mt-1 text-2xl sm:text-3xl">{d.role_title}</h1>
        </div>
        <p className="text-sm text-ink-mute">{user.full_name || user.email}</p>
      </div>
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[240px_1fr] lg:gap-8">
        <ControlNav queue={d.queue} role={d.role} />
        <div className="min-w-0">{children}</div>
      </div>
    </div>
  );
}
