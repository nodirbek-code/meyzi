"use client";

import { useState } from "react";

import { phoneReady, VerifiedPhoneField, type VerifiedPhone } from "@/components/PhoneField";
import { Badge } from "@/components/ui";
import { api, ClientApiError } from "@/lib/client";
import { AMENITIES, money } from "@/lib/format";
import { galleryError, MAX_IMAGES, MAX_VIDEOS, MEDIA_ACCEPT, MEDIA_HINT, mediaKind } from "@/lib/uploads";

import { ErrorText, Loading, Panel } from "./Bits";
import { ReviewsReply } from "./ReviewsReply";
import { useAction, useData } from "./useData";

type Hotel = { name: string; slug: string; status: string; moderation_note: string; description: string; address: string; phone: string; email: string; amenities: string[]; commission_percent: string; check_in_time: string; check_out_time: string };
type Img = { id: number; kind: "image" | "video"; image: string; is_cover: boolean };
type Room = { id: number; name: string; description: string; capacity: number; beds: string; size_m2: number | null; price_per_night_uzs: number; total_rooms: number; amenities: string[]; is_active: boolean };

const STATUS: Record<string, string> = { pending: "Tekshiruvda", approved: "Tasdiqlangan", rejected: "Rad etilgan", suspended: "To'xtatilgan" };

export function HotelCabinet() {
  const hotel = useData<Hotel>("/hotels/me");
  const images = useData<Img[]>("/cabinet/hotel/images");
  const act = useAction();
  const [form, setForm] = useState<Partial<Hotel> | null>(null);
  const [phone, setPhone] = useState<VerifiedPhone | null>(null);
  const h = hotel.data;
  const f = { ...h, ...form } as Hotel;

  const [uploadError, setUploadError] = useState("");
  async function upload(files: FileList | null) {
    if (!files?.length) return;
    const list = Array.from(files);
    const err = galleryError(list, images.data ?? []);
    setUploadError(err ?? "");
    if (err) return;
    await act.run(async () => {
      let hasCover = !!images.data?.some((i) => i.is_cover);
      for (const file of list) {
        const fd = new FormData();
        fd.append("image", file);
        if (!hasCover && mediaKind(file) === "image") {
          fd.append("is_cover", "true"); // muqova — faqat rasm
          hasCover = true;
        }
        const res = await fetch("/api/proxy/cabinet/hotel/images", { method: "POST", body: fd });
        if (!res.ok) throw new ClientApiError(res.status, await res.json().catch(() => ({ detail: "Yuklashda xato" })));
      }
      images.reload();
    });
  }

  if (!h) return hotel.error ? <ErrorText text={hotel.error} /> : <Loading />;
  const ph = phone ?? { phone: h.phone, token: "" };
  const phoneChanged = ph.phone !== h.phone;
  const phoneOk = phoneReady(ph, h.phone);
  return (
    <div className="space-y-6">
      <div className="card flex flex-wrap items-center gap-3 p-4">
        <Badge tone={h.status === "approved" ? "green" : h.status === "pending" ? "gold" : "red"}>{STATUS[h.status]}</Badge>
        {h.moderation_note && <span className="text-sm text-ink-soft">{h.moderation_note}</span>}
        <span className="ml-auto text-xs text-ink-mute">Komissiya: {h.commission_percent}%</span>
        {h.status === "approved" && <a href={`/hotels/${h.slug}`} target="_blank" className="text-sm text-forest-700">Saytda ↗</a>}
      </div>
      <ErrorText text={act.error} />
      <Panel title="Profil">
        <form className="grid gap-4 sm:grid-cols-2" onSubmit={(e) => { e.preventDefault(); act.run(async () => { await api.patch("/hotels/me", { ...form, ...(phoneChanged ? { phone: ph.phone, phone_token: ph.token } : {}) }); setForm(null); setPhone(null); hotel.reload(); }); }}>
          <label><span className="label">Nomi</span><input className="input" value={f.name} onChange={(e) => setForm({ ...form, name: e.target.value })} /></label>
          <div><VerifiedPhoneField value={ph} onChange={setPhone} trustedPhone={h.phone} /></div>
          <label className="sm:col-span-2"><span className="label">Manzil</span><input className="input" value={f.address} onChange={(e) => setForm({ ...form, address: e.target.value })} /></label>
          <label><span className="label">Kirish vaqti</span><input className="input" type="time" value={f.check_in_time?.slice(0, 5)} onChange={(e) => setForm({ ...form, check_in_time: e.target.value })} /></label>
          <label><span className="label">Chiqish vaqti</span><input className="input" type="time" value={f.check_out_time?.slice(0, 5)} onChange={(e) => setForm({ ...form, check_out_time: e.target.value })} /></label>
          <div className="sm:col-span-2"><span className="label">Qulayliklar</span>
            <div className="flex flex-wrap gap-2">
              {Object.entries(AMENITIES).map(([k, l]) => {
                const on = f.amenities?.includes(k);
                return <button type="button" key={k} onClick={() => setForm({ ...form, amenities: on ? f.amenities.filter((x) => x !== k) : [...(f.amenities ?? []), k] })} className={`chip border ${on ? "border-forest-700 bg-forest-700 text-white" : "border-sand-200 bg-white"}`}>{l}</button>;
              })}
            </div>
          </div>
          <label className="sm:col-span-2"><span className="label">Tavsif</span><textarea className="input min-h-24" value={f.description} onChange={(e) => setForm({ ...form, description: e.target.value })} /></label>
          <div><button className="btn-primary" disabled={act.busy || (!form && !phoneChanged) || !phoneOk}>Saqlash</button></div>
        </form>
      </Panel>
      <Panel title="Rasm va video" action={<label className="btn-ghost cursor-pointer px-3 py-1.5 text-xs">{act.busy ? "Yuklanmoqda…" : "+ Yuklash"}<input type="file" multiple accept={MEDIA_ACCEPT} className="hidden" onChange={(e) => { upload(e.target.files); e.target.value = ""; }} /></label>}>
        <p className="mb-3 text-xs text-ink-mute">
          {MEDIA_HINT} Hozir: {(images.data ?? []).filter((i) => i.kind !== "video").length}/{MAX_IMAGES} rasm, {(images.data ?? []).filter((i) => i.kind === "video").length}/{MAX_VIDEOS} video.
        </p>
        <ErrorText text={uploadError} />
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          {images.data?.map((i) => (
            <div key={i.id} className={`relative overflow-hidden rounded-xl ${i.is_cover ? "ring-2 ring-sun-500" : ""}`}>
              {i.kind === "video" ? (
                <video src={i.image} className="aspect-square w-full object-cover" muted playsInline controls preload="metadata" />
              ) : (
                // eslint-disable-next-line @next/next/no-img-element
                <img src={i.image} alt="" className="aspect-square w-full object-cover" />
              )}
              <button className="absolute right-1 top-1 rounded-full bg-white/90 px-2 text-xs text-clay-700" onClick={() => act.run(async () => { await api.del(`/cabinet/hotel/images/${i.id}`); images.reload(); })}>✕</button>
            </div>
          ))}
          {images.data && !images.data.length && <p className="col-span-full text-sm text-ink-mute">Rasm yo&apos;q — mehmonlar rasmsiz mehmonxonani kam tanlaydi.</p>}
        </div>
      </Panel>
      <Panel title="Sharhlar">
        <ReviewsReply listPath="/cabinet/hotel/reviews?page_size=100" replyPath={(id) => `/cabinet/hotel/reviews/${id}/reply`} replyField="hotel_reply" />
      </Panel>
    </div>
  );
}

const EMPTY_ROOM = { name: "", description: "", capacity: 2, beds: "", size_m2: "", price_per_night_uzs: "", total_rooms: 1, amenities: [] as string[], is_active: true };

export function HotelRooms() {
  const rooms = useData<Room[]>("/cabinet/hotel/rooms");
  const act = useAction();
  const [edit, setEdit] = useState<(typeof EMPTY_ROOM & { id?: number }) | null>(null);

  async function save(e: React.FormEvent) {
    e.preventDefault();
    if (!edit) return;
    const body = { ...edit, size_m2: edit.size_m2 ? Number(edit.size_m2) : null, price_per_night_uzs: Number(edit.price_per_night_uzs) };
    const ok = await act.run(() => (edit.id ? api.patch(`/cabinet/hotel/rooms/${edit.id}`, body) : api.post("/cabinet/hotel/rooms", body)));
    if (ok) {
      setEdit(null);
      rooms.reload();
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-end"><button className="btn-gold" onClick={() => setEdit({ ...EMPTY_ROOM })}>+ Xona turi</button></div>
      <ErrorText text={act.error || rooms.error} />
      {edit && (
        <form onSubmit={save} className="card grid gap-4 p-5 sm:grid-cols-3">
          <label className="sm:col-span-2"><span className="label">Nomi *</span><input className="input" required value={edit.name} onChange={(e) => setEdit({ ...edit, name: e.target.value })} /></label>
          <label><span className="label">Karavotlar</span><input className="input" placeholder="1 katta" value={edit.beds} onChange={(e) => setEdit({ ...edit, beds: e.target.value })} /></label>
          <label><span className="label">Sig&apos;im (kishi) *</span><input className="input" type="number" min={1} value={edit.capacity} onChange={(e) => setEdit({ ...edit, capacity: Number(e.target.value) })} /></label>
          <label><span className="label">Xonalar soni *</span><input className="input" type="number" min={1} value={edit.total_rooms} onChange={(e) => setEdit({ ...edit, total_rooms: Number(e.target.value) })} /></label>
          <label><span className="label">1 kecha, so&apos;m *</span><input className="input" required inputMode="numeric" value={edit.price_per_night_uzs} onChange={(e) => setEdit({ ...edit, price_per_night_uzs: e.target.value.replace(/\D/g, "") })} /></label>
          <label><span className="label">Maydon, m²</span><input className="input" inputMode="numeric" value={edit.size_m2 ?? ""} onChange={(e) => setEdit({ ...edit, size_m2: e.target.value.replace(/\D/g, "") })} /></label>
          <label className="flex items-center gap-2 pt-6 text-sm"><input type="checkbox" checked={edit.is_active} onChange={(e) => setEdit({ ...edit, is_active: e.target.checked })} /> Sotuvda</label>
          <label className="sm:col-span-3"><span className="label">Tavsif</span><textarea className="input" value={edit.description} onChange={(e) => setEdit({ ...edit, description: e.target.value })} /></label>
          <div className="flex gap-2 sm:col-span-3">
            <button className="btn-primary" disabled={act.busy}>Saqlash</button>
            <button type="button" className="btn-ghost" onClick={() => setEdit(null)}>Bekor</button>
          </div>
        </form>
      )}
      {rooms.loading && <Loading />}
      {rooms.data?.map((r) => (
        <div key={r.id} className="card flex flex-wrap items-center justify-between gap-3 p-4">
          <div>
            <div className="font-semibold">{r.name} {!r.is_active && <Badge tone="gray">sotuvda emas</Badge>}</div>
            <div className="text-sm text-ink-soft">👥 {r.capacity} · {r.total_rooms} ta xona{r.beds && ` · ${r.beds}`}</div>
          </div>
          <div className="flex items-center gap-4">
            <b className="text-forest-700">{money(r.price_per_night_uzs)}</b>
            <button className="btn-ghost px-3 py-1.5 text-xs" onClick={() => setEdit({ ...EMPTY_ROOM, ...r, size_m2: r.size_m2 ? String(r.size_m2) : "", price_per_night_uzs: String(r.price_per_night_uzs) })}>Tahrirlash</button>
          </div>
        </div>
      ))}
      {rooms.data && !rooms.data.length && !edit && <p className="card p-8 text-center text-sm text-ink-soft">Xona turlarini qo&apos;shing — shundan keyin mehmonlar bron qila oladi.</p>}
    </div>
  );
}

type HB = { code: string; status: string; room_type: string; check_in: string; check_out: string; nights: number; rooms: number; guests: number; total_uzs: number; hotel_amount_uzs: number; contact_name: string; contact_phone: string; note: string };

export function HotelBookings() {
  const { data, error, loading, reload } = useData<{ results: HB[] }>("/cabinet/hotel/bookings?page_size=100");
  const act = useAction();
  const [confirm, setConfirm] = useState<string | null>(null);
  return (
    <div className="space-y-3">
      <ErrorText text={error || act.error} />
      {loading && <Loading />}
      {data && !data.results.length && <p className="card p-8 text-center text-sm text-ink-soft">Bronlar yo&apos;q.</p>}
      {data?.results.map((b) => (
        <div key={b.code} className="card space-y-2 p-4">
          <div className="flex flex-wrap justify-between gap-2">
            <div>
              <span className="font-mono text-xs text-ink-mute">{b.code}</span>
              <div className="font-semibold">{b.room_type} × {b.rooms}</div>
              <div className="text-sm text-ink-soft">{b.check_in} → {b.check_out} ({b.nights} kecha) · {b.guests} mehmon</div>
            </div>
            <div className="text-right"><Badge tone={b.status === "confirmed" ? "green" : b.status === "pending_payment" ? "gold" : "gray"}>{b.status}</Badge><div className="mt-1 text-sm">sizga <b>{money(b.hotel_amount_uzs)}</b></div></div>
          </div>
          <div className="text-sm">👤 {b.contact_name}, <a className="text-forest-700" href={`tel:${b.contact_phone}`}>{b.contact_phone}</a></div>
          {(b.status === "confirmed" || b.status === "pending_payment") && (confirm === b.code ? (
            <div className="text-sm">Mehmonga 100% qaytariladi. Ishonchingiz komilmi?{" "}
              <button className="font-semibold text-clay-700" onClick={() => act.run(async () => { await api.post(`/cabinet/hotel/bookings/${b.code}/cancel`, { reason: "Mehmonxona bekor qildi" }); setConfirm(null); reload(); })}>Ha</button>{" "}
              <button onClick={() => setConfirm(null)}>Yo&apos;q</button>
            </div>
          ) : <button className="text-sm text-clay-700" onClick={() => setConfirm(b.code)}>Bekor qilish</button>)}
        </div>
      ))}
    </div>
  );
}
