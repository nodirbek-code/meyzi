import type { Config } from "tailwindcss";

/**
 * Tabiat palitrasi: o'rmon yashili (asosiy), quyosh oxrasi (urg'u), tuproq (dam olish kunlari, ogohlantirish),
 * osmon (ma'lumot), qum (fon), ko'mir (matn).
 *
 * `gold`, `turquoise` — eski nomlar (hali qayta dizayn qilinmagan sahifalar uchun) — yangi
 * ranglarga ulangan. Sahifalar yangilangani sari `forest`/`sun`/`sky` ga o'tkaziladi.
 */
const forest = {
  50: "#EEF6F0",
  100: "#D6EADB",
  200: "#ADD4B8",
  300: "#7DB890",
  400: "#4F9A6B",
  500: "#2F7F51",
  600: "#226B43", // tugmalar
  700: "#1B5737", // asosiy
  800: "#15432B",
  900: "#0E2E1E", // footer
};
const sun = {
  50: "#FDF7EC",
  100: "#F9EBCF",
  200: "#F2D49C",
  300: "#E9BA67",
  500: "#D99A2B", // urg'u
  600: "#B87D1C",
  700: "#8E5F15",
};
const sky = { 50: "#EEF6FA", 100: "#D7EBF3", 300: "#8CC3DA", 500: "#2D7C9C", 700: "#1F5870" };

export default {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        forest,
        sun,
        sky,
        clay: { 50: "#FBF1EC", 100: "#F5DDD1", 500: "#C1623A", 700: "#8F4426" }, // tuproq
        sand: { 50: "#FBFAF6", 100: "#F5F2EA", 200: "#E8E2D3", 300: "#D6CDB8" }, // fon
        ink: { DEFAULT: "#18221D", soft: "#4A5650", mute: "#7E8882" }, // matn
        // eski nomlar → yangi ranglar
        gold: sun,
        turquoise: sky,
      },
      fontFamily: {
        display: ["var(--font-display)", "system-ui", "sans-serif"],
        sans: ["var(--font-sans)", "system-ui", "sans-serif"],
        brand: ["var(--font-brand)", "system-ui", "sans-serif"],
      },
      boxShadow: {
        card: "0 1px 2px rgba(24,34,29,.05), 0 6px 20px -10px rgba(24,34,29,.16)",
        lift: "0 2px 4px rgba(24,34,29,.06), 0 18px 36px -16px rgba(24,34,29,.28)",
      },
      borderRadius: { xl2: "1.125rem" },
    },
  },
  plugins: [],
} satisfies Config;
