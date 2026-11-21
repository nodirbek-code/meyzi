"use client";

import { useState } from "react";

import { phoneReady, VerifiedPhoneField, type VerifiedPhone } from "@/components/PhoneField";
import { api } from "@/lib/client";

import { ErrorText, Loading, Panel, Stat } from "./Bits";
import { useAction, useData } from "./useData";

type Stats = {
  tours_total: number;
  tours_by_status: Record<string, number>;
  upcoming_departures: number;
  upcoming_seats_total: number;
  upcoming_seats_booked: number;
  sold_out_departures: number;
};
type Agency = { name: string; description: string; phone: string; email: string; telegram: string; website: string; address: string; inn: string; license_number: string; status: string; is_verified: boolean; commission_percent: string; rating: string; reviews_count: number };

const EDITABLE = ["name", "description", "email", "telegram", "website", "address", "inn", "license_number"] as const;
const LABELS: Record<string, string> = { name: "Nomi", description: "Tavsif", phone: "Telefon", email: "Email", telegram: "Telegram", website: "Sayt", address: "Manzil", inn: "STIR", license_number: "Litsenziya" };

export function AgencyHome() {
  const stats = useData<Stats>("/cabinet/stats");
  const agency = useData<Agency>("/cabinet/agency");
  const [form, setForm] = useState<Partial<Agency> | null>(null);
  const save = useAction();
  const [saved, setSaved] = useState(false);
  const [phone, setPhone] = useState<VerifiedPhone | null>(null);
  const a = agency.data;
  const f = form ?? a ?? {};
  const ph = phone ?? { phone: a?.phone ?? "", token: "" };
  // telefon bo'sh qoldirilishi mumkin; o'zgarsa — Telegram kodi bilan tasdiqlanadi
  const phoneOk = !ph.phone || phoneReady(ph, a?.phone || null);

  return (
    <div className="space-y-6">
      {stats.data ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Stat label="E'lon qilingan turlar" value={stats.data.tours_by_status.published ?? 0} />
          <Stat label="Moderatsiyada" value={stats.data.tours_by_status.pending_review ?? 0} />
          <Stat label="Kelgusi sanalar" value={stats.data.upcoming_departures} />
          <Stat label="Band joylar" value={`${stats.data.upcoming_seats_booked} / ${stats.data.upcoming_seats_total}`} />
        </div>
      ) : <Loading />}
      <Panel title="Agentlik profili" action={a && <span className="text-xs text-ink-mute">Komissiya: {a.commission_percent}% · {a.is_verified ? "✔ tekshirilgan" : "tekshirilmagan"}</span>}>
        {!a ? <Loading /> : (
          <form
            className="grid gap-4 sm:grid-cols-2"
            onSubmit={async (e) => {
              e.preventDefault();
              setSaved(false);
              const body = {
                ...Object.fromEntries(EDITABLE.map((k) => [k, (f as Agency)[k] ?? ""])),
                phone: ph.phone,
                phone_token: ph.token,
              };
              if (await save.run(() => api.patch("/cabinet/agency", body))) {
                setSaved(true);
                agency.reload();
                setForm(null);
                setPhone(null);
              }
            }}
          >
            {EDITABLE.map((k) => (
              <label key={k} className={k === "description" ? "sm:col-span-2" : ""}>
                <span className="label">{LABELS[k]}</span>
                {k === "description" ? (
                  <textarea className="input min-h-24" value={(f as Agency)[k] ?? ""} onChange={(e) => setForm({ ...f, [k]: e.target.value })} />
                ) : (
                  <input className="input" value={(f as Agency)[k] ?? ""} onChange={(e) => setForm({ ...f, [k]: e.target.value })} />
                )}
              </label>
            ))}
            <div className="sm:col-span-2">
              <VerifiedPhoneField value={ph} onChange={setPhone} trustedPhone={a.phone || null} required={false} />
            </div>
            <div className="sm:col-span-2 flex items-center gap-3">
              <button className="btn-primary" disabled={save.busy || !phoneOk}>Saqlash</button>
              {saved && <span className="text-sm text-forest-700">Saqlandi</span>}
            </div>
            <div className="sm:col-span-2"><ErrorText text={save.error} /></div>
          </form>
        )}
      </Panel>
    </div>
  );
}
