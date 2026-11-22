import Link from "next/link";

import type { Dashboard } from "@/lib/control";
import { controlGet, requireStaff } from "@/lib/control-server";
import { money } from "@/lib/format";

const fmtDay = (d: string) => d.slice(8, 10);
const fmtAt = (iso: string) => new Date(iso).toLocaleString("uz-UZ", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" });

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="space-y-3">
      <h2 className="text-sm font-semibold uppercase tracking-wide text-ink-mute">{title}</h2>
      {children}
    </section>
  );
}

export default async function ControlDashboard() {
  await requireStaff();
  const d = await controlGet<Dashboard>("/dashboard/");
  const m = d.money;

  return (
    <div className="space-y-8">
      {/* 1. Tekshiruv navbati */}
      <Section title="✅ Tekshiruv navbati">
        {d.queue_total ? (
          <p className="rounded-xl bg-sun-50 px-4 py-3 text-sm">
            {d.role === "admin" ? (
              <>
                <b>{d.queue_total} ta</b> narsa yakuniy tasdig&apos;ingizni kutyapti. Kartani bosing → ko&apos;rib chiqing →{" "}
                <b>Tasdiqlash</b> yoki <b>Qaytarish</b> (izoh bilan).
              </>
            ) : (
              <>
                <b>{d.queue_total} ta</b> ariza tekshiruvingizni kutyapti. Ma&apos;lumotlarni tekshiring → <b>Tekshirildi</b>{" "}
                (adminga yuboriladi) yoki kamchilik bo&apos;lsa <b>Hamkorga qaytarish</b>.
              </>
            )}
          </p>
        ) : (
          <p className="rounded-xl bg-forest-50 px-4 py-3 text-sm text-forest-700">Hammasi ko&apos;rib chiqilgan — kutayotgan narsa yo&apos;q. 🎉</p>
        )}
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          {d.queue.map((q) => (
            <Link
              key={q.kind}
              href={`/control/queue/${q.kind}?state=${q.state}`}
              className={`card block p-4 transition hover:-translate-y-0.5 hover:shadow-lift ${q.count ? (q.overdue ? "border-l-4 border-l-clay-500" : "border-l-4 border-l-sun-500") : "opacity-70"}`}
            >
              <div className="text-3xl font-bold">{q.count}</div>
              <div className="mt-1 text-sm">{q.icon} {q.title}</div>
              {q.count > 0 && (
                <div className={`mt-1 text-xs ${q.overdue ? "font-semibold text-clay-700" : "text-ink-mute"}`}>
                  Eng eskisi: {q.oldest}
                  {q.overdue && " — kechikyapti"}
                </div>
              )}
              {q.with_moderator > 0 && <div className="mt-1 text-xs text-sky-700">Moderatorda: {q.with_moderator} ta</div>}
            </Link>
          ))}
        </div>
      </Section>

      {/* 2. Pul — faqat asosiy admin */}
      {m && (
      <Section title="💰 To'lovlar va komissiya">
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          {[
            ["Bugungi komissiya", m.today],
            ["7 kunlik komissiya", m.week],
            ["30 kunlik komissiya", m.month],
          ].map(([label, v]) => {
            const x = v as NonNullable<Dashboard["money"]>["today"];
            return (
              <div key={label as string} className="card p-4">
                <div className="text-2xl font-bold">{money(x.commission)}</div>
                <div className="mt-1 text-sm">{label as string}</div>
                <div className="mt-1 text-xs text-ink-mute">{x.count} ta to&apos;langan bron · aylanma {money(x.total)}</div>
              </div>
            );
          })}
          <div className="card p-4">
            <div className="text-2xl font-bold">{m.new_today}</div>
            <div className="mt-1 text-sm">Bugun yangi bronlar</div>
            <div className="mt-1 text-xs text-ink-mute">To&apos;lov kutilmoqda: {m.pending_payment} · bugun bekor: {m.cancelled_today}</div>
          </div>
        </div>
        <div className="card p-4">
          <p className="mb-3 text-xs text-ink-mute">Oxirgi 14 kun — kunlik komissiya</p>
          <div className="flex h-32 items-end gap-1.5">
            {m.chart.map((c) => (
              <div key={c.day} className="flex h-full flex-1 flex-col items-center justify-end" title={`${c.day}: ${money(c.value)}`}>
                <div className="w-full rounded-t bg-forest-500" style={{ height: `${Math.max(c.pct, 2)}%` }} />
                <span className="mt-1 text-[10px] text-ink-mute">{fmtDay(c.day)}</span>
              </div>
            ))}
          </div>
          <p className="mt-3 text-xs text-ink-soft">
            30 kun:{" "}
            {m.by_kind.map((k, i) => (
              <span key={k.label}>
                {k.label} — <b>{k.count}</b> bron, {money(k.commission)}
                {i < m.by_kind.length - 1 && " · "}
              </span>
            ))}
          </p>
        </div>
      </Section>
      )}

      <div className="grid gap-8 xl:grid-cols-[1fr_1fr]">
        {/* 3. Ogohlantirishlar va platforma */}
        {d.role === "admin" && (
        <div className="space-y-8">
          <Section title="⚠️ E'tibor talab qiladi">
            {d.alerts.length ? (
              <ul className="space-y-2">
                {d.alerts.map((a) => (
                  <li key={a.text} className="rounded-xl border-l-4 border-l-clay-500 bg-white px-4 py-2.5 text-sm shadow-card">{a.text}</li>
                ))}
              </ul>
            ) : (
              <p className="rounded-xl bg-forest-50 px-4 py-3 text-sm text-forest-700">Ogohlantirish yo&apos;q.</p>
            )}
          </Section>
          <Section title="📊 Platforma">
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
              {d.platform.map((p) => (
                <div key={p.label} className="card p-4">
                  <div className="text-2xl font-bold">{p.value.toLocaleString("ru-RU")}</div>
                  <div className="mt-1 text-xs text-ink-soft">{p.label}</div>
                </div>
              ))}
            </div>
          </Section>
        </div>
        )}

        {/* 4. Oxirgi amallar */}
        <Section title={d.role === "admin" ? "🕘 Oxirgi admin amallari" : "🕘 Mening oxirgi amallarim"}>
          {d.recent_actions.length ? (
            <ul className="card divide-y divide-sand-200">
              {d.recent_actions.map((a, i) => (
                <li key={i} className="px-4 py-3 text-sm">
                  <b>{a.user}</b> — {a.object}
                  <div className="mt-0.5 text-xs text-ink-mute">
                    {a.message} · {fmtAt(a.at)}
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-ink-mute">Hali amal yo&apos;q.</p>
          )}
        </Section>
      </div>
    </div>
  );
}
