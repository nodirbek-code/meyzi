import { GuideCabinet } from "@/components/cabinet/GuideCabinet";
import { requireRole } from "@/lib/roles";

export default async function Page() {
  await requireRole("guide", "/cabinet/guide");
  return <GuideCabinet />;
}
