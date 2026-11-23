import { HotelMedia } from "@/components/cabinet/HotelCabinet";
import { requireRole } from "@/lib/roles";

export default async function Page() {
  await requireRole("hotel", "/cabinet/hotel/media");
  return <HotelMedia />;
}
