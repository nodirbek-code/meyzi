import { TourEditor } from "@/components/cabinet/TourEditor";
import { requireUser } from "@/lib/session";

export default async function Page({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  await requireUser(`/cabinet/agency/tours/${slug}`);
  return <TourEditor slug={slug === "new" ? null : slug} />;
}
