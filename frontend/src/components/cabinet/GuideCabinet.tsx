"use client";

import Link from "next/link";
import { useState } from "react";

import { Badge } from "@/components/ui";
import { api } from "@/lib/client";
import { dateLong, dateTime, LANGUAGE_NAMES, money, weekday } from "@/lib/format";
import type { Paginated } from "@/lib/types";

import { ErrorText, Loading, ModerationBanner, Panel, Stat } from "./Bits";
import { MeetingPoints } from "./MeetingPoints";
import { useAction, useData } from "./useData";

type Profile = { display_name: string; slug: string; status: string; destinations: string[]; moderation_note: string; rating: string; reviews_count: number; warnings_count: number; no_show_count: number };
type Row = {
  code: string; status: string; duration: string; start_date: string; days: number; starts_at: string; group_size: number; language: string;
  total_uzs: number; guide_amount_uzs: number; meeting_point: string; note: string; contact_name: string; contact_phone: string | null;
  respond_by: string | null; guide_penalty_usd: string; no_show: string;
};
type Busy = { id: number; date: string; note: string };

const STATUS: Record<string, { label: string; tone: "gold" | "green" | "gray" | "red" | "blue" }> = {
  requested: { label: "Javob kutilmoqda", tone: "gold" },
  accepted: { label: "Qabul qilindi — to'lov kutilmoqda", tone: "blue" },
  confirmed: { label: "To'langan", tone: "green" },
  completed: { label: "Yakunlangan", tone: "gray" },
  declined: { label: "Rad etildi", tone: "red" },
  expired: { label: "Javob berilmadi", tone: "gray" },
  cancelled: { label: "Bekor qilingan", tone: "red" },
};
const PROFILE_STATUS: Record<string, string> = { pending: "Tekshiruvda", approved: "Tasdiqlangan", rejected: "Rad etilgan", suspended: "To'xtatilgan" };
const DURATION: Record<string, string> = { half_day: "Yarim kun", full_day: "To'liq kun", multi_day: "Ko'p kunlik" };

export function GuideCabinet() {
  const profile = useData<Profile>("/guides/me");
  const bookings = useData<Paginated<Row>>("/cabinet/guide/bookings?page_size=100");
  const act = useAction();
  const [reason, setReason] = useState<Record<string, string>>({});
  const p = profile.data;
  const approved = p?.status === "approved";
  const doAct = (path: string, body?: unknown) => act.run(async () => { await api.post(path, body); bookings.reload(); });

  return (
    <div className="space-y-6">
      {p && (
        <div className="card flex flex-wrap items-center gap-3 p-4">
          <Badge tone={approved ? "green" : p.status === "pending" ? "gold" : "red"}>{PROFILE_STATUS[p.status]}</Badge>
          {approved && <Link href={`/guides/${p.slug}`} className="ml-auto text-sm text-forest-700">Ommaviy profil ↗</Link>}
          <div className="w-full">
            {p.status === "suspended" ? (
              p.moderation_note && <p className="text-sm text-clay-700">{p.moderation_note}</p>
            ) : (
              <ModerationBanner state={p.status} note={p.moderation_note} what="Gid profili" />
            )}
          </div>
        </div>
      )}
      {p && (
        <div className="grid gap-4 sm:grid-cols-4">
          <Stat label="Reyting" value={p.reviews_count ? `★ ${Number(p.rating).toFixed(1)}` : "—"} />
          <Stat label="Sharhlar" value={p.reviews_count} />
          <Stat label="Ogohlantirishlar" value={p.warnings_count} />
          <Stat label="Kelmay qolish" value={`${p.no_show_count} / 3`} />
        </div>
      )}
      <ErrorText text={act.error || bookings.error} />
      <Panel title="So'rovlar va bronlar">
        {bookings.loading && <Loading />}
        {bookings.data && !bookings.data.results.length && <p className="text-sm text-ink-mute">Hali so&apos;rov yo&apos;q.</p>}
        <div className="space-y-3">
          {bookings.data?.results.map((b) => {
            const st = STATUS[b.status];
            const started = new Date(b.starts_at).getTime() < Date.now();
            const canNoShow = b.status === "confirmed" && Date.now() > new Date(b.starts_at).getTime() + 3600_000;
            return (
              <div key={b.code} className="rounded-xl border border-sand-200 p-4">
                <div className="flex flex-wrap justify-between gap-2">
                  <div>
                    <span className="font-mono text-xs text-ink-mute">{b.code}</span>
                    <div className="font-semibold">{DURATION[b.duration]}{b.days > 1 && ` · ${b.days} kun`} · {b.group_size} kishi · {LANGUAGE_NAMES[b.language] ?? b.language}</div>
                    <div className="text-sm text-ink-soft">{dateTime(b.starts_at)} · 📍 {b.meeting_point}</div>
                  </div>
                  <div className="text-right">
                    <Badge tone={st?.tone ?? "gray"}>{st?.label ?? b.status}</Badge>
                    <div className="mt-1 text-sm">Sizga <b className="text-forest-700">{money(b.guide_amount_uzs)}</b></div>
                  </div>
                </div>
                <div className="mt-2 text-sm">👤 {b.contact_name}{b.contact_phone ? <>, <a href={`tel:${b.contact_phone}`} className="text-forest-700">{b.contact_phone}</a></> : <span className="text-xs text-ink-mute"> (telefon to&apos;lovdan keyin ochiladi)</span>}</div>
                {b.note && <div className="text-xs text-ink-soft">Izoh: {b.note}</div>}
                {b.status === "requested" && b.respond_by && <div className="mt-1 text-xs text-sun-700">Javob muddati: {dateTime(b.respond_by)}</div>}
                {Number(b.guide_penalty_usd) > 0 && <div className="mt-1 text-xs text-clay-700">Jarima: ${b.guide_penalty_usd}</div>}
                <div className="mt-3 flex flex-wrap items-center gap-2">
                  {b.status === "requested" && approved && (
                    <>
                      <button className="btn-primary px-4 py-1.5" disabled={act.busy} onClick={() => doAct(`/cabinet/guide/bookings/${b.code}/accept`)}>Qabul qilish</button>
                      <input className="input w-48 py-1.5" placeholder="Rad etish sababi" value={reason[b.code] ?? ""} onChange={(e) => setReason({ ...reason, [b.code]: e.target.value })} />
                      <button className="btn-ghost px-4 py-1.5" disabled={act.busy} onClick={() => doAct(`/cabinet/guide/bookings/${b.code}/decline`, { reason: reason[b.code] ?? "" })}>Rad etish</button>
                    </>
                  )}
                  {(b.status === "accepted" || b.status === "confirmed") && !started && (
                    <button className="text-sm text-clay-700" disabled={act.busy} onClick={() => doAct(`/cabinet/guide/bookings/${b.code}/cancel`, { reason: "Gid bekor qildi" })}>
                      Bekor qilish (jarima vaqtga qarab)
                    </button>
                  )}
                  {canNoShow && (
                    <button className="btn-ghost px-4 py-1.5" disabled={act.busy} onClick={() => doAct(`/cabinet/guide/bookings/${b.code}/tourist-no-show`)}>Turist kelmadi (30% kompensatsiya)</button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </Panel>
    </div>
  );
}


/** Gidning ishlamaydigan kunlari (turistlar bu kunlarga bron qila olmaydi). */
export function GuideSchedule() {
  const busy = useData<Busy[]>("/cabinet/guide/unavailable-dates");
  const act = useAction();
  const [newBusy, setNewBusy] = useState("");
  return (
    <div className="space-y-4">
      <ErrorText text={act.error || busy.error} />
      <Panel title="Ishlamaydigan kunlarim">
        <form className="mb-3 flex gap-2" onSubmit={(e) => { e.preventDefault(); act.run(async () => { await api.post("/cabinet/guide/unavailable-dates", { date: newBusy }); setNewBusy(""); busy.reload(); }); }}>
          <input className="input w-auto" type="date" required value={newBusy} onChange={(e) => setNewBusy(e.target.value)} />
          <button className="btn-primary">Qo&apos;shish</button>
        </form>
        <div className="flex flex-wrap gap-2">
          {busy.data?.map((d) => (
            <span key={d.id} className="chip bg-sand-100 text-ink">
              {weekday(d.date)}, {dateLong(d.date)}
              <button aria-label="O'chirish" className="text-clay-700" onClick={() => act.run(async () => { await api.del(`/cabinet/guide/unavailable-dates/${d.id}`); busy.reload(); })}>✕</button>
            </span>
          ))}
          {busy.data && !busy.data.length && <span className="text-sm text-ink-mute">Belgilanmagan.</span>}
        </div>
      </Panel>
    </div>
  );
}

/** Uchrashuv joylari — gid ishlaydigan shaharlar bo'yicha. */
export function GuideMeetingPoints() {
  const profile = useData<Profile>("/guides/me");
  if (!profile.data) return profile.error ? <ErrorText text={profile.error} /> : <Loading />;
  return (
    <div className="space-y-4">
      <p className="text-sm text-ink-mute">
        Turist bron qilganda shu joylardan birini tanlaydi. Yangi joy qo&apos;shsangiz yoki o&apos;zgartirsangiz — profil qayta
        tekshiruvga yuboriladi.
      </p>
      <MeetingPoints cities={profile.data.destinations} />
    </div>
  );
}
