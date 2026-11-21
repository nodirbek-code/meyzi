import { AgencyBookings } from "@/components/cabinet/AgencyBookings";
import { requireUser } from "@/lib/session";

export default async function Page() {
  await requireUser("/cabinet/agency/bookings");
  return <AgencyBookings />;
}
