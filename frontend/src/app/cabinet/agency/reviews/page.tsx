import { AgencyReviews } from "@/components/cabinet/ReviewsReply";
import { requireRole } from "@/lib/roles";

export default async function Page() {
  await requireRole("agency", "/cabinet/agency/reviews");
  return <AgencyReviews />;
}
