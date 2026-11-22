import Link from "next/link";

import { ItemActions } from "@/components/control/ItemActions";
import { ItemData } from "@/components/control/ItemData";
import { Badge } from "@/components/ui";
import { REVIEW_KINDS, REVIEW_STATE_LABEL, STATE_LABEL, STATE_TONE, TWO_STAGE_LABEL, type ControlKind, type Item } from "@/lib/control";
import { controlGet, requireStaff } from "@/lib/control-server";

const fmtAt = (iso: string) => new Date(iso).toLocaleString("uz-UZ", { day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit" });

export default async function ControlItem({ params }: { params: Promise<{ kind: ControlKind; id: string }> }) {
  await requireStaff();
  const { kind, id } = await params;
  const item = await controlGet<Item>(`/items/${kind}/${id}/`);
  const labels = REVIEW_KINDS.includes(kind) ? REVIEW_STATE_LABEL : item.two_stage ? TWO_STAGE_LABEL : STATE_LABEL;
  const note = (item.data.moderation_note as string) || "";

  return (
    <div className="space-y-5">
      <Link href={`/control/queue/${kind}`} className="text-sm text-ink-mute hover:text-forest-700">‹ {item.title}</Link>
      <div className="flex flex-wrap items-center gap-3">
        <h2 className="text-2xl">{item.name}</h2>
        <Badge tone={STATE_TONE[item.state] ?? "gray"}>{labels[item.state] ?? item.state}</Badge>
        {item.public_url && item.state === "approved" && (
          <a href={item.public_url} target="_blank" className="text-sm text-forest-700">Saytda ko&apos;rish ↗</a>
        )}
      </div>
      {item.precheck && (
        <div className="rounded-xl border border-sky-100 bg-sky-50 px-4 py-3 text-sm text-sky-700">
          🟢 <b>Moderator tekshirdi:</b> {item.precheck.by} · {fmtAt(item.precheck.at)}
          {item.precheck.note && <p className="mt-1 whitespace-pre-line text-ink">«{item.precheck.note}»</p>}
        </div>
      )}
      {item.two_stage && item.state === "precheck" && item.role === "admin" && (
        <p className="rounded-xl bg-sand-100 px-4 py-3 text-sm text-ink-soft">
          ⏳ Moderator hali tekshirmagan. Kutishingiz yoki o&apos;zingiz darhol qaror qilishingiz mumkin.
        </p>
      )}
      {note && item.state === "rejected" && (
        <p className="rounded-xl bg-clay-50 px-4 py-3 text-sm text-clay-700">
          <b>Oxirgi qaytarish izohi:</b> {note}
        </p>
      )}

      <div className="grid gap-5 xl:grid-cols-[1fr_320px]">
        <ItemData data={item.data} />
        <div className="space-y-5">
          <ItemActions kind={kind} id={item.id} actions={item.actions} role={item.role} state={item.state} />
          <section className="card p-5">
            <h3 className="mb-3 text-base font-semibold">Tarix</h3>
            {item.history.length ? (
              <ul className="space-y-2 text-sm">
                {item.history.map((h, i) => (
                  <li key={i}>
                    {h.message}
                    <div className="text-xs text-ink-mute">{h.user} · {fmtAt(h.at)}</div>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-ink-mute">Hali qaror qilinmagan.</p>
            )}
          </section>
        </div>
      </div>
    </div>
  );
}
