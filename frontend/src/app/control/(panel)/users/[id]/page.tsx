import Link from "next/link";

import { UserActions } from "@/components/control/UserActions";
import { controlGet, requireStaff } from "@/lib/control-server";

type Stat = { total: number; completed: number };
type ControlUser = {
  id: number;
  full_name: string;
  email: string;
  email_verified: boolean;
  phone: string;
  phone_verified: boolean;
  role_display: string;
  date_joined: string;
  last_login: string | null;
  is_active: boolean;
  is_staff: boolean;
  is_superuser: boolean;
  is_me: boolean;
  staff_area: string;
  staff_title: string;
  telegram_linked: boolean;
  google_linked: boolean;
  partner: { kind: string; name: string; role: string }[];
  bookings: { tours: Stat; hotels: Stat; guides: Stat };
  completed_trips: number;
  history: { user: string; message: string; at: string }[];
};

const fmt = (iso: string | null) =>
  iso ? new Date(iso).toLocaleString("uz-UZ", { day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit" }) : "—";

export default async function ControlUserPage({ params }: { params: Promise<{ id: string }> }) {
  await requireStaff();
  const { id } = await params;
  const u = await controlGet<ControlUser>(`/users/${id}/`);
  const locked = u.is_me
    ? "Bu sizning akkauntingiz — o'z huquqlaringizni o'zgartira olmaysiz."
    : u.is_superuser
      ? "Asosiy admin (superuser) — huquqlari bu yerda o'zgarmaydi."
      : "";
  const rows: [string, string][] = [
    ["Email", `${u.email || "—"}${u.email && u.email_verified ? " ✓" : ""}`],
    ["Telefon", `${u.phone || "—"}${u.phone && u.phone_verified ? " ✓" : ""}`],
    ["Turi", u.role_display],
    ["Huquq", u.is_staff ? u.staff_title : "Oddiy foydalanuvchi"],
    ["Holati", u.is_active ? "Faol" : "Bloklangan"],
    ["Kirish usullari", [u.google_linked && "Google", u.telegram_linked && "Telegram"].filter(Boolean).join(", ") || "Email/telefon"],
    ["Ro'yxatdan o'tgan", fmt(u.date_joined)],
    ["Oxirgi kirish", fmt(u.last_login)],
    [
      "Bronlar (jami / yakunlangan)",
      `Tur ${u.bookings.tours.total}/${u.bookings.tours.completed} · Mehmonxona ${u.bookings.hotels.total}/${u.bookings.hotels.completed} · Gid ${u.bookings.guides.total}/${u.bookings.guides.completed}`,
    ],
  ];

  return (
    <div className="space-y-5">
      <Link href="/control/manage/user" className="text-sm text-ink-mute hover:text-forest-700">‹ Foydalanuvchilar</Link>
      <h2 className="text-2xl">{u.full_name || u.email || u.phone}</h2>

      <section className="card p-5">
        <dl className="grid gap-x-6 gap-y-2 text-sm sm:grid-cols-[14rem_1fr]">
          {rows.map(([k, v]) => (
            <div key={k} className="contents">
              <dt className="text-ink-mute">{k}</dt>
              <dd className="font-medium">{v}</dd>
            </div>
          ))}
          {u.partner.map((p, i) => (
            <div key={i} className="contents">
              <dt className="text-ink-mute">{p.kind}</dt>
              <dd className="font-medium">
                {p.name} <span className="text-ink-mute">({p.role})</span>
              </dd>
            </div>
          ))}
        </dl>
      </section>

      <UserActions id={u.id} isActive={u.is_active} isStaff={u.is_staff} staffArea={u.staff_area} locked={locked} />

      {u.history.length > 0 && (
        <section className="card p-5">
          <h3 className="mb-3 font-semibold">Tarix</h3>
          <ul className="space-y-1 text-sm">
            {u.history.map((h, i) => (
              <li key={i}>
                <span className="text-ink-mute">{fmt(h.at)}</span> · {h.message} <span className="text-ink-mute">— {h.user}</span>
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}
