"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { api, ClientApiError } from "@/lib/client";
import { REVIEW_KINDS, type ControlKind, type StaffRole } from "@/lib/control";

const DONE: Record<string, string> = {
  approve: "Tasdiqlandi — saytda ko'rinadi, hamkorga xabar ketdi.",
  precheck: "Tekshirildi — yakuniy tasdiq uchun asosiy adminga yuborildi.",
  return: "Qaytarildi — izoh hamkorga yuborildi.",
  suspend: "To'xtatildi.",
  activate: "Faollashtirildi.",
};

/**
 * Qaror tugmalari — backend ruxsat bergan amallar (`actions`) bo'yicha:
 * moderator: 🟢 Tekshirildi → adminga · ↩️ Hamkorga qaytarish; asosiy admin: ✅ Tasdiqlash · ↩️ Qaytarish · ⛔/▶️.
 */
export function ItemActions({ kind, id, actions, role, state }: { kind: ControlKind; id: number; actions: string[]; role: StaffRole; state: string }) {
  const router = useRouter();
  const isReview = REVIEW_KINDS.includes(kind);
  const [note, setNote] = useState("");
  const [adminNote, setAdminNote] = useState("");
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");
  const [done, setDone] = useState("");
  const can = (a: string) => actions.includes(a);

  async function run(action: string, body?: unknown) {
    setBusy(action);
    setError("");
    setDone("");
    try {
      await api.post(`/control/items/${kind}/${id}/${action}`, body);
      setNote("");
      setAdminNote("");
      setDone(isReview ? (action === "approve" ? "E'lon qilindi." : "Yashirildi.") : (DONE[action] ?? "Bajarildi."));
      router.refresh();
    } catch (e) {
      setError(e instanceof ClientApiError ? e.message : "Xatolik yuz berdi");
    } finally {
      setBusy("");
    }
  }

  if (!actions.length) {
    return (
      <div className="card space-y-2 p-5 text-sm">
        <h3 className="text-base font-semibold">Qaror</h3>
        {done && <p className="rounded-xl bg-forest-50 px-3 py-2 text-forest-700">✅ {done}</p>}
        <p className="text-ink-soft">
          {role !== "admin" && state === "pending"
            ? "Siz tekshirgansiz — asosiy admin yakuniy qarorini kutmoqda."
            : "Hozircha siz uchun amal yo'q."}
        </p>
      </div>
    );
  }

  return (
    <div className="card space-y-4 p-5">
      <h3 className="text-base font-semibold">{role === "admin" ? "Qaror" : "Tekshiruv"}</h3>
      {done && <p className="rounded-xl bg-forest-50 px-3 py-2 text-sm text-forest-700">✅ {done}</p>}
      {error && <p className="rounded-xl bg-clay-50 px-3 py-2 text-sm text-clay-700">{error}</p>}

      {can("precheck") && (
        <div className="space-y-2">
          <label className="label" htmlFor="adminNote">Admin uchun izoh (ixtiyoriy)</label>
          <textarea
            id="adminNote"
            className="input min-h-20"
            placeholder="Masalan: hujjatlar to'liq, rasmlar sifatli, narxlar bozorga mos."
            value={adminNote}
            onChange={(e) => setAdminNote(e.target.value)}
          />
          <button className={`${role === "admin" ? "btn-ghost" : "btn-primary"} w-full py-3`} disabled={!!busy} onClick={() => run("precheck", { note: adminNote })}>
            {busy === "precheck" ? "…" : "🟢 Tekshirildi — adminga yuborish"}
          </button>
          {role !== "admin" && <p className="text-xs text-ink-mute">Yakuniy tasdiq — asosiy adminda. Unga xabar boradi.</p>}
        </div>
      )}

      {can("approve") && (
        <button className="btn-primary w-full py-3" disabled={!!busy} onClick={() => run("approve")}>
          {busy === "approve" ? "…" : isReview ? "✅ E'lon qilish" : "✅ Tasdiqlash (saytga chiqadi)"}
        </button>
      )}

      {can("return") && (
        <div className="space-y-2 border-t border-sand-200 pt-4">
          {!isReview && (
            <>
              <label className="label" htmlFor="note">
                {role === "admin" ? "Qaytarish" : "Hamkorga qaytarish"} — qayerda kamchilik bor?
              </label>
              <textarea
                id="note"
                className="input min-h-28"
                placeholder="Masalan: rasmlar xira, xona narxlari ko'rsatilmagan, sertifikat o'qilmaydi…"
                value={note}
                onChange={(e) => setNote(e.target.value)}
              />
              <p className="text-xs text-ink-mute">Bu matn hamkorga email va Telegram orqali yuboriladi, kabinetida ham ko&apos;rinadi.</p>
            </>
          )}
          <button
            className="btn w-full border border-clay-500 py-3 text-clay-700 hover:bg-clay-50"
            disabled={!!busy || (!isReview && note.trim().length < 5)}
            onClick={() => run("return", { note })}
          >
            {busy === "return" ? "…" : isReview ? "🚫 Yashirish" : "↩️ Qaytarish va izohni yuborish"}
          </button>
        </div>
      )}

      {(can("suspend") || can("activate")) && (
        <div className="border-t border-sand-200 pt-4">
          {can("activate") ? (
            <button className="btn-ghost w-full" disabled={!!busy} onClick={() => run("activate")}>▶️ Faollashtirish</button>
          ) : (
            <button className="btn-ghost w-full text-clay-700" disabled={!!busy} onClick={() => run("suspend")}>⛔ To&apos;xtatish</button>
          )}
        </div>
      )}
    </div>
  );
}
