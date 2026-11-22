import Link from "next/link";

import { Badge } from "@/components/ui";
import { REVIEW_KINDS, REVIEW_STATE_LABEL, STATE_LABEL, STATE_TONE, TWO_STAGE_LABEL, type ControlKind, type ListResponse } from "@/lib/control";
import { controlGet, requireStaff } from "@/lib/control-server";

export default async function ControlQueue({
  params,
  searchParams,
}: {
  params: Promise<{ kind: ControlKind }>;
  searchParams: Promise<{ state?: string; q?: string }>;
}) {
  await requireStaff();
  const { kind } = await params;
  const { state: asked, q = "" } = await searchParams;
  const data = await controlGet<ListResponse>(`/items/${kind}/`, { state: asked, q });
  const state = data.state;
  const labels = REVIEW_KINDS.includes(kind) ? REVIEW_STATE_LABEL : data.two_stage ? TWO_STAGE_LABEL : STATE_LABEL;

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-xl">{data.title}</h2>
        <form className="flex gap-2">
          <input type="hidden" name="state" value={state} />
          <input className="input w-56" name="q" defaultValue={q} placeholder="Qidirish…" />
          <button className="btn-ghost px-3">Izlash</button>
        </form>
      </div>

      <div className="no-scrollbar flex gap-2 overflow-x-auto">
        {data.states.map((s) => (
          <Link
            key={s}
            href={`/control/queue/${kind}?state=${s}`}
            className={`chip shrink-0 border px-3.5 py-2 text-sm ${s === state ? "border-forest-600 bg-forest-600 text-white" : "border-sand-300 bg-white text-ink-soft"}`}
          >
            {labels[s] ?? s} <span className="ml-1 opacity-70">{data.counts[s] ?? 0}</span>
          </Link>
        ))}
      </div>

      {data.results.length ? (
        <ul className="card divide-y divide-sand-200">
          {data.results.map((r) => (
            <li key={r.id}>
              <Link href={`/control/queue/${kind}/${r.id}`} className="flex flex-wrap items-center gap-3 px-4 py-3 transition hover:bg-sand-50">
                <div className="min-w-0 flex-1">
                  <p className="truncate font-semibold">{r.title}</p>
                  <p className="truncate text-xs text-ink-mute">{r.subtitle}</p>
                </div>
                {r.waiting && (
                  <span className={`text-xs ${r.overdue ? "font-semibold text-clay-700" : "text-ink-mute"}`}>
                    {state === data.default_state ? `kutyapti: ${r.waiting}` : r.waiting}
                  </span>
                )}
                <Badge tone={STATE_TONE[r.status] ?? "gray"}>{labels[r.status] ?? r.status}</Badge>
                <span className="text-sm text-forest-700">Ko&apos;rish ›</span>
              </Link>
            </li>
          ))}
        </ul>
      ) : (
        <p className="card p-8 text-center text-sm text-ink-mute">
          {state === data.default_state ? "Tekshiruv kutayotgan narsa yo'q. 🎉" : "Bo'sh."}
        </p>
      )}
    </div>
  );
}
