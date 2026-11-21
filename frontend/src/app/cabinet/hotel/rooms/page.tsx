import { HotelRooms } from "@/components/cabinet/HotelCabinet";
import { requireUser } from "@/lib/session";

export default async function Page() {
  await requireUser("/cabinet/hotel/rooms");
  return <HotelRooms />;
}
