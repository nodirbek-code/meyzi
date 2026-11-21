/* eslint-disable @next/next/no-img-element */
import { BRAND } from "@/lib/brand";

/**
 * MEYZI logotipi (fayllar: public/brand/). Manba: D:\lazuri\brand\ — "Minimalist MEYZI logotipi.png".
 * `light` — to'q fon ustida (footer, tabiat panellari) oq variant.
 */
export function LogoMark({ size = 34, light = false }: { size?: number; light?: boolean }) {
  // belgining nisbati 407×247
  return (
    <img
      src={light ? "/brand/meyzi-mark-white.png" : "/brand/meyzi-mark.png"}
      alt=""
      width={Math.round((size * 407) / 247)}
      height={size}
      className="shrink-0"
      aria-hidden
    />
  );
}

export function Logo({ light = false, size = "md" }: { light?: boolean; size?: "md" | "lg" }) {
  const h = size === "lg" ? 44 : 36;
  return (
    <span className="inline-flex items-center gap-2.5" aria-label={BRAND.name}>
      <LogoMark size={h} light={light} />
      <img
        src={light ? "/brand/meyzi-wordmark-white.png" : "/brand/meyzi-wordmark.png"}
        alt={BRAND.name}
        height={Math.round(h * 0.55)}
        width={Math.round((h * 0.55 * 698) / 122)}
        className="shrink-0"
      />
    </span>
  );
}

/** Ilova ikonkasi (to'q ko'k kvadrat, oq M) */
export function AppIcon({ size = 56 }: { size?: number }) {
  return <img src="/brand/meyzi-app-icon-192.png" alt={`${BRAND.name} ilovasi`} width={size} height={size} className="rounded-[22%] shadow-card" />;
}
