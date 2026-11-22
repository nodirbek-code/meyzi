import Link from "next/link";

import { apiGet } from "@/lib/api";
import { getUser } from "@/lib/session";
import type { DestinationShort, Paginated } from "@/lib/types";

import { HeaderSearch } from "./HeaderSearch";
import { LanguageSwitcher } from "./LanguageSwitcher";
import { Logo } from "./Logo";
import { MobileNav } from "./MobileNav";
import { NavLinks } from "./NavLinks";
import { UserMenu } from "./UserMenu";

export const NAV = [
  { href: "/tours", label: "Turlar" },
  { href: "/guides", label: "Gidlar" },
  { href: "/hotels", label: "Mehmonxonalar" },
  { href: "/destinations", label: "Yo'nalishlar" },
  { href: "/hamkorlik", label: "Hamkorlik" },
];

async function popularDestinations(): Promise<DestinationShort[]> {
  try {
    const r = await apiGet<Paginated<DestinationShort>>("/catalog/destinations/", { query: { page_size: 8 } });
    return r.results.map(({ id, name, slug }) => ({ id, name, slug }));
  } catch {
    return [];
  }
}

export async function Header() {
  const [user, destinations] = await Promise.all([getUser(), popularDestinations()]);
  return (
    <header
      className="sticky top-0 z-40 border-b border-sand-200 bg-white/95 backdrop-blur"
      style={{ top: "env(safe-area-inset-top, 0px)" }}
    >
      <div className="container-lz flex h-16 items-center justify-between gap-4">
        <Link href="/" aria-label="Bosh sahifa" className="shrink-0">
          <Logo />
        </Link>
        <NavLinks items={NAV} />
        <div className="flex items-center gap-1.5 sm:gap-3">
          <HeaderSearch destinations={destinations} />
          <LanguageSwitcher />
          {user ? (
            <UserMenu user={user} />
          ) : (
            <>
              <Link href="/login" className="hidden px-2 text-sm font-semibold text-ink-soft hover:text-forest-700 sm:inline">
                Kirish
              </Link>
              <Link href="/register" className="btn-primary hidden px-4 py-2 sm:inline-flex">
                Ro&apos;yxatdan o&apos;tish
              </Link>
            </>
          )}
          <MobileNav items={NAV} loggedIn={!!user} />
        </div>
      </div>
    </header>
  );
}
