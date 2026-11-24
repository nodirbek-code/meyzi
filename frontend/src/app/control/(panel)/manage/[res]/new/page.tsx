import Link from "next/link";
import { notFound } from "next/navigation";

import { CrudForm } from "@/components/control/CrudForm";
import type { CrudList } from "@/lib/control";
import { controlGet, requireStaff } from "@/lib/control-server";

function prefill(schema: CrudList["schema"], sp: Record<string, string | undefined>) {
  const out: Record<string, unknown> = {};
  for (const f of schema) if (f.type === "fk" && sp[f.name]) out[f.name] = sp[f.name];
  return Object.keys(out).length ? out : null;
}

export default async function ManageNew({
  params,
  searchParams,
}: {
  params: Promise<{ res: string }>;
  searchParams: Promise<Record<string, string | undefined>>;
}) {
  await requireStaff();
  const { res } = await params;
  const sp = await searchParams;
  const d = await controlGet<CrudList>(`/manage/${res}/`, { page: 1 });
  if (!d.can_create) notFound();
  return (
    <div className="space-y-5">
      <Link href={`/control/manage/${res}`} className="text-sm text-ink-mute hover:text-forest-700">‹ {d.title}</Link>
      <h2 className="text-xl">Yangi: {d.title}</h2>
      {d.hint && <p className="rounded-xl bg-sky-50 px-4 py-3 text-sm text-sky-700">{d.hint}</p>}
      {/* ?hotel=5 kabi — maydon oldindan tanlanadi (hamkor mehmonxonasiga rasm qo'shish) */}
      <CrudForm res={res} schema={d.schema} data={prefill(d.schema, sp)} />
    </div>
  );
}
