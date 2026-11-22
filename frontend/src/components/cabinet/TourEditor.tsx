"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { Badge } from "@/components/ui";
import { api, ClientApiError } from "@/lib/client";
import { dateLong, weekday } from "@/lib/format";
import type { Category, Destination, Paginated } from "@/lib/types";
import { galleryError, MAX_IMAGES, MAX_VIDEOS, MEDIA_ACCEPT, MEDIA_HINT, mediaKind } from "@/lib/uploads";

import { TOUR_STATUS } from "./AgencyTours";
import { parseCoords } from "./MeetingPoints";
import { ErrorText, LinesInput, Loading, ModerationBanner, Panel } from "./Bits";
import { useAction, useData } from "./useData";

type Item = { start_time: string | null; end_time: string | null; title: string; description: string; is_extra_cost: boolean };
type Day = { day_number: number; title: string; description: string; items: Item[] };
type Media = { id: number; kind: "image" | "video"; file: string; is_cover: boolean };
type Tour = {
  slug?: string;
  title: string;
  short_description: string;
  description: string;
  destination: string;
  categories: string[];
  duration_days: number;
  duration_nights: number;
  max_group_size: number;
  departure_time: string | null;
  return_time: string | null;
  meeting_point: string;
  meeting_latitude: string | null;
  meeting_longitude: string | null;
  meeting_map_url: string;
  price_uzs: number | string;
  price_note: string;
  cancellation_policy: string;
  included: string[];
  not_included: string[];
  what_to_bring: string[];
  itinerary: Day[];
  media?: Media[];
  status?: string;
  moderation_note?: string;
};
type Departure = { id: number; date: string; seats_total: number; seats_booked: number; seats_left: number; price_uzs: number | null; status: string };

const EMPTY: Tour = {
  title: "", short_description: "", description: "", destination: "", categories: [], duration_days: 1, duration_nights: 0,
  max_group_size: 20, departure_time: "07:00", return_time: null, meeting_point: "", meeting_latitude: null, meeting_longitude: null, meeting_map_url: "", price_uzs: "",
  price_note: "", cancellation_policy: "free", included: [], not_included: [], what_to_bring: [], itinerary: [],
};
const t5 = (v: string | null) => (v ? v.slice(0, 5) : "");

export function TourEditor({ slug }: { slug: string | null }) {
  const router = useRouter();
  const isNew = !slug;
  const tourQ = useData<Tour>(isNew ? null : `/cabinet/tours/${slug}`);
  const cats = useData<Category[]>("/tours/categories");
  const dests = useData<Paginated<Destination>>("/catalog/destinations?page_size=100");
  const [t, setT] = useState<Tour>(EMPTY);
  const save = useAction();
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (tourQ.data) setT({ ...EMPTY, ...tourQ.data });
  }, [tourQ.data]);
  useEffect(() => {
    if (isNew && dests.data?.results[0] && !t.destination) setT((x) => ({ ...x, destination: dests.data!.results[0].slug }));
  }, [isNew, dests.data, t.destination]);

  if (!isNew && !tourQ.data) return tourQ.error ? <ErrorText text={tourQ.error} /> : <Loading />;

  const set = <K extends keyof Tour>(k: K, v: Tour[K]) => setT((x) => ({ ...x, [k]: v }));
  const setDay = (i: number, d: Partial<Day>) => set("itinerary", t.itinerary.map((x, j) => (j === i ? { ...x, ...d } : x)));
  const setItem = (di: number, ii: number, it: Partial<Item>) =>
    setDay(di, { items: t.itinerary[di].items.map((x, j) => (j === ii ? { ...x, ...it } : x)) });

  async function submitForm(e: React.FormEvent) {
    e.preventDefault();
    setSaved(false);
    const body = {
      ...t,
      price_uzs: Number(t.price_uzs) || 0,
      departure_time: t.departure_time || null,
      return_time: t.return_time || null,
      itinerary: t.itinerary.map((d) => ({
        ...d,
        items: d.items.filter((i) => i.title.trim()).map((i) => ({ ...i, start_time: i.start_time || null, end_time: i.end_time || null })),
      })),
    };
    delete (body as Partial<Tour>).media;
    delete (body as Partial<Tour>).status;
    delete (body as Partial<Tour>).moderation_note;
    await save.run(async () => {
      const res = isNew ? await api.post<Tour>("/cabinet/tours", body) : await api.patch<Tour>(`/cabinet/tours/${slug}`, body);
      setSaved(true);
      if (isNew) router.replace(`/cabinet/agency/tours/${res.slug}`);
      else tourQ.reload();
    });
  }

  return (
    <div className="space-y-6">
      {!isNew && t.status && (
        <TourStatusBar slug={slug!} status={t.status} note={t.moderation_note} hasMedia={!!t.media?.length} onChange={tourQ.reload} />
      )}
      <form onSubmit={submitForm} className="space-y-6">
        <Panel title={isNew ? "Yangi tur" : "Asosiy ma'lumotlar"}>
          <div className="grid gap-4 sm:grid-cols-2">
            <label className="sm:col-span-2"><span className="label">Nomi *</span><input className="input" required value={t.title} onChange={(e) => set("title", e.target.value)} /></label>
            <label className="sm:col-span-2"><span className="label">Qisqa tavsif</span><input className="input" maxLength={300} value={t.short_description} onChange={(e) => set("short_description", e.target.value)} /></label>
            <label className="sm:col-span-2"><span className="label">Batafsil</span><textarea className="input min-h-32" value={t.description} onChange={(e) => set("description", e.target.value)} /></label>
            <label><span className="label">Yo&apos;nalish *</span>
              <select className="input" value={t.destination} onChange={(e) => set("destination", e.target.value)}>
                {dests.data?.results.map((d) => <option key={d.slug} value={d.slug}>{d.name}</option>)}
              </select>
            </label>
            <div><span className="label">Toifalar *</span>
              <div className="flex flex-wrap gap-2">
                {cats.data?.map((c) => {
                  const on = t.categories.includes(c.slug);
                  return (
                    <button type="button" key={c.slug} onClick={() => set("categories", on ? t.categories.filter((x) => x !== c.slug) : [...t.categories, c.slug])}
                      className={`chip border ${on ? "border-forest-700 bg-forest-700 text-white" : "border-sand-200 bg-white"}`}>{c.icon} {c.name}</button>
                  );
                })}
              </div>
            </div>
            <label><span className="label">Kunlar</span><input className="input" type="number" min={1} max={60} value={t.duration_days} onChange={(e) => set("duration_days", Number(e.target.value))} /></label>
            <label><span className="label">Kechalar</span><input className="input" type="number" min={0} value={t.duration_nights} onChange={(e) => set("duration_nights", Number(e.target.value))} /></label>
            <label><span className="label">Narx (1 kishi, so&apos;m) *</span><input className="input" required inputMode="numeric" value={t.price_uzs} onChange={(e) => set("price_uzs", e.target.value.replace(/\D/g, ""))} /></label>
            <label><span className="label">Narx izohi</span><input className="input" placeholder="2 kishilik xonada 1 kishi uchun" value={t.price_note} onChange={(e) => set("price_note", e.target.value)} /></label>
            <label><span className="label">Maks. guruh</span><input className="input" type="number" min={1} value={t.max_group_size} onChange={(e) => set("max_group_size", Number(e.target.value))} /></label>
            <label><span className="label">Bekor qilish siyosati</span>
              <select className="input" value={t.cancellation_policy} onChange={(e) => set("cancellation_policy", e.target.value)}>
                <option value="free">Bepul (24 soatgacha)</option><option value="partial">Qisman (48 soatdan oldin 50%)</option><option value="non_refundable">Qaytarilmaydi</option>
              </select>
            </label>
            <label><span className="label">Jo&apos;nash vaqti</span><input className="input" type="time" value={t5(t.departure_time)} onChange={(e) => set("departure_time", e.target.value)} /></label>
            <label><span className="label">Qaytish vaqti</span><input className="input" type="time" value={t5(t.return_time)} onChange={(e) => set("return_time", e.target.value)} /></label>
            <div className="space-y-3 rounded-xl border border-sky-100 bg-sky-50 p-4 sm:col-span-2">
              <p className="text-sm font-semibold text-sky-700">📍 Uchrashuv joyi — turistlar faqat shu joyda yig&apos;iladi</p>
              <div className="grid gap-3 sm:grid-cols-2">
                <label>
                  <span className="label">Joy nomi / manzil <span className="text-clay-500">*</span></span>
                  <input className="input" required placeholder="Toshkent, Amir Temur xiyoboni" value={t.meeting_point} onChange={(e) => set("meeting_point", e.target.value)} />
                </label>
                <label>
                  <span className="label">Xaritadagi joyi <span className="text-clay-500">*</span></span>
                  <input
                    className="input"
                    placeholder="41.311151, 69.279737 — yoki xarita havolasi"
                    defaultValue={t.meeting_map_url || (t.meeting_latitude ? `${t.meeting_latitude}, ${t.meeting_longitude}` : "")}
                    onChange={(e) => {
                      const v = e.target.value.trim();
                      const c = parseCoords(v);
                      setT((x) => ({
                        ...x,
                        meeting_latitude: c?.latitude ?? null,
                        meeting_longitude: c?.longitude ?? null,
                        meeting_map_url: /^https?:\/\//.test(v) ? v : "",
                      }));
                    }}
                  />
                </label>
              </div>
              <p className="text-xs text-ink-mute">
                {t.meeting_latitude ? (
                  <>
                    ✓ Koordinata: {t.meeting_latitude}, {t.meeting_longitude} ·{" "}
                    <a className="text-sky-700 hover:underline" target="_blank" rel="noopener noreferrer" href={`https://yandex.uz/maps/?pt=${t.meeting_longitude},${t.meeting_latitude}&z=16&l=map`}>tekshirish ↗</a>
                  </>
                ) : t.meeting_map_url ? (
                  "✓ Xarita havolasi saqlanadi"
                ) : (
                  "Xaritada joyni bosing va koordinatani nusxalang yoki havolani qo'ying. E'longa yuborish uchun majburiy."
                )}
              </p>
            </div>
          </div>
        </Panel>

        <Panel title="Narxga kiradi / kirmaydi">
          <div className="grid gap-4 md:grid-cols-3">
            <label><span className="label">Kiradi</span><LinesInput value={t.included} onChange={(v) => set("included", v)} /></label>
            <label><span className="label">Kirmaydi</span><LinesInput value={t.not_included} onChange={(v) => set("not_included", v)} /></label>
            <label><span className="label">O&apos;zingiz bilan oling</span><LinesInput value={t.what_to_bring} onChange={(v) => set("what_to_bring", v)} /></label>
          </div>
        </Panel>

        <Panel
          title="Kunlik dastur"
          action={
            <button type="button" className="btn-ghost px-3 py-1.5 text-xs" disabled={t.itinerary.length >= t.duration_days}
              onClick={() => set("itinerary", [...t.itinerary, { day_number: t.itinerary.length + 1, title: "", description: "", items: [] }])}>
              + Kun qo&apos;shish
            </button>
          }
        >
          {!t.itinerary.length && <p className="text-sm text-ink-mute">Dastur hali yo&apos;q.</p>}
          <div className="space-y-5">
            {t.itinerary.map((d, di) => (
              <div key={di} className="rounded-xl border border-sand-200 p-4">
                <div className="mb-3 flex items-center gap-3">
                  <span className="rounded-full bg-forest-700 px-2.5 py-0.5 text-xs font-semibold text-white">{d.day_number}-kun</span>
                  <input className="input" placeholder="Kun sarlavhasi" value={d.title} onChange={(e) => setDay(di, { title: e.target.value })} />
                  <button type="button" className="text-sm text-clay-700" aria-label="Kunni o'chirish"
                    onClick={() => set("itinerary", t.itinerary.filter((_, j) => j !== di).map((x, j) => ({ ...x, day_number: j + 1 })))}>✕</button>
                </div>
                <div className="space-y-2">
                  {d.items.map((it, ii) => (
                    <div key={ii} className="grid grid-cols-[90px_90px_1fr_auto_auto] items-center gap-2">
                      <input className="input px-2" type="time" value={t5(it.start_time)} onChange={(e) => setItem(di, ii, { start_time: e.target.value })} />
                      <input className="input px-2" type="time" value={t5(it.end_time)} onChange={(e) => setItem(di, ii, { end_time: e.target.value })} />
                      <input className="input" placeholder="Nima bo'ladi" value={it.title} onChange={(e) => setItem(di, ii, { title: e.target.value })} />
                      <label className="flex items-center gap-1 text-xs" title="O'z hisobidan"><input type="checkbox" checked={it.is_extra_cost} onChange={(e) => setItem(di, ii, { is_extra_cost: e.target.checked })} /> 💰</label>
                      <button type="button" className="text-clay-700" aria-label="O'chirish" onClick={() => setDay(di, { items: d.items.filter((_, j) => j !== ii) })}>✕</button>
                    </div>
                  ))}
                </div>
                <button type="button" className="mt-2 text-sm font-semibold text-forest-700"
                  onClick={() => setDay(di, { items: [...d.items, { start_time: "", end_time: "", title: "", description: "", is_extra_cost: false }] })}>
                  + Band qo&apos;shish
                </button>
              </div>
            ))}
          </div>
        </Panel>

        <div className="sticky bottom-4 z-10 flex items-center gap-3 rounded-full bg-white/95 p-2 shadow-card backdrop-blur" style={{ bottom: "calc(env(safe-area-inset-bottom, 0px) + 1rem)" }}>
          <button className="btn-primary px-8" disabled={save.busy}>{save.busy ? "Saqlanmoqda…" : isNew ? "Yaratish" : "Saqlash"}</button>
          {saved && <span className="text-sm text-forest-700">Saqlandi ✓</span>}
          <div className="flex-1"><ErrorText text={save.error} /></div>
        </div>
      </form>

      {!isNew && (
        <>
          <MediaManager slug={slug!} media={t.media ?? []} onChange={tourQ.reload} />
          <DeparturesManager slug={slug!} />
        </>
      )}
    </div>
  );
}

function TourStatusBar({ slug, status, note, hasMedia, onChange }: { slug: string; status: string; note?: string; hasMedia: boolean; onChange: () => void }) {
  const act = useAction();
  const st = TOUR_STATUS[status];
  const canSubmit = ["draft", "rejected", "archived"].includes(status);
  return (
    <div className="card flex flex-wrap items-center gap-3 p-4">
      <Badge tone={st?.tone ?? "gray"}>{st?.label ?? status}</Badge>
      {status === "pending_review" && <span className="text-sm text-ink-soft">⏳ Admin tekshiruvida — tasdiqlangach saytda chiqadi.</span>}
      {status === "published" && <a href={`/tours/${slug}`} target="_blank" className="text-sm text-forest-700">Saytda ko&apos;rish ↗</a>}
      <div className="ml-auto flex gap-2">
        {canSubmit && (
          <button className="btn-gold" disabled={act.busy || !hasMedia} title={hasMedia ? "" : "Avval kamida 1 rasm yuklang"}
            onClick={() => act.run(async () => { await api.post(`/cabinet/tours/${slug}/submit`); onChange(); })}>
            E&apos;longa yuborish
          </button>
        )}
        {status !== "archived" && (
          <button className="btn-ghost" disabled={act.busy} onClick={() => act.run(async () => { await api.post(`/cabinet/tours/${slug}/archive`); onChange(); })}>Arxivlash</button>
        )}
      </div>
      {!hasMedia && canSubmit && <p className="w-full text-xs text-ink-mute">E&apos;longa yuborish uchun kamida bitta rasm yuklang.</p>}
      {status === "rejected" && (
        <div className="w-full">
          <ModerationBanner state="rejected" note={note} what="Tur" />
        </div>
      )}
      {status === "published" && (
        <div className="w-full">
          <ModerationBanner state="approved" />
        </div>
      )}
      <div className="w-full"><ErrorText text={act.error} /></div>
    </div>
  );
}

function MediaManager({ slug, media, onChange }: { slug: string; media: Media[]; onChange: () => void }) {
  const act = useAction();
  const [localError, setLocalError] = useState("");
  async function upload(files: FileList | null) {
    if (!files?.length) return;
    const list = Array.from(files);
    const err = galleryError(list, media);
    setLocalError(err ?? "");
    if (err) return;
    await act.run(async () => {
      for (const file of list) {
        const fd = new FormData();
        fd.append("file", file);
        fd.append("kind", mediaKind(file) ?? "image");
        if (!media.length) fd.append("is_cover", "true");
        const res = await fetch(`/api/proxy/cabinet/tours/${slug}/media`, { method: "POST", body: fd });
        if (!res.ok) throw new ClientApiError(res.status, await res.json().catch(() => ({ detail: "Yuklashda xato" })));
      }
      onChange();
    });
  }
  return (
    <Panel
      title="Rasm va video"
      action={
        <label className="btn-ghost cursor-pointer px-3 py-1.5 text-xs">
          {act.busy ? "Yuklanmoqda…" : "+ Yuklash"}
          <input type="file" multiple accept={MEDIA_ACCEPT} className="hidden" onChange={(e) => { upload(e.target.files); e.target.value = ""; }} />
        </label>
      }
    >
      <p className="mb-3 text-xs text-ink-mute">
        {MEDIA_HINT} Hozir: {media.filter((m) => m.kind !== "video").length}/{MAX_IMAGES} rasm, {media.filter((m) => m.kind === "video").length}/{MAX_VIDEOS} video.
      </p>
      <ErrorText text={localError || act.error} />
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {media.map((m) => (
          <div key={m.id} className={`relative overflow-hidden rounded-xl ${m.is_cover ? "ring-2 ring-sun-500" : ""}`}>
            {m.kind === "video" ? <video src={m.file} className="aspect-square w-full object-cover" /> : (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={m.file} alt="" className="aspect-square w-full object-cover" />
            )}
            <div className="absolute inset-x-0 bottom-0 flex justify-between bg-forest-900/70 p-1.5 text-xs text-white">
              {m.kind === "image" && !m.is_cover ? (
                <button onClick={() => act.run(async () => { await api.patch(`/cabinet/tours/${slug}/media/${m.id}`, { is_cover: true }); onChange(); })}>Muqova</button>
              ) : <span>{m.is_cover ? "★ Muqova" : "Video"}</span>}
              <button onClick={() => act.run(async () => { await api.del(`/cabinet/tours/${slug}/media/${m.id}`); onChange(); })}>O&apos;chirish</button>
            </div>
          </div>
        ))}
      </div>
    </Panel>
  );
}

function DeparturesManager({ slug }: { slug: string }) {
  const deps = useData<Departure[]>(`/cabinet/tours/${slug}/departures`);
  const act = useAction();
  const [d, setD] = useState({ date: "", seats_total: "20" });
  const [confirmId, setConfirmId] = useState<number | null>(null);
  const tomorrow = new Date(Date.now() + 86400000).toISOString().slice(0, 10);
  return (
    <Panel title="Jo'nash sanalari">
      <form className="mb-4 flex flex-wrap items-end gap-2" onSubmit={(e) => { e.preventDefault(); act.run(async () => { await api.post(`/cabinet/tours/${slug}/departures`, { date: d.date, seats_total: Number(d.seats_total) }); setD({ ...d, date: "" }); deps.reload(); }); }}>
        <label><span className="label">Sana</span><input className="input" type="date" min={tomorrow} required value={d.date} onChange={(e) => setD({ ...d, date: e.target.value })} /></label>
        <label><span className="label">Joylar</span><input className="input w-24" type="number" min={1} required value={d.seats_total} onChange={(e) => setD({ ...d, seats_total: e.target.value })} /></label>
        <button className="btn-primary" disabled={act.busy}>+ Qo&apos;shish</button>
      </form>
      <ErrorText text={act.error} />
      {!deps.data ? <Loading /> : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead><tr className="text-left text-xs uppercase text-ink-mute"><th className="py-2">Sana</th><th>Band / jami</th><th>Holat</th><th /></tr></thead>
            <tbody>
              {deps.data.map((x) => (
                <tr key={x.id} className="border-t border-sand-200">
                  <td className="py-2">{weekday(x.date)}, {dateLong(x.date, true)}</td>
                  <td>{x.seats_booked} / {x.seats_total}</td>
                  <td><Badge tone={x.status === "open" ? "green" : x.status === "cancelled" ? "red" : "gray"}>{x.status === "open" ? "Sotuvda" : x.status === "cancelled" ? "Bekor" : "Yopilgan"}</Badge></td>
                  <td className="space-x-3 text-right">
                    {x.status === "open" && (
                      <button className="text-xs text-ink-soft" onClick={() => act.run(async () => { await api.patch(`/cabinet/tours/${slug}/departures/${x.id}`, { status: "closed" }); deps.reload(); })}>Sotuvni yopish</button>
                    )}
                    {x.status !== "cancelled" && confirmId !== x.id && (
                      <button className="text-xs text-clay-700" onClick={() => setConfirmId(x.id)}>Bekor qilish</button>
                    )}
                    {confirmId === x.id && (
                      <span className="text-xs">
                        {x.seats_booked ? `${x.seats_booked} ta bron bekor bo'ladi (100% qaytariladi). ` : ""}Ishonchingiz komilmi?{" "}
                        <button className="font-semibold text-clay-700" onClick={() => act.run(async () => { await api.patch(`/cabinet/tours/${slug}/departures/${x.id}`, { status: "cancelled" }); setConfirmId(null); deps.reload(); })}>Ha</button>{" "}
                        <button className="text-ink-soft" onClick={() => setConfirmId(null)}>Yo&apos;q</button>
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Panel>
  );
}
