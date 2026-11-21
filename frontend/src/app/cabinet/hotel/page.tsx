import { notFound } from "next/navigation";

import { HotelCabinet } from "@/components/cabinet/HotelCabinet";
import { getRoles } from "@/lib/roles";
import { requireUser } from "@/lib/session";

export default async function Page() {
  await requireUser("/cabinet/hotel");
  if (!(await getRoles()).hotel) notFound();
  return <HotelCabinet />;
}
