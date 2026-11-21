import type { Metadata } from "next";

import { PartnerPage } from "@/components/PartnerPage";
import { BecomeGuideForm } from "@/components/PartnerForms";
import { apiGet } from "@/lib/api";
import { BRAND } from "@/lib/brand";
import { accountPhone } from "@/lib/phone";
import { requireUser } from "@/lib/session";
import type { Destination, Paginated } from "@/lib/types";

export const metadata: Metadata = { title: "Gid bo'lish" };

export default async function BecomeGuidePage() {
  const user = await requireUser("/guides/become");
  const d = await apiGet<Paginated<Destination>>("/catalog/destinations/", { query: { page_size: 50 } });
  return (
    <PartnerPage
      title={`${BRAND.name} gidi bo'ling`}
      text="Narxni o'zingiz belgilaysiz, ish kunlaringizni o'zingiz tanlaysiz."
      perks={[
        "Komissiya — 15%, qolgani sizga",
        "To'lov xizmatdan keyin 24 soat ichida",
        "Uchrashuv joylarini o'zingiz belgilaysiz",
        "Profil 48 soat ichida tekshiriladi",
      ]}
    >
      <BecomeGuideForm destinations={d.results} trustedPhone={accountPhone(user)} />
    </PartnerPage>
  );
}
