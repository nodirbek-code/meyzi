import Link from "next/link";
import { redirect } from "next/navigation";

import { CrudForm } from "@/components/control/CrudForm";
import { Gallery } from "@/components/control/Gallery";
import type { CrudDetail } from "@/lib/control";
import { controlGet, requireStaff } from "@/lib/control-server";

export default async function ManageEdit({ params }: { params: Promise<{ res: string; id: string }> }) {
  await requireStaff();
  const { res, id } = await params;
  const d = await controlGet<CrudDetail>(`/manage/${res}/${id}/`);
  // Hamkor kiritgan yozuv: faqat rasmlar (gid surati, logotip, tur/mehmonxona galereyasi), qolgani — moderatsiya
  const mediaOnly = !d.editable && (!!d.media_fields?.length || !!d.gallery);
  if (!d.editable && !mediaOnly) redirect(`/control/manage/${res}`);
  const schema = mediaOnly ? d.schema.filter((f) => d.media_fields?.includes(f.name)) : d.schema;
  return (
    <div className="space-y-5">
      <Link href={`/control/manage/${res}`} className="text-sm text-ink-mute hover:text-forest-700">‹ {d.title}</Link>
      <h2 className="text-xl">{d.name}</h2>
      {mediaOnly && (
        <p className="rounded-xl bg-sky-50 px-4 py-3 text-sm text-sky-700">
          Hamkorning o&apos;zi kiritgan yozuv — admin faqat rasmlarini o&apos;zgartira oladi.
        </p>
      )}
      {d.gallery && <Gallery gallery={d.gallery} parentId={d.id} />}
      {schema.length > 0 && (
        <CrudForm res={res} schema={schema} data={d.data} id={d.id} canDelete={d.can_delete && !mediaOnly} />
      )}
    </div>
  );
}
