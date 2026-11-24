"use client";

import { useRouter } from "next/navigation";
import { useRef, useState } from "react";

import { firstError } from "@/lib/client";

type Result = { row: number; name: string; column: string; url: string; ok: boolean; message: string };

/** Excel orqali rasm havolalari: shablonda nomlar tayyor, admin havolalarni qo'yadi — server yuklab oladi. */
export function PhotoLinks({ res, title }: { res: string; title: string }) {
  const router = useRouter();
  const input = useRef<HTMLInputElement>(null);
  const [open, setOpen] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [ok, setOk] = useState("");
  const [error, setError] = useState("");
  const [results, setResults] = useState<Result[]>([]);

  async function upload(e: React.FormEvent) {
    e.preventDefault();
    if (!file) return;
    setBusy(true);
    setOk("");
    setError("");
    setResults([]);
    const fd = new FormData();
    fd.append("file", file);
    try {
      const r = await fetch(`/api/proxy/control/manage/${res}/photo-links`, { method: "POST", body: fd });
      const body = await r.json().catch(() => ({}));
      if (!r.ok) {
        setError(body.detail || firstError(body) || "Yuklab bo'lmadi");
        return;
      }
      setOk(body.detail || "Saqlandi");
      setResults(Array.isArray(body.results) ? body.results : []);
      setFile(null);
      if (input.current) input.current.value = "";
      router.refresh();
    } catch {
      setError("Tarmoq xatosi yoki javob juda uzoq kutildi. Faylni kichikroq qismlarga bo'lib yuklang.");
    } finally {
      setBusy(false);
    }
  }

  if (!open) {
    return (
      <button type="button" className="btn-ghost" onClick={() => setOpen(true)}>
        🖼 Rasm havolalari (Excel)
      </button>
    );
  }

  const failed = results.filter((x) => !x.ok);

  return (
    <div className="card w-full space-y-4 p-5">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="font-semibold">Rasm havolalari: {title}</h3>
          <p className="mt-1 text-sm text-ink-mute">
            Shablonda barcha yozuvlar nomi tayyor — faqat havolalarni qo&apos;ying. Server rasmlarni o&apos;zi yuklab olib saqlaydi.
          </p>
        </div>
        <button type="button" className="text-ink-mute hover:text-ink" onClick={() => setOpen(false)} aria-label="Yopish">
          ✕
        </button>
      </div>

      <ol className="list-decimal space-y-1 pl-5 text-sm text-ink-soft">
        <li>
          <a className="font-semibold text-forest-700 underline" href={`/api/proxy/control/manage/${res}/photo-links/template`}>
            Shablonni yuklab oling
          </a>{" "}
          — nom va slug ustunlariga tegmang.
        </li>
        <li>
          Havola to&apos;g&apos;ridan-to&apos;g&apos;ri faylga olib borsin (brauzerda ochganda faqat rasm ko&apos;rinsin). Instagram sahifasi yoki
          YouTube havolasi ishlamaydi.
        </li>
        <li>Faylni yuklang. Ishlamagan havolalar sababi bilan chiqadi, qolganlari saqlanadi.</li>
      </ol>

      <form onSubmit={upload} className="flex flex-wrap items-center gap-3">
        <input
          ref={input}
          type="file"
          accept=".xlsx,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
          className="text-sm"
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
        />
        <button className="btn-primary" disabled={!file || busy}>
          {busy ? "Rasmlar yuklab olinmoqda…" : "Yuklash"}
        </button>
      </form>

      {ok && <p className="rounded-xl bg-forest-50 px-4 py-3 text-sm text-forest-700">✓ {ok}</p>}
      {error && <p className="rounded-xl bg-red-50 px-4 py-3 text-sm font-semibold text-red-700">{error}</p>}
      {failed.length > 0 && (
        <ul className="max-h-72 space-y-1 overflow-y-auto rounded-xl bg-red-50 px-4 py-3 text-sm text-red-700">
          {failed.map((x, i) => (
            <li key={i}>
              <span className="font-semibold">
                {x.row}-qator, {x.name} ({x.column}):
              </span>{" "}
              {x.message}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
