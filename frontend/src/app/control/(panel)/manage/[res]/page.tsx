import Link from "next/link";

import { ImportExcel } from "@/components/control/ImportExcel";
import type { CrudList } from "@/lib/control";
import { controlGet, requireStaff } from "@/lib/control-server";

export default async function ManageList({
  params,
  searchParams,
}: {
  params: Promise<{ res: string }>;
  searchParams: Promise<{ q?: string; page?: string }>;
}) {
  await requireStaff();
  const { res } = await params;
  const { q = "", page = "1" } = await searchParams;
  const d = await controlGet<CrudList>(`/manage/${res}/`, { q, page });

  return (
    <div className="space-y-5">
      <Link href="/control/manage" className="text-sm text-ink-mute hover:text-forest-700">‹ Boshqarish</Link>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-xl">
          {d.title} <span className="text-base text-ink-mute">({d.count})</span>
        </h2>
        <div className="flex flex-wrap gap-2">
          <form className="flex gap-2">
            <input className="input w-52" name="q" defaultValue={q} placeholder="Qidirish…" />
            <button className="btn-ghost px-3">Izlash</button>
          </form>
          {d.can_create && (
            <Link href={`/control/manage/${res}/new`} className="btn-primary">+ Yangi qo&apos;shish</Link>
          )}
        </div>
      </div>
      {d.hint && <p className="rounded-xl bg-sky-50 px-4 py-3 text-sm text-sky-700">{d.hint}</p>}
      {d.can_import && <ImportExcel res={res} title={d.title} />}

      <div className="card overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="border-b border-sand-200 text-left text-xs uppercase tracking-wide text-ink-mute">
            <tr>
              {d.columns.map((c) => (
                <th key={c} className="px-4 py-3 font-semibold">{c}</th>
              ))}
              <th className="px-4 py-3" />
            </tr>
          </thead>
          <tbody className="divide-y divide-sand-200">
            {d.results.map((r) => {
              const href = r.editable ? `/control/manage/${res}/${r.id}` : r.moderation_url;
              return (
                <tr key={r.id} className="hover:bg-sand-50">
                  {r.cells.map((c, i) => (
                    <td key={i} className={`px-4 py-2.5 ${i === 0 ? "font-semibold" : "text-ink-soft"}`}>{c}</td>
                  ))}
                  <td className="whitespace-nowrap px-4 py-2.5 text-right">
                    {r.editable ? (
                      <Link href={href} className="text-forest-700">Tahrirlash ›</Link>
                    ) : href ? (
                      <Link href={href} className="text-ink-mute" title="Hamkor kiritgan — faqat moderatsiya">🔒 Moderatsiya ›</Link>
                    ) : (
                      <span className="text-ink-mute">🔒</span>
                    )}
                  </td>
                </tr>
              );
            })}
            {!d.results.length && (
              <tr>
                <td colSpan={d.columns.length + 1} className="px-4 py-8 text-center text-ink-mute">Hech narsa topilmadi.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {d.pages > 1 && (
        <div className="flex gap-2">
          {Array.from({ length: d.pages }, (_, i) => i + 1).map((p) => (
            <Link
              key={p}
              href={`/control/manage/${res}?page=${p}${q ? `&q=${encodeURIComponent(q)}` : ""}`}
              className={`chip border px-3 py-1.5 ${p === d.page ? "border-forest-600 bg-forest-600 text-white" : "border-sand-300 bg-white"}`}
            >
              {p}
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
