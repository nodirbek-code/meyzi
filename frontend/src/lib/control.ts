/** Saytdagi admin paneli (/control): turlar, holatlar va yorliqlar. */

export type ControlKind = "application" | "hotel" | "guide" | "tour" | "agency" | "review" | "hotel_review" | "guide_review";

export type QueueCard = { kind: ControlKind; title: string; icon: string; count: number; oldest: string; overdue: boolean; state: string; with_moderator: number };

/** "admin" — asosiy admin; "hotels" / "guides" — soha moderatori */
export type StaffRole = "admin" | "hotels" | "guides";

export type Dashboard = {
  role: StaffRole;
  role_title: string;
  queue: QueueCard[];
  queue_total: number;
  money: null | {
    today: Money;
    week: Money;
    month: Money;
    chart: { day: string; value: number; pct: number }[];
    by_kind: { label: string; count: number; commission: number }[];
    pending_payment: number;
    new_today: number;
    cancelled_today: number;
  };
  alerts: { text: string }[];
  platform: { label: string; value: number }[];
  recent_actions: { user: string; object: string; message: string; at: string }[];
};
type Money = { count: number; total: number; commission: number };

export type ListRow = { id: number; title: string; subtitle: string; status: string; waiting: string; overdue: boolean };
export type ListResponse = { kind: ControlKind; title: string; states: string[]; state: string; default_state: string; two_stage: boolean; can_suspend: boolean; import_key?: string | null; results: ListRow[]; counts: Record<string, number> };

export type Item = {
  kind: ControlKind;
  title: string;
  id: number;
  name: string;
  state: string;
  public_url: string | null;
  can_suspend: boolean;
  two_stage: boolean;
  role: StaffRole;
  /** Joriy ishchiga ruxsat etilgan amallar: approve | precheck | return | suspend | activate */
  actions: string[];
  precheck: { by: string; at: string; note: string } | null;
  data: Record<string, unknown>;
  history: { user: string; message: string; at: string }[];
};

export const REVIEW_KINDS: ControlKind[] = ["review", "hotel_review", "guide_review"];

export const STATE_LABEL: Record<string, string> = {
  precheck: "Moderatorda",
  pending: "Tekshiruvda",
  rejected: "Qaytarilgan",
  approved: "Tasdiqlangan",
  suspended: "To'xtatilgan",
};
/** Sharhlarda "qaytarish" — yashirish */
export const REVIEW_STATE_LABEL: Record<string, string> = { pending: "Tekshiruvda", rejected: "Yashirilgan", approved: "E'lon qilingan" };

/** Ikki bosqichli bo'limlar (mehmonxona, gid): moderator → admin */
export const TWO_STAGE_LABEL: Record<string, string> = {
  precheck: "Moderator tekshiruvida",
  pending: "Admin tasdig'ida",
  rejected: "Qaytarilgan",
  approved: "Tasdiqlangan",
  suspended: "To'xtatilgan",
};

export const STATE_TONE: Record<string, "gold" | "red" | "green" | "gray" | "blue"> = {
  precheck: "blue",
  pending: "gold",
  rejected: "red",
  approved: "green",
  suspended: "gray",
};

/** Batafsil sahifada maydon nomlari (ko'rsatilmaydiganlar — HIDDEN). */
export const FIELD_LABEL: Record<string, string> = {
  name: "Nomi",
  title: "Nomi",
  display_name: "Ism familiya",
  agency_name: "Agentlik",
  contact_person: "Mas'ul shaxs",
  account_email: "Akkaunt emaili",
  kind: "Turi",
  stars: "Yulduz",
  destination_name: "Shahar",
  destination_names: "Shaharlar",
  address: "Manzil",
  phone: "Telefon",
  email: "Email",
  telegram: "Telegram",
  website: "Sayt",
  inn: "STIR",
  license_number: "Litsenziya",
  description: "Tavsif",
  short_description: "Qisqa tavsif",
  bio: "O'zi haqida",
  message: "Izoh (arizada)",
  amenities: "Qulayliklar",
  check_in_time: "Kirish vaqti",
  check_out_time: "Chiqish vaqti",
  languages: "Tillar",
  specializations: "Yo'nalishlar",
  experience_years: "Tajriba (yil)",
  certificate_number: "Sertifikat raqami",
  price_half_day_uzs: "Yarim kun narxi",
  price_full_day_uzs: "To'liq kun narxi",
  price_per_day_uzs: "Ko'p kunlik (1 kun)",
  group_surcharge_percent: "Guruh ustamasi (%)",
  max_group_size: "Guruh hajmi (max)",
  duration_days: "Kunlar",
  duration_nights: "Tunlar",
  departure_time: "Jo'nash vaqti",
  return_time: "Qaytish vaqti",
  meeting_point: "Uchrashuv joyi",
  meeting_map_url: "Xarita havolasi",
  price_uzs: "Narx",
  price_note: "Narx izohi",
  cancellation_policy: "Bekor qilish siyosati",
  categories: "Toifalar",
  included: "Narxga kiradi",
  not_included: "Narxga kirmaydi",
  what_to_bring: "O'zi bilan olish",
  commission_percent: "Komissiya (%)",
  rating: "Reyting",
  reviews_count: "Sharhlar soni",
  about: "Nima haqida",
  author: "Muallif",
  text: "Sharh matni",
  reply: "Hamkor javobi",
  created_at: "Yuborilgan",
  updated_at: "Oxirgi o'zgarish",
};

/** Alohida ko'rsatiladigan yoki texnik maydonlar */
export const SPECIAL_FIELDS = new Set([
  "id", "slug", "status", "moderation_status", "moderation_note", "phone_token", "photo", "logo", "media", "rooms",
  "members", "itinerary", "departures", "meeting_points", "certificate_url", "has_certificate_file", "certificate_file",
  "destination", "destinations", "places", "installment", "meeting_latitude", "meeting_longitude", "is_platform",
  "auto_publish", "is_verified", "is_certified", "published_at", "warnings_count", "no_show_count", "user",
]);

// ---------- Boshqarish (CRUD) ----------

export type CrudField = {
  name: string;
  label: string;
  type: "text" | "textarea" | "number" | "checkbox" | "select" | "fk" | "multiselect" | "tags" | "image" | "file" | "date" | "time" | "datetime" | "email" | "url";
  required: boolean;
  help: string;
  options?: [string, string][];
  extra?: boolean;
};

export type CrudMeta = { key: string; title: string; group: string; can_create: boolean; can_delete: boolean; can_import?: boolean; hint: string; columns: string[]; count?: number };

export type CrudList = CrudMeta & {
  schema: CrudField[];
  results: { id: number; cells: string[]; editable: boolean; moderation_url: string }[];
  count: number;
  page: number;
  pages: number;
};

export type CrudDetail = CrudMeta & { schema: CrudField[]; id: number; name: string; editable: boolean; data: Record<string, unknown> };
