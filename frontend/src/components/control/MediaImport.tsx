"use client";

import { useEffect, useRef, useState } from "react";

import { firstError } from "@/lib/client";

export type MediaJob = {
  id: number;
  name: string;
  status: "queued" | "running" | "done" | "failed";
  status_text: string;
  total: number;
  processed: number;
  attached: number;
  failed: number;
  error: string;
  created_at: string;
  finished_at: string | null;
  report?: { path: string; ok: boolean; target: string; message: string }[];
};

const ACTIVE = ["queued", "running"];

/** ZIP yuklash va jarayonni kuzatish: sahifa ochiq turganda har 2 soniyada navbatdagi qism ishlanadi. */
export function MediaImport({ initial }: { initial: MediaJob[] }) {
  const input = useRef<HTMLInputElement>(null);
  const [jobs, setJobs] = useState(initial);
  const [current, setCurrent] = useState<MediaJob | null>(initial.find((j) => ACTIVE.includes(j.status)) ?? null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [onlyErrors, setOnlyErrors] = useState(true);

  const currentId = current?.id ?? null;
  const running = !!current && ACTIVE.includes(current.status);
  useEffect(() => {
    if (!running || currentId === null) return;
    const t = setTimeout(async () => {
      const r = await fetch(`/api/proxy/control/media-import/${currentId}`);
      if (!r.ok) return;
      const job: MediaJob = await r.json();
      setCurrent(job);
      setJobs((list) => list.map((j) => (j.id === job.id ? job : j)));
    }, 2000);
    return () => clearTimeout(t);
  }, [running, currentId, current?.processed]);

  async function upload(e: React.FormEvent) {
    e.preventDefault();
    const file = input.current?.files?.[0];
    if (!file) return;
    setBusy(true);
    setError("");
    const fd = new FormData();
    fd.append("file", file);
    try {
      const r = await fetch("/api/proxy/control/media-import", { method: "POST", body: fd });
      const body = await r.json().catch(() => ({}));
      if (!r.ok) {
        setError(firstError(body) || "Yuklab bo'lmadi");
        return;
      }
      setCurrent(body);
      setJobs((list) => [body, ...list]);
      if (input.current) input.current.value = "";
    } catch {
      setError("Tarmoq xatosi yoki arxiv juda katta.");
    } finally {
      setBusy(false);
    }
  }

  async function open(id: number) {
    const r = await fetch(`/api/proxy/control/media-import/${id}`);
    if (r.ok) setCurrent(await r.json());
  }

  const pct = current && current.total ? Math.round((current.processed / current.total) * 100) : 0;
  const rows = (current?.report ?? []).filter((r) => !onlyErrors || !r.ok);

  return (
    <div className="space-y-5">
      <form onSubmit={upload} className="card flex flex-wrap items-center gap-3 p-5">
        <input ref={input} type="file" accept=".zip,application/zip" className="text-sm" />
        <button className="btn-primary" disabled={busy}>
          {busy ? "Yuklanmoqda…" : "ZIP yuklash"}
        </button>
        {error && <p className="w-full rounded-xl bg-red-50 px-4 py-2 text-sm text-red-700">{error}</p>}
      </form>

      {current && (
        <div className="card space-y-4 p-5">
          <div className="flex flex-wrap items-baseline justify-between gap-2">
            <h3 className="font-semibold">{current.name}</h3>
            <span className="text-sm text-ink-soft">
              {current.status_text} · {current.processed}/{current.total} · ✓ {current.attached} · ✕ {current.failed}
            </span>
          </div>
          <div className="h-2 overflow-hidden rounded-full bg-sand-200">
            <div className="h-full bg-forest-600 transition-all" style={{ width: `${pct}%` }} />
          </div>
          {running && <p className="text-xs text-ink-mute">Sahifani yopsangiz ham ish fonda davom etadi.</p>}
          {current.error && <p className="rounded-xl bg-red-50 px-4 py-2 text-sm text-red-700">{current.error}</p>}
          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" checked={onlyErrors} onChange={(e) => setOnlyErrors(e.target.checked)} />
            Faqat biriktirilmaganlar
          </label>
          {rows.length > 0 ? (
            <ul className="max-h-96 divide-y divide-sand-200 overflow-y-auto text-sm">
              {rows.map((r) => (
                <li key={r.path} className="flex flex-wrap gap-x-3 py-2">
                  <span className={r.ok ? "text-forest-600" : "text-red-600"}>{r.ok ? "✓" : "✕"}</span>
                  <span className="font-mono text-xs">{r.path}</span>
                  <span className="text-ink-soft">
                    {r.target && `${r.target} — `}
                    {r.message}
                  </span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-ink-mute">{onlyErrors ? "Muammoli fayl yo'q." : "Hali natija yo'q."}</p>
          )}
        </div>
      )}

      {jobs.length > 0 && (
        <div className="card p-5">
          <h3 className="mb-3 font-semibold">Oxirgi yuklashlar</h3>
          <ul className="divide-y divide-sand-200 text-sm">
            {jobs.map((j) => (
              <li key={j.id} className="flex flex-wrap items-center justify-between gap-2 py-2">
                <button className="text-left font-medium hover:underline" onClick={() => open(j.id)}>
                  {j.name}
                </button>
                <span className="text-ink-soft">
                  {j.status_text} · ✓ {j.attached} / {j.total}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
