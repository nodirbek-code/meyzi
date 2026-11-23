"use client";

import { useRouter } from "next/navigation";
import { useRef, useState } from "react";

import { firstError } from "@/lib/client";

type RowError = { row: number; errors: string[] };

/** Excel (.xlsx) orqali ommaviy qo'shish — faqat matnli ma'lumotlar; fayllar keyin qo'lda. */
export function ImportExcel({ res, title }: { res: string; title: string }) {
  const router = useRouter();
  const input = useRef<HTMLInputElement>(null);
  const [open, setOpen] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [ok, setOk] = useState("");
  const [error, setError] = useState("");
  const [rows, setRows] = useState<RowError[]>([]);

  async function upload(e: React.FormEvent) {
    e.preventDefault();
    if (!file) return;
    setBusy(true);
    setOk("");
    setError("");
    setRows([]);
    const fd = new FormData();
    fd.append("file", file);
    try {
      const r = await fetch(`/api/proxy/control/manage/${res}/import`, { method: "POST", body: fd });
      const body = await r.json().catch(() => ({}));
      if (!r.ok) {
        setRows(Array.isArray(body.rows) ? body.rows : []);
        setError(body.detail || firstError(body) || "Yuklab bo'lmadi");
        return;
      }
      setOk(body.detail || "Qo'shildi");
      setFile(null);
      if (input.current) input.current.value = "";
      router.refresh();
    } catch {
      setError("Tarmoq xatosi. Qayta urinib ko'ring.");
    } finally {
      setBusy(false);
    }
  }

  if (!open) {
    return (
      <button type="button" className="btn-ghost" onClick={() => setOpen(true)}>
        📥 Excel&apos;dan yuklash
      </button>
    );
  }

  return (
    <div className="card w-full space-y-4 p-5">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="font-semibold">Excel orqali qo&apos;shish: {title}</h3>
          <p className="mt-1 text-sm text-ink-mute">
            Faqat matnli ma&apos;lumotlar. Rasm, logotip, sertifikat va boshqa fayllar keyin har bir yozuvni tahrirlashda qo&apos;lda
            qo&apos;shiladi.
          </p>
        </div>
        <button type="button" className="text-ink-mute hover:text-ink" onClick={() => setOpen(false)} aria-label="Yopish">
          ✕
        </button>
      </div>

      <ol className="list-decimal space-y-1 pl-5 text-sm text-ink-soft">
        <li>
          <a className="font-semibold text-forest-700 underline" href={`/api/proxy/control/manage/${res}/import/template`}>
            Shablonni yuklab oling
          </a>{" "}
          — «Yo&apos;riqnoma» varag&apos;ida har bir ustun qanday to&apos;ldirilishi yozilgan.
        </li>
        <li>Ma&apos;lumotni 2-qatordan boshlab to&apos;ldiring, ustun nomlarini o&apos;zgartirmang (* — majburiy).</li>
        <li>Faylni yuklang. Bitta qatorda xato bo&apos;lsa — hech narsa saqlanmaydi, xatolar qator raqami bilan chiqadi.</li>
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
          {busy ? "Yuklanmoqda…" : "Yuklash"}
        </button>
      </form>

      {ok && <p className="rounded-xl bg-forest-50 px-4 py-3 text-sm text-forest-700">✓ {ok}</p>}
      {error && (
        <div className="space-y-2 rounded-xl bg-red-50 px-4 py-3 text-sm text-red-700">
          <p className="font-semibold">{error}</p>
          {rows.length > 0 && (
            <ul className="max-h-72 space-y-1 overflow-y-auto">
              {rows.map((r) => (
                <li key={r.row}>
                  <span className="font-semibold">{r.row}-qator:</span> {r.errors.join(" · ")}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
