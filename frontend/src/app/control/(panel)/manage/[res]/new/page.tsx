import Link from "next/link";
import { notFound } from "next/navigation";

import { CrudForm } from "@/components/control/CrudForm";
import type { CrudList } from "@/lib/control";
import { controlGet, requireStaff } from "@/lib/control-server";

export default async function ManageNew({ params }: { params: Promise<{ res: string }> }) {
  await requireStaff();
  const { res } = await params;
  const d = await controlGet<CrudList>(`/manage/${res}/`, { page: 1 });
  if (!d.can_create) notFound();
  return (
    <div className="space-y-5">
      <Link href={`/control/manage/${res}`} className="text-sm text-ink-mute hover:text-forest-700">‹ {d.title}</Link>
      <h2 className="text-xl">Yangi: {d.title}</h2>
      {d.hint && <p className="rounded-xl bg-sky-50 px-4 py-3 text-sm text-sky-700">{d.hint}</p>}
      <CrudForm res={res} schema={d.schema} data={null} />
    </div>
  );
}
