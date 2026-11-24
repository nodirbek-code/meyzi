"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { firstError } from "@/lib/client";

const ROLES = [
  { value: "none", label: "Oddiy foydalanuvchi", help: "Admin paneliga kira olmaydi." },
  { value: "admin", label: "Asosiy admin", help: "/control'ning hamma bo'limlari: boshqarish, moderatsiya, foydalanuvchilar." },
  { value: "hotels", label: "Mehmonxona moderatori", help: "Faqat mehmonxonalar arizalarini tekshiradi." },
  { value: "guides", label: "Gid moderatori", help: "Faqat gidlar arizalarini tekshiradi." },
] as const;

type Props = { id: number; isActive: boolean; isStaff: boolean; staffArea: string; locked: string };

/** Foydalanuvchini admin / moderator qilish va bloklash. */
export function UserActions({ id, isActive, isStaff, staffArea, locked }: Props) {
  const router = useRouter();
  const current = !isStaff ? "none" : staffArea || "admin";
  const [role, setRole] = useState<string>(current);
  const [reason, setReason] = useState("");
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState("");
  const [error, setError] = useState("");

  async function call(path: string, body: object, done: string) {
    setBusy(true);
    setMsg("");
    setError("");
    try {
      const r = await fetch(`/api/proxy/control/users/${id}/${path}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const data = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(firstError(data) || "Bajarib bo'lmadi");
      setMsg(done);
      router.refresh();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  function saveRole() {
    if (role === "admin" && !window.confirm("Bu foydalanuvchi asosiy admin bo'ladi va /control'ning hamma bo'limiga kira oladi. Davom etilsinmi?")) return;
    const label = ROLES.find((r) => r.value === role)?.label ?? "";
    call("staff", { is_staff: role !== "none", staff_area: role === "none" || role === "admin" ? "" : role }, `Saqlandi: ${label}`);
  }

  if (locked) {
    return <p className="card p-5 text-sm text-ink-mute">🔒 {locked}</p>;
  }

  return (
    <div className="grid gap-5 lg:grid-cols-2">
      <section className="card space-y-4 p-5">
        <h3 className="font-semibold">Huquqlar</h3>
        <div className="space-y-2">
          {ROLES.map((r) => (
            <label
              key={r.value}
              className={`flex cursor-pointer gap-3 rounded-xl border px-4 py-3 ${role === r.value ? "border-forest-600 bg-forest-50" : "border-sand-200"}`}
            >
              <input type="radio" name="role" value={r.value} checked={role === r.value} onChange={() => setRole(r.value)} className="mt-1" />
              <span>
                <span className="block font-semibold">{r.label}</span>
                <span className="block text-sm text-ink-mute">{r.help}</span>
              </span>
            </label>
          ))}
        </div>
        <button type="button" className="btn-primary" disabled={busy || role === current} onClick={saveRole}>
          {busy ? "Saqlanmoqda…" : "Saqlash"}
        </button>
      </section>

      <section className="card space-y-4 p-5">
        <h3 className="font-semibold">Bloklash</h3>
        {isActive ? (
          <>
            <p className="text-sm text-ink-mute">Bloklangan foydalanuvchi saytga kira olmaydi, faol sessiyalari darhol tugaydi. Ma&apos;lumotlari saqlanadi.</p>
            <textarea className="input w-full text-sm" rows={2} placeholder="Sabab (ixtiyoriy)" value={reason} onChange={(e) => setReason(e.target.value)} />
            <button
              type="button"
              className="btn-ghost text-red-600"
              disabled={busy}
              onClick={() => window.confirm("Foydalanuvchi bloklansinmi?") && call("block", { reason }, "Bloklandi")}
            >
              🚫 Bloklash
            </button>
          </>
        ) : (
          <>
            <p className="text-sm text-red-700">Bu foydalanuvchi bloklangan.</p>
            <button type="button" className="btn-primary" disabled={busy} onClick={() => call("unblock", {}, "Blokdan chiqarildi")}>
              ✅ Blokdan chiqarish
            </button>
          </>
        )}
      </section>

      {(msg || error) && (
        <p className={`rounded-xl px-4 py-3 text-sm lg:col-span-2 ${error ? "bg-red-50 text-red-700" : "bg-forest-50 text-forest-700"}`}>
          {error || `✓ ${msg}`}
        </p>
      )}
    </div>
  );
}
