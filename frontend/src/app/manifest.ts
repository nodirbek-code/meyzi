import type { MetadataRoute } from "next";

import { BRAND } from "@/lib/brand";

/** Telefonda "Bosh ekranga qo'shish" uchun (PWA manifest) */
export default function manifest(): MetadataRoute.Manifest {
  return {
    name: BRAND.name,
    short_name: BRAND.name,
    description: BRAND.description,
    start_url: "/",
    display: "standalone",
    background_color: "#FBFAF6",
    theme_color: "#06192B",
    icons: [
      { src: "/brand/meyzi-app-icon-192.png", sizes: "192x192", type: "image/png" },
      { src: "/brand/meyzi-app-icon-512.png", sizes: "512x512", type: "image/png" },
    ],
  };
}
