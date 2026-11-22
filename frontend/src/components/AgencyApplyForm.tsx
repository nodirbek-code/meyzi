"use client";

import { useState } from "react";

import { api, ClientApiError } from "@/lib/client";

import { phoneReady, VerifiedPhoneField, type VerifiedPhone } from "./PhoneField";

/** Agentlik arizasi. Telefon — akkauntdagi (Telegram bot orqali tasdiqlangan) raqam. */
export function AgencyApplyForm({ trustedPhone }: { trustedPhone?: string | null }) {
  const [f, setF] = useState({ agency_name: "", contact_person: "", email: "", message: "" });
  const [phone, setPhone] = useState<VerifiedPhone>({ phone: trustedPhone ?? "", token: "" });
  const [done, setDone] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const set = (k: keyof typeof f) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => setF({ ...f, [k]: e.target.value });
  const ready = f.agency_name.trim() && f.contact_person.trim() && phoneReady(phone, trustedPhone);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await api.post("/agencies/applications", { ...f, phone: phone.phone, phone_token: phone.token });
      setDone(true);
    } catch (err) {
      setError(err instanceof ClientApiError ? err.message : "Xatolik");
    } finally {
      setBusy(false);
    }
  }

  if (done) {
    return (
      <div className="card p-10 text-center">
        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-forest-600 text-2xl text-white">✓</div>
        <h3 className="mt-4 text-xl">Arizangiz qabul qilindi</h3>
        <p className="mt-2 text-sm text-ink-soft">Jamoamiz 24 soat ichida siz bilan bog&apos;lanadi.</p>
      </div>
    );
  }
  return (
    <form onSubmit={submit} className="card space-y-4 p-6 sm:p-8">
      <div className="grid gap-4 sm:grid-cols-2">
        <label className="block">
          <span className="label">
            Agentlik nomi <span className="text-clay-500">*</span>
          </span>
          <input className="input" required placeholder="Masalan: Silk Road Travel" value={f.agency_name} onChange={set("agency_name")} />
        </label>
        <label className="block">
          <span className="label">
            Aloqa shaxsi <span className="text-clay-500">*</span>
          </span>
          <input className="input" required placeholder="To'liq ismingiz" value={f.contact_person} onChange={set("contact_person")} />
        </label>
      </div>
      <VerifiedPhoneField value={phone} onChange={setPhone} trustedPhone={trustedPhone} />
      <label className="block">
        <span className="label">Email</span>
        <input className="input" type="email" placeholder="info@agentlik.uz" value={f.email} onChange={set("email")} />
      </label>
      <label className="block">
        <span className="label">Izoh</span>
        <textarea className="input min-h-24" placeholder="Qanday turlar o'tkazasiz, qaysi hududlarda…" value={f.message} onChange={set("message")} />
      </label>
      {error && <p className="rounded-xl bg-clay-50 px-3 py-2 text-sm text-clay-700">{error}</p>}
      <button className="btn-primary w-full py-3.5 text-base" disabled={busy || !ready}>
        {busy ? "Yuborilmoqda…" : "Arizani yuborish"}
      </button>
      <p className="text-center text-xs text-ink-mute">Barcha ma&apos;lumotlar maxfiy saqlanadi.</p>
    </form>
  );
}
