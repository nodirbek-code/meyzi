"use client";

import { useRouter } from "next/navigation";
import { useRef, useState } from "react";

import { firstError } from "@/lib/client";
import type { CrudGallery } from "@/lib/control";

import { LinkUpload } from "./LinkUpload";

/** Tur / mehmonxona tahrirlash sahifasidagi rasm va videolar: bir nechtasini birdan yuklash, muqova, o'chirish. */
export function Gallery({ gallery, parentId }: { gallery: CrudGallery; parentId: number }) {
  const router = useRouter();
  const input = useRef<HTMLInputElement>(null);
  const [busy, setBusy] = useState("");
  const [errors, setErrors] = useState<string[]>([]);
  const base = `/api/proxy/control/manage/${gallery.res}`;
  const hasCover = gallery.items.some((m) => m.is_cover);

  async function upload(files: FileList | null) {
    if (!files?.length) return;
    const errs: string[] = [];
    let first = !hasCover;
    for (const [i, f] of Array.from(files).entries()) {
      setBusy(`Yuklanmoqda: ${i + 1} / ${files.length}`);
      const fd = new FormData();
      fd.append(gallery.parent, String(parentId));
      fd.append(gallery.file_field, f);
      const isImage = f.type.startsWith("image/");
      if (first && isImage) fd.append("is_cover", "true"); // muqova bo'lmasa — birinchi rasm muqova
      try {
        const r = await fetch(base, { method: "POST", body: fd });
        if (!r.ok) {
          const body = await r.json().catch(() => ({}));
          errs.push(`${f.name}: ${firstError(body) || "yuklab bo'lmadi"}`);
        } else if (first && isImage) first = false;
      } catch {
        errs.push(`${f.name}: tarmoq xatosi`);
      }
    }
    setErrors(errs);
    setBusy("");
    if (input.current) input.current.value = "";
    router.refresh();
  }

  async function act(id: number, method: "PATCH" | "DELETE") {
    if (method === "DELETE" && !window.confirm("Bu fayl o'chirilsinmi?")) return;
    setBusy(method === "DELETE" ? "O'chirilmoqda…" : "Saqlanmoqda…");
    const fd = new FormData();
    fd.append("is_cover", "true");
    const r = await fetch(`${base}/${id}`, { method, body: method === "PATCH" ? fd : undefined });
    if (!r.ok) {
      const body = await r.json().catch(() => ({}));
      setErrors([firstError(body) || "Bajarib bo'lmadi"]);
    } else setErrors([]);
    setBusy("");
    router.refresh();
  }

  return (
    <section className="card space-y-4 p-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="font-semibold">Rasm va videolar ({gallery.items.length})</h3>
          <p className="text-sm text-ink-mute">
            Rasm — jpg/png/webp, 6 MB gacha (20 ta); video — mp4/mov/webm, 20 MB gacha (4 ta). Bir nechtasini birdan tanlash mumkin.
          </p>
        </div>
        <label className={`btn-primary cursor-pointer ${busy ? "pointer-events-none opacity-60" : ""}`}>
          {busy || "+ Rasm / video qo'shish"}
          <input
            ref={input}
            type="file"
            multiple
            accept="image/jpeg,image/png,image/webp,video/mp4,video/quicktime,video/webm"
            className="hidden"
            onChange={(e) => upload(e.target.files)}
          />
        </label>
      </div>

      <LinkUpload res={gallery.parent} id={parentId} />

      {errors.length > 0 && (
        <ul className="space-y-1 rounded-xl bg-red-50 px-4 py-3 text-sm text-red-700">
          {errors.map((e, i) => (
            <li key={i}>{e}</li>
          ))}
        </ul>
      )}

      {gallery.items.length ? (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
          {gallery.items.map((m) => (
            <div key={m.id} className="overflow-hidden rounded-xl border border-sand-200 bg-white">
              <div className="relative aspect-[4/3] bg-sand-100">
                {m.kind === "video" ? (
                  <video src={m.url} className="h-full w-full object-cover" muted controls preload="metadata" />
                ) : (
                  <img src={m.url} alt="" className="h-full w-full object-cover" />
                )}
                {m.is_cover && (
                  <span className="absolute left-2 top-2 rounded-full bg-forest-600 px-2 py-0.5 text-xs font-semibold text-white">
                    Muqova
                  </span>
                )}
              </div>
              <div className="flex items-center justify-between gap-2 px-3 py-2 text-sm">
                {m.kind === "image" && !m.is_cover ? (
                  <button type="button" className="text-forest-700 hover:underline" onClick={() => act(m.id, "PATCH")} disabled={!!busy}>
                    Muqova qilish
                  </button>
                ) : (
                  <span className="text-ink-mute">{m.kind === "video" ? "Video" : ""}</span>
                )}
                <button type="button" className="text-red-600 hover:underline" onClick={() => act(m.id, "DELETE")} disabled={!!busy}>
                  O&apos;chirish
                </button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <p className="rounded-xl bg-sand-50 px-4 py-6 text-center text-sm text-ink-mute">Hali rasm yo&apos;q.</p>
      )}
    </section>
  );
}
