import { HotelBookings } from "@/components/cabinet/HotelCabinet";
import { requireRole } from "@/lib/roles";

export default async function Page() {
  await requireRole("hotel", "/cabinet/hotel/bookings");
  return <HotelBookings />;
}
