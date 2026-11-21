import { HotelBookings } from "@/components/cabinet/HotelCabinet";
import { requireUser } from "@/lib/session";

export default async function Page() {
  await requireUser("/cabinet/hotel/bookings");
  return <HotelBookings />;
}
