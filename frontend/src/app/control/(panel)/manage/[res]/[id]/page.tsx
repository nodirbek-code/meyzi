import Link from "next/link";
import { redirect } from "next/navigation";

import { CrudForm } from "@/components/control/CrudForm";
import type { CrudDetail } from "@/lib/control";
import { controlGet, requireStaff } from "@/lib/control-server";

export default async function ManageEdit({ params }: { params: Promise<{ res: string; id: string }> }) {
  await requireStaff();
  const { res, id } = await params;
  const d = await controlGet<CrudDetail>(`/manage/${res}/${id}/`);
  if (!d.editable) redirect(`/control/manage/${res}`); // hamkor kiritgan — faqat moderatsiya
  return (
    <div className="space-y-5">
      <Link href={`/control/manage/${res}`} className="text-sm text-ink-mute hover:text-forest-700">‹ {d.title}</Link>
      <h2 className="text-xl">{d.name}</h2>
      <CrudForm res={res} schema={d.schema} data={d.data} id={d.id} canDelete={d.can_delete} />
    </div>
  );
}
