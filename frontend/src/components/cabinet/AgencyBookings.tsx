"use client";

import { useState } from "react";

import { Badge } from "@/components/ui";
import { api } from "@/lib/client";
import { BOOKING_STATUS, dateTime, money } from "@/lib/format";
import type { Paginated } from "@/lib/types";

import { ErrorText, Loading } from "./Bits";
import { useAction, useData } from "./useData";

type Row = {
  code: string; status: string; tour: { title: string }; departure_at: string; seats: number; total_uzs: number;
  agency_amount_uzs: number; contact_name: string; contact_phone: string; user_email: string | null;
  travelers: { full_name: string }[]; note: string; refund_uzs: number;
};

export function AgencyBookings() {
  const [status, setStatus] = useState("");
  const [search, setSearch] = useState("");
  const q = new URLSearchParams({ page_size: "100", ...(status && { status }), ...(search && { search }) });
  const { data, error, loading, reload } = useData<Paginated<Row>>(`/cabinet/bookings?${q}`);
  const act = useAction();
  const [confirm, setConfirm] = useState<string | null>(null);

  return (
    <div className="space-y-4">
      <div className="card flex flex-wrap gap-3 p-4">
        <select className="input w-auto" value={status} onChange={(e) => setStatus(e.target.value)}>
          <option value="">Barcha holatlar</option>
          {Object.entries(BOOKING_STATUS).map(([k, v]) => <option key={k} value={k}>{v.label}</option>)}
        </select>
        <input className="input max-w-xs" placeholder="Kod, ism yoki telefon" value={search} onChange={(e) => setSearch(e.target.value)} />
      </div>
      <ErrorText text={error || act.error} />
      {loading && <Loading />}
      {data && !data.results.length && <p className="card p-8 text-center text-sm text-ink-soft">Bronlar yo&apos;q.</p>}
      {data?.results.map((b) => {
        const st = BOOKING_STATUS[b.status];
        return (
          <div key={b.code} className="card space-y-2 p-4">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div>
                <span className="font-mono text-xs text-ink-mute">{b.code}</span>
                <div className="font-semibold">{b.tour.title}</div>
                <div className="text-sm text-ink-soft">{dateTime(b.departure_at)} · {b.seats} kishi</div>
              </div>
              <div className="text-right">
                <Badge tone={st?.tone ?? "gray"}>{st?.label ?? b.status}</Badge>
                <div className="mt-1 text-sm">Jami {money(b.total_uzs)} · <b className="text-forest-700">sizga {money(b.agency_amount_uzs)}</b></div>
              </div>
            </div>
            <div className="text-sm">👤 {b.contact_name}, <a className="text-forest-700" href={`tel:${b.contact_phone}`}>{b.contact_phone}</a>{b.user_email && ` · ${b.user_email}`}</div>
            {b.travelers.length > 0 && <div className="text-xs text-ink-soft">Sayohatchilar: {b.travelers.map((t) => t.full_name).join(", ")}</div>}
            {b.note && <div className="text-xs text-ink-soft">Izoh: {b.note}</div>}
            {(b.status === "confirmed" || b.status === "pending_payment") && (
              confirm === b.code ? (
                <div className="text-sm">
                  Bekor qilsangiz turistga 100% qaytariladi. Ishonchingiz komilmi?{" "}
                  <button className="font-semibold text-clay-700" disabled={act.busy} onClick={() => act.run(async () => { await api.post(`/cabinet/bookings/${b.code}/cancel`, { reason: "Agentlik bekor qildi" }); setConfirm(null); reload(); })}>Ha</button>{" "}
                  <button onClick={() => setConfirm(null)}>Yo&apos;q</button>
                </div>
              ) : <button className="text-sm text-clay-700" onClick={() => setConfirm(b.code)}>Bekor qilish</button>
            )}
          </div>
        );
      })}
    </div>
  );
}
