const MONTHS = ["yanvar", "fevral", "mart", "aprel", "may", "iyun", "iyul", "avgust", "sentabr", "oktabr", "noyabr", "dekabr"];
const WEEKDAYS = ["Ya", "Du", "Se", "Ch", "Pa", "Ju", "Sh"];

/** 890000 -> "890 000 so'm" */
export function money(value: number | string, suffix = " so'm"): string {
  const n = Math.round(Number(value) || 0);
  return n.toString().replace(/\B(?=(\d{3})+(?!\d))/g, " ") + suffix;
}

function toDate(value: string | Date): Date {
  if (value instanceof Date) return value;
  // "2026-11-21" — mahalliy sana sifatida (UTC siljishisiz)
  if (/^\d{4}-\d{2}-\d{2}$/.test(value)) {
    const [y, m, d] = value.split("-").map(Number);
    return new Date(y, m - 1, d);
  }
  return new Date(value);
}

/** "21 noyabr" yoki yil bilan "21 noyabr 2026" */
export function dateLong(value: string | Date, withYear = false): string {
  const d = toDate(value);
  return `${d.getDate()} ${MONTHS[d.getMonth()]}${withYear ? ` ${d.getFullYear()}` : ""}`;
}

export function weekday(value: string | Date): string {
  return WEEKDAYS[toDate(value).getDay()];
}

export function time(value: string | null | undefined): string {
  return value ? value.slice(0, 5) : "";
}

const TZ = "Asia/Tashkent";

/** Sana va vaqt doim Toshkent vaqtida (server UTC'da ishlasa ham) */
export function dateTime(value: string): string {
  const parts = Object.fromEntries(
    new Intl.DateTimeFormat("en-GB", {
      timeZone: TZ,
      year: "numeric",
      month: "numeric",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      hourCycle: "h23",
    })
      .formatToParts(new Date(value))
      .map((p) => [p.type, p.value]),
  );
  return `${Number(parts.day)} ${MONTHS[Number(parts.month) - 1]} ${parts.year}, ${parts.hour}:${parts.minute}`;
}

/** "+998901234567" → "+998 90 123 45 67" */
export function phone(value: string | null | undefined): string {
  const d = (value ?? "").replace(/\D/g, "");
  if (d.length === 12 && d.startsWith("998"))
    return `+998 ${d.slice(3, 5)} ${d.slice(5, 8)} ${d.slice(8, 10)} ${d.slice(10)}`;
  return value ?? "";
}

export function duration(days: number, nights = 0): string {
  return nights ? `${days} kun / ${nights} kecha` : `${days} kun`;
}

export const POLICY_LABEL: Record<string, string> = {
  free: "Bepul bekor qilish",
  partial: "Qisman qaytarish",
  non_refundable: "Qaytarilmaydi",
};

export const BOOKING_STATUS: Record<string, { label: string; tone: "gold" | "green" | "gray" | "red" | "blue" }> = {
  pending_payment: { label: "To'lov kutilmoqda", tone: "gold" },
  confirmed: { label: "Tasdiqlangan", tone: "green" },
  completed: { label: "Yakunlangan", tone: "blue" },
  cancelled: { label: "Bekor qilingan", tone: "red" },
  expired: { label: "Muddati o'tgan", tone: "gray" },
};

export const LANGUAGE_NAMES: Record<string, string> = {
  uz: "O'zbek", ru: "Rus", en: "Ingliz", de: "Nemis", fr: "Fransuz", es: "Ispan",
  it: "Italyan", tr: "Turk", zh: "Xitoy", ja: "Yapon", ko: "Koreys", ar: "Arab",
};
export const SPECIALIZATIONS: Record<string, string> = {
  history: "Tarix va me'morchilik", city: "Shahar sayohati", mountain: "Tog' va trekking", nature: "Tabiat",
  food: "Milliy taomlar", craft: "Hunarmandchilik", religious: "Ziyorat", photo: "Fotosayohat",
};
export const AMENITIES: Record<string, string> = {
  wifi: "Wi-Fi", parking: "Avtoturargoh", breakfast: "Nonushta", ac: "Konditsioner", pool: "Basseyn",
  spa: "Spa", gym: "Sport zal", restaurant: "Restoran", transfer: "Transfer", pets: "Uy hayvonlari",
};
export const HOTEL_KIND: Record<string, string> = {
  hotel: "Mehmonxona", hostel: "Hostel", guesthouse: "Mehmon uyi", resort: "Dam olish maskani",
};
