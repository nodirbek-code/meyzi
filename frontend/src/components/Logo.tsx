import { BRAND } from "@/lib/brand";

/**
 * VAQTINCHALIK belgi (tog' + quyosh). Haqiqiy logo keyin tanlanadi — shu faylni almashtirish yetarli.
 */
export function LogoMark({ size = 32 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 40 40" aria-hidden>
      <rect width="40" height="40" rx="11" fill="#1B5737" />
      <circle cx="27" cy="13" r="4.5" fill="#E9BA67" />
      <path d="M5 31 L15 16 L21 24 L25 19 L35 31 Z" fill="#7DB890" />
      <path d="M5 31 L15 16 L18.5 21.2 L13 31 Z" fill="#ADD4B8" />
    </svg>
  );
}

export function Logo({ light = false }: { light?: boolean }) {
  return (
    <span className="inline-flex items-center gap-2.5">
      <LogoMark />
      <span className={`font-display text-xl font-extrabold tracking-tight ${light ? "text-white" : "text-forest-800"}`}>
        {BRAND.name}
      </span>
    </span>
  );
}
