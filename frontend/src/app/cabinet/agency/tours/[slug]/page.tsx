import { TourEditor } from "@/components/cabinet/TourEditor";
import { requireRole } from "@/lib/roles";

export default async function Page({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  await requireRole("agency", `/cabinet/agency/tours/${slug}`);
  return <TourEditor slug={slug === "new" ? null : slug} />;
}
