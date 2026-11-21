import type { Metadata } from "next";

import { AttachPhone, ProfileForm, VerifyEmail } from "@/components/ProfileForms";
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
        <p className="text-sm text-ink-soft">{user.email || "Email ulanmagan"}</p>
        {user.email && !user.email_verified && <VerifyEmail />}
      </section>
      <section className="card space-y-3 p-6">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold">Telefon</h2>
          {user.phone && <Badge tone={user.phone_verified ? "green" : "gold"}>{user.phone_verified ? "Tasdiqlangan" : "Tasdiqlanmagan"}</Badge>}
        </div>
        <p className="text-sm text-ink-soft">{user.phone || "Telefon ulanmagan. Raqamingizni ulang — bron formalarida qayta tasdiqlash so'ralmaydi."}</p>
        <AttachPhone current={user.phone} />
      </section>
    </div>
  );
}
