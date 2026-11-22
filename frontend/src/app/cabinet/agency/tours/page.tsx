import { AgencyTours } from "@/components/cabinet/AgencyTours";
import { requireRole } from "@/lib/roles";

export default async function Page() {
  await requireRole("agency", "/cabinet/agency/tours");
  return <AgencyTours />;
}
