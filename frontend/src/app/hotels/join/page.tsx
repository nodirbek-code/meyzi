import type { Metadata } from "next";

import { PartnerPage } from "@/components/PartnerPage";
import { JoinHotelForm } from "@/components/PartnerForms";
import { apiGet } from "@/lib/api";
import { BRAND } from "@/lib/brand";
import { accountPhone } from "@/lib/phone";
import { requireUser } from "@/lib/session";
import type { Destination, Paginated } from "@/lib/types";

export const metadata: Metadata = { title: "Mehmonxonani qo'shish" };

export default async function JoinHotelPage() {
  const user = await requireUser("/hotels/join");
  const d = await apiGet<Paginated<Destination>>("/catalog/destinations/", { query: { page_size: 50 } });
  return (
    <PartnerPage
      title={`Joyingizni ${BRAND.name}'ga qo'shing`}
      text="Mehmonxona, mehmon uyi, hostel yoki dam olish maskani — sayohatchilar sizni topsin."
      perks={[
        "Xona turlari, narxlar va bo'sh xonalarni kabinetda boshqarasiz",
        "Bronlar to'langandan keyin tasdiqlanadi",
        "Bekor qilish siyosatini o'zingiz tanlaysiz",
        "Ariza tekshiruvdan so'ng faollashadi",
      ]}
    >
      <JoinHotelForm destinations={d.results} trustedPhone={accountPhone(user)} />
    </PartnerPage>
  );
}
