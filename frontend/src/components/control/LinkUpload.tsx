"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { firstError } from "@/lib/client";

type Result = { url: string; ok: boolean; message: string };

/** Havola orqali rasm/video qo'shish (Google rasm havolasi ham bo'ladi) — server o'zi yuklab oladi. */
export function LinkUpload({ res, id, multiple = true }: { res: string; id: number; multiple?: boolean }) {
  const router = useRouter();
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [ok, setOk] = useState("");
  const [failed, setFailed] = useState<Result[]>([]);
  const [error, setError] = useState("");

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!text.trim()) return;
    setBusy(true);
    setOk("");
    setError("");
    setFailed([]);
    // bitta havola bir necha qatorga bo'linib qolgan bo'lsa ham: yangi havola faqat http bilan boshlanadi
    const urls = text
      .split(/\s+(?=https?:\/\/)/)
      .map((u) => u.replace(/\s+/g, ""))
      .filter(Boolean);
    try {
      const r = await fetch(`/api/proxy/control/manage/${res}/${id}/links`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ urls: multiple ? urls : urls.slice(0, 1) }),
      });
      const body = await r.json().catch(() => ({}));
      if (!r.ok) {
        setError(body.detail || firstError(body) || "Qo'shib bo'lmadi");
        return;
      }
      const results: Result[] = Array.isArray(body.results) ? body.results : [];
      setOk(body.done ? body.detail : "");
      setFailed(results.filter((x) => !x.ok));
      if (body.done) {
        setText(results.filter((x) => !x.ok).map((x) => x.url).join("\n"));
        router.refresh();
      }
    } catch {
      setError("Tarmoq xatosi. Qayta urinib ko'ring.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={submit} className="space-y-2">
      <label className="block text-sm font-semibold">
        Havoladan qo&apos;shish{" "}
        <span className="font-normal text-ink-mute">
          — rasm havolasi yoki Google rasmlar sahifasidagi havola{multiple ? "; bir nechta bo'lsa — har biri yangi qatorda" : ""}
        </span>
      </label>
      <div className="flex flex-col gap-2 sm:flex-row sm:items-start">
        <textarea
          className="input min-h-[2.75rem] flex-1 py-2 text-sm"
          rows={multiple ? 3 : 2}
          placeholder="https://…"
          value={text}
          onChange={(e) => setText(e.target.value)}
        />
        <button className="btn-primary shrink-0" disabled={busy || !text.trim()}>
          {busy ? "Yuklab olinmoqda…" : "Qo'shish"}
        </button>
      </div>
      {ok && <p className="rounded-xl bg-forest-50 px-4 py-2 text-sm text-forest-700">✓ {ok}</p>}
      {error && <p className="rounded-xl bg-red-50 px-4 py-2 text-sm text-red-700">{error}</p>}
      {failed.length > 0 && (
        <ul className="space-y-1 rounded-xl bg-red-50 px-4 py-2 text-sm text-red-700">
          {failed.map((x, i) => (
            <li key={i} className="break-all">
              <span className="font-semibold">{x.message}</span> — {x.url.slice(0, 90)}
              {x.url.length > 90 ? "…" : ""}
            </li>
          ))}
        </ul>
      )}
    </form>
  );
}
