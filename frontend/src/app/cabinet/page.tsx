import { redirect } from "next/navigation";

import { getRoles } from "@/lib/roles";
import { requireUser } from "@/lib/session";

/** Kabinet faqat hamkorlar uchun: agentlik, gid yoki mehmonxona. Oddiy foydalanuvchi — shaxsiy kabinetga. */
export default async function CabinetHome() {
  await requireUser("/cabinet");
  const roles = await getRoles();
  if (roles.agency) redirect("/cabinet/agency");
  if (roles.hotel) redirect("/cabinet/hotel");
  if (roles.guide) redirect("/cabinet/guide");
  redirect("/account");
}
