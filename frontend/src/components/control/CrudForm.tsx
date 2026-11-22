"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { firstError } from "@/lib/client";
import type { CrudField } from "@/lib/control";

type Values = Record<string, unknown>;

const toStr = (v: unknown) => (v === null || v === undefined ? "" : String(v));

function initial(schema: CrudField[], data: Values | null): Values {
  const out: Values = {};
  for (const f of schema) {
    const v = data?.[f.name];
    if (f.type === "checkbox") out[f.name] = data ? !!v : f.name.startsWith("is_") && ["is_published", "is_active"].includes(f.name);
    else if (f.type === "multiselect") out[f.name] = Array.isArray(v) ? v.map(String) : [];
    else if (f.type === "tags") {
      const list = Array.isArray(v) ? v.map(String) : [];
      out[f.name] = f.options ? list : list.join("\n"); // erkin ro'yxat — har qatorga bittadan
    }
    else if (f.type === "image" || f.type === "file") out[f.name] = null;
    else if (f.type === "time") out[f.name] = toStr(v).slice(0, 5);
    else if (f.type === "datetime") out[f.name] = toStr(v).slice(0, 16);
    else out[f.name] = toStr(v);
  }
  return out;
}

/** Sxema bo'yicha chiziladigan forma (yaratish va tahrirlash). Fayl bo'lsa — multipart. */
export function CrudForm({
  res,
  schema,
  data,
  id,
  canDelete,
}: {
  res: string;
  schema: CrudField[];
  data: Values | null;
  id?: number;
  canDelete?: boolean;
}) {
  const router = useRouter();
  const [v, setV] = useState<Values>(() => initial(schema, data));
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [saved, setSaved] = useState(false);
  const set = (k: string, val: unknown) => setV((p) => ({ ...p, [k]: val }));
  const fields = schema.filter((f) => !(f.extra && id)); // qo'shimcha maydonlar (egasi emaili) — faqat yaratishda

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    setErrors({});
    setSaved(false);
    const fd = new FormData();
    for (const f of fields) {
      const val = v[f.name];
      if (f.type === "checkbox") fd.append(f.name, val ? "true" : "false");
      else if (f.type === "multiselect") (val as string[]).forEach((x) => fd.append(f.name, x));
      else if (f.type === "tags") {
        const list = typeof val === "string" ? val.split("\n").map((x) => x.trim()).filter(Boolean) : (val as string[]);
        fd.append(f.name, JSON.stringify(list));
      }
      else if (f.type === "image" || f.type === "file") {
        if (val) fd.append(f.name, val as File);
      } else if (["number", "date", "time", "datetime"].includes(f.type)) {
        if (val !== "") fd.append(f.name, String(val));
      } else if (f.type === "fk" || f.type === "select") {
        if (val !== "" || id) fd.append(f.name, String(val));
      } else if (!(f.extra && val === "")) fd.append(f.name, String(val ?? ""));
    }
    try {
      const url = `/api/proxy/control/manage/${res}${id ? `/${id}` : ""}`;
      const r = await fetch(url, { method: id ? "PATCH" : "POST", body: fd });
      const body = await r.json().catch(() => ({}));
      if (!r.ok) {
        const fieldErrors: Record<string, string> = {};
        for (const [k, msg] of Object.entries(body as Record<string, unknown>)) {
          fieldErrors[k] = Array.isArray(msg) ? String(msg[0]) : typeof msg === "string" ? msg : firstError(msg);
        }
        setErrors(fieldErrors);
        throw new Error(fieldErrors.detail || firstError(body) || "Saqlab bo'lmadi");
      }
      if (id) {
        setSaved(true);
        router.refresh();
      } else {
        router.push(`/control/manage/${res}/${(body as { id: number }).id}`);
        router.refresh();
      }
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function remove() {
    if (!id || !window.confirm("Rostdan o'chirilsinmi? Bu amalni qaytarib bo'lmaydi.")) return;
    setBusy(true);
    setError("");
    const r = await fetch(`/api/proxy/control/manage/${res}/${id}`, { method: "DELETE" });
    if (r.ok) {
      router.push(`/control/manage/${res}`);
      router.refresh();
    } else {
      setError(firstError(await r.json().catch(() => ({}))) || "O'chirib bo'lmadi");
      setBusy(false);
    }
  }

  return (
    <form onSubmit={submit} className="card space-y-5 p-6">
      <div className="grid gap-5 sm:grid-cols-2">
        {fields.map((f) => {
          const wide = ["textarea", "tags", "multiselect", "image", "file"].includes(f.type);
          const current = data?.[f.name];
          return (
            <div key={f.name} className={wide ? "sm:col-span-2" : ""}>
              {f.type === "checkbox" ? (
                <label className="flex items-center gap-2 pt-6 text-sm font-semibold">
                  <input type="checkbox" className="h-4 w-4" checked={!!v[f.name]} onChange={(e) => set(f.name, e.target.checked)} />
                  {f.label}
                </label>
              ) : (
                <label className="block">
                  <span className="label">
                    {f.label}
                    {f.required && <span className="text-clay-500"> *</span>}
                  </span>
                  {f.type === "textarea" ? (
                    <textarea className="input min-h-28" required={f.required} value={v[f.name] as string} onChange={(e) => set(f.name, e.target.value)} />
                  ) : f.type === "select" || f.type === "fk" ? (
                    <select className="input" required={f.required} value={v[f.name] as string} onChange={(e) => set(f.name, e.target.value)}>
                      <option value="">—</option>
                      {f.options?.map(([val, label]) => (
                        <option key={val} value={val}>{label}</option>
                      ))}
                    </select>
                  ) : f.type === "multiselect" || (f.type === "tags" && f.options) ? (
                    <span className="mt-1 flex max-h-56 flex-wrap gap-2 overflow-y-auto">
                      {f.options?.map(([val, label]) => {
                        const list = v[f.name] as string[];
                        const on = list.includes(val);
                        return (
                          <button
                            type="button"
                            key={val}
                            onClick={() => set(f.name, on ? list.filter((x) => x !== val) : [...list, val])}
                            className={`chip border px-3 py-1.5 ${on ? "border-forest-600 bg-forest-600 text-white" : "border-sand-300 bg-white text-ink-soft"}`}
                          >
                            {on && "✓ "}
                            {label}
                          </button>
                        );
                      })}
                      {!f.options?.length && <span className="text-sm text-ink-mute">Variant yo&apos;q.</span>}
                    </span>
                  ) : f.type === "tags" ? (
                    <textarea
                      className="input min-h-24"
                      placeholder="Har bir qatorga bittadan"
                      value={v[f.name] as string}
                      onChange={(e) => set(f.name, e.target.value)}
                    />
                  ) : f.type === "image" || f.type === "file" ? (
                    <span className="mt-1 flex flex-wrap items-center gap-3">
                      {typeof current === "string" && current && (
                        f.type === "image" ? (
                          // eslint-disable-next-line @next/next/no-img-element
                          <a href={current} target="_blank"><img src={current} alt="" className="h-16 w-16 rounded-xl object-cover" /></a>
                        ) : (
                          <a href={current} target="_blank" className="text-sm text-forest-700 underline">Joriy fayl</a>
                        )
                      )}
                      <input className="input flex-1 py-2" type="file" required={f.required && !current} onChange={(e) => set(f.name, e.target.files?.[0] ?? null)} />
                    </span>
                  ) : (
                    <input
                      className="input"
                      type={{ number: "number", date: "date", time: "time", datetime: "datetime-local", email: "email", url: "url" }[f.type as string] ?? "text"}
                      step={f.type === "number" ? "any" : undefined}
                      required={f.required}
                      value={v[f.name] as string}
                      onChange={(e) => set(f.name, e.target.value)}
                    />
                  )}
                </label>
              )}
              {(errors[f.name] || f.help) && (
                <span className={`mt-1 block text-xs ${errors[f.name] ? "text-clay-700" : "text-ink-mute"}`}>{errors[f.name] || f.help}</span>
              )}
            </div>
          );
        })}
      </div>
      {error && <p className="rounded-xl bg-clay-50 px-3 py-2 text-sm text-clay-700">{error}</p>}
      {saved && <p className="rounded-xl bg-forest-50 px-3 py-2 text-sm text-forest-700">✅ Saqlandi.</p>}
      <div className="flex flex-wrap items-center gap-3">
        <button className="btn-primary px-6" disabled={busy}>{busy ? "Saqlanmoqda…" : id ? "Saqlash" : "Yaratish"}</button>
        {id && canDelete && (
          <button type="button" className="btn-ghost text-clay-700" disabled={busy} onClick={remove}>🗑 O&apos;chirish</button>
        )}
      </div>
    </form>
  );
}
