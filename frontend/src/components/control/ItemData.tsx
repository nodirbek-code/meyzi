/* eslint-disable @next/next/no-img-element */
import { FIELD_LABEL, SPECIAL_FIELDS } from "@/lib/control";
import { AMENITIES, LANGUAGE_NAMES, money, SPECIALIZATIONS } from "@/lib/format";

type Data = Record<string, unknown>;
type Media = { id: number; kind?: string; image?: string; file?: string; is_cover?: boolean; caption?: string };

const PRICE = /_uzs$/;
const DICTS: Record<string, Record<string, string>> = { amenities: AMENITIES, languages: LANGUAGE_NAMES, specializations: SPECIALIZATIONS };

function value(key: string, v: unknown): React.ReactNode {
  if (v === null || v === undefined || v === "" || (Array.isArray(v) && !v.length)) return <span className="text-ink-mute">—</span>;
  if (typeof v === "boolean") return v ? "Ha" : "Yo'q";
  if (typeof v === "number" && PRICE.test(key)) return money(v);
  if (Array.isArray(v)) {
    const dict = DICTS[key];
    return (
      <span className="flex flex-wrap gap-1.5">
        {v.map((x, i) => (
          <span key={i} className="chip bg-sand-100 text-ink">
            {typeof x === "string" ? (dict?.[x] ?? x) : JSON.stringify(x)}
          </span>
        ))}
      </span>
    );
  }
  if (typeof v === "string" && /^https?:\/\//.test(v)) return <a href={v} target="_blank" className="text-forest-700 underline">{v}</a>;
  if (typeof v === "string" && /^\d{4}-\d{2}-\d{2}T/.test(v)) return new Date(v).toLocaleString("uz-UZ");
  if (typeof v === "object") return <code className="text-xs">{JSON.stringify(v)}</code>;
  return <span className="whitespace-pre-line">{String(v)}</span>;
}

function Block({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="card p-5">
      <h3 className="mb-3 text-base font-semibold">{title}</h3>
      {children}
    </section>
  );
}

function Gallery({ items }: { items: Media[] }) {
  if (!items.length) return <p className="text-sm text-clay-700">Rasm yoki video yuklanmagan.</p>;
  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
      {items.map((m) => {
        const src = m.image ?? m.file ?? "";
        return (
          <a key={m.id} href={src} target="_blank" className={`relative block overflow-hidden rounded-xl bg-sand-100 ${m.is_cover ? "ring-2 ring-sun-500" : ""}`}>
            {m.kind === "video" ? (
              <video src={src} controls preload="metadata" className="aspect-square w-full object-cover" />
            ) : (
              <img src={src} alt={m.caption ?? ""} className="aspect-square w-full object-cover" />
            )}
            {m.is_cover && <span className="absolute left-1 top-1 rounded bg-sun-500 px-1.5 text-[10px] font-bold text-white">MUQOVA</span>}
          </a>
        );
      })}
    </div>
  );
}

/** Hamkor ma'lumotlari — faqat ko'rish uchun (admin o'zgartirmaydi). */
export function ItemData({ data }: { data: Data }) {
  const photo = (data.photo || data.logo) as string | null;
  const fields = Object.entries(data).filter(([k]) => !SPECIAL_FIELDS.has(k) && k in FIELD_LABEL);
  const media = (data.media as Media[] | undefined) ?? null;
  const rooms = (data.rooms as Data[] | undefined) ?? null;
  const itinerary = (data.itinerary as { day_number: number; title: string; items?: Data[] }[] | undefined) ?? null;
  const departures = (data.departures as Data[] | undefined) ?? null;
  const points = (data.meeting_points as Data[] | undefined) ?? null;
  const members = (data.members as { email: string | null; phone: string | null; role: string }[] | undefined) ?? null;
  const cert = data.certificate_url as string | null | undefined;

  return (
    <div className="space-y-5">
      <Block title="Ma'lumotlar">
        <div className="flex flex-col gap-5 sm:flex-row">
          {photo && <img src={photo} alt="" className="h-28 w-28 shrink-0 rounded-2xl object-cover" />}
          <dl className="grid flex-1 gap-x-6 gap-y-3 sm:grid-cols-2">
            {fields.map(([k, v]) => (
              <div key={k} className={["description", "bio", "text", "message", "short_description"].includes(k) ? "sm:col-span-2" : ""}>
                <dt className="text-xs text-ink-mute">{FIELD_LABEL[k]}</dt>
                <dd className="mt-0.5 text-sm">{value(k, v)}</dd>
              </div>
            ))}
          </dl>
        </div>
      </Block>

      {cert !== undefined && (
        <Block title="Sertifikat">
          {cert ? (
            <a href={`/api/proxy${cert}`} target="_blank" className="btn-ghost">📄 Sertifikatni ochish</a>
          ) : (
            <p className="text-sm text-clay-700">Sertifikat yuklanmagan.</p>
          )}
        </Block>
      )}

      {media && (
        <Block title={`Rasm va video (${media.filter((m) => m.kind !== "video").length} rasm, ${media.filter((m) => m.kind === "video").length} video)`}>
          <Gallery items={media} />
        </Block>
      )}

      {rooms && (
        <Block title={`Xona turlari (${rooms.length})`}>
          {rooms.length ? (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="text-left text-xs text-ink-mute">
                  <tr><th className="py-1.5 pr-3">Nomi</th><th className="pr-3">Sig&apos;im</th><th className="pr-3">Karavot</th><th className="pr-3">1 kecha</th><th className="pr-3">Soni</th><th>Sotuvda</th></tr>
                </thead>
                <tbody className="divide-y divide-sand-200">
                  {rooms.map((r) => (
                    <tr key={r.id as number}>
                      <td className="py-2 pr-3 font-semibold">{r.name as string}</td>
                      <td className="pr-3">{r.capacity as number} kishi</td>
                      <td className="pr-3">{(r.beds as string) || "—"}</td>
                      <td className="pr-3">{money(r.price_per_night_uzs as number)}</td>
                      <td className="pr-3">{r.total_rooms as number}</td>
                      <td>{r.is_active ? "Ha" : "Yo'q"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="text-sm text-clay-700">Xona turlari qo&apos;shilmagan.</p>
          )}
        </Block>
      )}

      {itinerary && (
        <Block title="Kunlik dastur">
          {itinerary.length ? (
            <ol className="space-y-3">
              {itinerary.map((d) => (
                <li key={d.day_number}>
                  <p className="font-semibold">{d.day_number}-kun{d.title ? `: ${d.title}` : ""}</p>
                  <ul className="ml-5 list-disc text-sm text-ink-soft">
                    {(d.items ?? []).map((it, i) => (
                      <li key={i}>{[it.time, it.title, it.description].filter(Boolean).join(" — ")}</li>
                    ))}
                  </ul>
                </li>
              ))}
            </ol>
          ) : (
            <p className="text-sm text-clay-700">Dastur yozilmagan.</p>
          )}
        </Block>
      )}

      {departures && (
        <Block title={`Jo'nash sanalari (${departures.length})`}>
          <div className="flex flex-wrap gap-2">
            {departures.map((d) => (
              <span key={d.id as number} className="chip bg-sand-100 text-ink">
                {d.date as string} · {d.seats_total as number} joy
              </span>
            ))}
            {!departures.length && <span className="text-sm text-ink-mute">Sana qo&apos;shilmagan.</span>}
          </div>
        </Block>
      )}

      {points && (
        <Block title={`Uchrashuv joylari (${points.length})`}>
          <ul className="space-y-1 text-sm">
            {points.map((p) => (
              <li key={p.id as number}>📍 <b>{p.name as string}</b> — {p.address as string}</li>
            ))}
            {!points.length && <li className="text-ink-mute">Qo&apos;shilmagan.</li>}
          </ul>
        </Block>
      )}

      {members && (
        <Block title="Hisob egalari">
          <ul className="space-y-1 text-sm">
            {members.map((m, i) => (
              <li key={i}>{m.email || "—"} · {m.phone || "—"} <span className="text-ink-mute">({m.role})</span></li>
            ))}
          </ul>
        </Block>
      )}
    </div>
  );
}
