import type { Metadata } from "next";

import { AddPhoneViaTelegram, AttachEmail, ProfileForm } from "@/components/ProfileForms";
import { Badge } from "@/components/ui";
import { requireUser } from "@/lib/session";

export const metadata: Metadata = { title: "Profil" };

export default async function ProfilePage() {
  const user = await requireUser("/account/profile");
  return (
    <div className="grid max-w-3xl gap-6">
      <section className="card p-6">
        <h2 className="mb-4 text-lg font-bold">Shaxsiy ma&apos;lumotlar</h2>
        <ProfileForm user={user} />
      </section>
      <section className="card space-y-3 p-6">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold">Email</h2>
          {user.email && <Badge tone={user.email_verified ? "green" : "gold"}>{user.email_verified ? "Tasdiqlangan" : "Tasdiqlanmagan"}</Badge>}
        </div>
        <p className="text-sm text-ink-soft">{user.email || "Email ulanmagan. Email qo'shsangiz, bron va to'lov xabarlari unga keladi."}</p>
        {!(user.email && user.email_verified) && <AttachEmail current={user.email} />}
      </section>
      <section className="card space-y-3 p-6">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold">Telefon</h2>
          {user.phone && <Badge tone={user.phone_verified ? "green" : "gold"}>{user.phone_verified ? "Tasdiqlangan" : "Tasdiqlanmagan"}</Badge>}
        </div>
        <p className="text-sm text-ink-soft">
          {user.phone || "Telefon raqam ulanmagan. Qo'shsangiz, bron va to'lov xabarlari Telegram'ga keladi va saytga raqam bilan ham kira olasiz."}
        </p>
        {!user.phone && <AddPhoneViaTelegram />}
      </section>
    </div>
  );
}
