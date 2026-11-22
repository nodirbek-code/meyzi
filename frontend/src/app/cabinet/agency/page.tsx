import { AgencyHome } from "@/components/cabinet/AgencyHome";
import { requireRole } from "@/lib/roles";

export default async function Page() {
  await requireRole("agency", "/cabinet/agency");
  return <AgencyHome />;
}
