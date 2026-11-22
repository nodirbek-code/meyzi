import { GuideProfileEdit } from "@/components/cabinet/GuideProfile";
import { requireRole } from "@/lib/roles";

export default async function Page() {
  await requireRole("guide", "/cabinet/guide/profile");
  return <GuideProfileEdit />;
}
