import { AccountTabs } from "@/components/AccountTabs";
import { requireUser } from "@/lib/session";

export default async function AccountLayout({ children }: { children: React.ReactNode }) {
  const user = await requireUser("/account");
  const name = user.full_name || user.first_name || "sayohatchi";
  return (
    <div className="container-lz py-8 sm:py-10">
      <div className="mb-8 flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="eyebrow">Shaxsiy kabinet</p>
          <h1 className="mt-1 text-3xl">Xush kelibsiz, {name}</h1>
        </div>
        <AccountTabs />
      </div>
      {children}
    </div>
  );
}
