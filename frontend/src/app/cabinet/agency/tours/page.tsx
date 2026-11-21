import { AgencyTours } from "@/components/cabinet/AgencyTours";
import { requireUser } from "@/lib/session";

export default async function Page() {
  await requireUser("/cabinet/agency/tours");
  return <AgencyTours />;
}
