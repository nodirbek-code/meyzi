import { GuideReviews } from "@/components/cabinet/ReviewsReply";
import { requireRole } from "@/lib/roles";

export default async function Page() {
  await requireRole("guide", "/cabinet/guide/reviews");
  return <GuideReviews />;
}
