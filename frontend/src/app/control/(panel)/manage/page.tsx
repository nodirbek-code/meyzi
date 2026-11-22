import Link from "next/link";

import type { CrudMeta } from "@/lib/control";
import { controlGet, requireStaff } from "@/lib/control-server";

/** Boshqarish: admin yaratadigan va tahrirlaydigan barcha bo'limlar. */
export default async function ManageIndex() {
  await requireStaff();
  const list = await controlGet<CrudMeta[]>("/manage/");
  const groups = [...new Set(list.map((r) => r.group))];
  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-xl">Boshqarish</h2>
        <p className="mt-1 text-sm text-ink-soft">
          Kontentni va platforma o&apos;zi boshqaradigan hamkorlarni shu yerda yaratasiz va tahrirlaysiz. Hamkorlarning o&apos;zi
          kiritgan ma&apos;lumotlari — faqat ko&apos;rish va moderatsiya (Tekshiruv bo&apos;limi).
        </p>
      </div>
      {groups.map((g) => (
        <section key={g} className="space-y-3">
          <h3 className="text-sm font-semibold uppercase tracking-wide text-ink-mute">{g}</h3>
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
            {list
              .filter((r) => r.group === g)
              .map((r) => (
                <Link key={r.key} href={`/control/manage/${r.key}`} className="card block p-4 transition hover:-translate-y-0.5 hover:shadow-lift">
                  <div className="flex items-baseline justify-between gap-2">
                    <span className="font-semibold">{r.title}</span>
                    <span className="text-sm text-ink-mute">{r.count}</span>
                  </div>
                  <span className="mt-2 inline-block text-sm text-forest-700">{r.can_create ? "Ko'rish va qo'shish ›" : "Ko'rish ›"}</span>
                </Link>
              ))}
          </div>
        </section>
      ))}
    </div>
  );
}
