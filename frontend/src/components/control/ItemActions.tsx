"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { api, ClientApiError } from "@/lib/client";
import { REVIEW_KINDS, type ControlKind } from "@/lib/control";

/** Admin qarori: ✅ Tasdiqlash · ↩️ Qaytarish (izoh hamkorga boradi) · ⛔ To'xtatish / ▶️ Faollashtirish. */
export function ItemActions({ kind, id, state, canSuspend }: { kind: ControlKind; id: number; state: string; canSuspend: boolean }) {
  const router = useRouter();
  const isReview = REVIEW_KINDS.includes(kind);
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");
  const [done, setDone] = useState("");

  async function run(action: string, body?: unknown) {
    setBusy(action);
    setError("");
    setDone("");
    try {
      await api.post(`/control/items/${kind}/${id}/${action}`, body);
      setNote("");
      setDone(
        { approve: isReview ? "E'lon qilindi." : "Tasdiqlandi — saytda ko'rinadi, hamkorga xabar ketdi.", return: isReview ? "Yashirildi." : "Qaytarildi — izoh hamkorga yuborildi.", suspend: "To'xtatildi.", activate: "Faollashtirildi." }[action] ?? "Bajarildi.",
      );
      router.refresh();
    } catch (e) {
      setError(e instanceof ClientApiError ? e.message : "Xatolik yuz berdi");
    } finally {
      setBusy("");
    }
  }

  return (
    <div className="card space-y-4 p-5">
      <h3 className="text-base font-semibold">Qaror</h3>
      {done && <p className="rounded-xl bg-forest-50 px-3 py-2 text-sm text-forest-700">✅ {done}</p>}
      {error && <p className="rounded-xl bg-clay-50 px-3 py-2 text-sm text-clay-700">{error}</p>}

      {state !== "approved" && (
        <button className="btn-primary w-full py-3" disabled={!!busy} onClick={() => run("approve")}>
          {busy === "approve" ? "…" : isReview ? "✅ E'lon qilish" : "✅ Tasdiqlash"}
        </button>
      )}

      <div className="space-y-2 border-t border-sand-200 pt-4">
        {!isReview && (
          <>
            <label className="label" htmlFor="note">Qaytarish — qayerda kamchilik bor?</label>
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
        {(!isReview || state !== "rejected") && (
          <button
            className="btn w-full border border-clay-500 py-3 text-clay-700 hover:bg-clay-50"
            disabled={!!busy || (!isReview && note.trim().length < 5)}
            onClick={() => run("return", { note })}
          >
            {busy === "return" ? "…" : isReview ? "🚫 Yashirish" : "↩️ Qaytarish va izohni yuborish"}
          </button>
        )}
      </div>

      {canSuspend && (
        <div className="border-t border-sand-200 pt-4">
          {state === "suspended" ? (
            <button className="btn-ghost w-full" disabled={!!busy} onClick={() => run("activate")}>▶️ Faollashtirish</button>
          ) : (
            <button className="btn-ghost w-full text-clay-700" disabled={!!busy} onClick={() => run("suspend")}>⛔ To&apos;xtatish</button>
          )}
        </div>
      )}
    </div>
  );
}
