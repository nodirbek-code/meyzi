import { notFound } from "next/navigation";

import { AgencyHome } from "@/components/cabinet/AgencyHome";
import { getRoles } from "@/lib/roles";
import { requireUser } from "@/lib/session";

export default async function AgencyCabinetPage() {
  await requireUser("/cabinet/agency");
  if (!(await getRoles()).agency) notFound();
  return <AgencyHome />;
}
