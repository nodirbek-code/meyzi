import type { Metadata } from "next";
import { redirect } from "next/navigation";

import { ControlLogin } from "@/components/control/ControlLogin";
import { getUser } from "@/lib/session";

export const metadata: Metadata = { title: "Admin paneli", robots: { index: false, follow: false } };

export default async function ControlLoginPage() {
  const user = await getUser();
  if (user?.is_staff) redirect("/control");
  return (
    <div className="container-lz flex min-h-[70vh] items-center justify-center py-10">
      <ControlLogin />
    </div>
  );
}
