import { notFound } from "next/navigation";

import { GuideCabinet } from "@/components/cabinet/GuideCabinet";
import { getRoles } from "@/lib/roles";
import { requireUser } from "@/lib/session";

export default async function Page() {
  await requireUser("/cabinet/guide");
  if (!(await getRoles()).guide) notFound();
  return <GuideCabinet />;
}
