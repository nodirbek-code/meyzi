"use client";

import { ReviewsReply } from "@/components/cabinet/ReviewsReply";

export default function Page() {
  return <ReviewsReply listPath="/cabinet/reviews?page_size=100" replyPath={(id) => `/cabinet/reviews/${id}/reply`} replyField="agency_reply" />;
}
