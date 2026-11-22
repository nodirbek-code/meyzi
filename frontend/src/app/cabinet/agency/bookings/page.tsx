import { AgencyBookings } from "@/components/cabinet/AgencyBookings";
import { requireRole } from "@/lib/roles";

export default async function Page() {
  await requireRole("agency", "/cabinet/agency/bookings");
  return <AgencyBookings />;
}
