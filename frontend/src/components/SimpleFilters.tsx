"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useState } from "react";

export type FilterField =
  | { name: string; label: string; type: "select"; options: [string, string][] }
  | { name: string; label: string; type: "date" | "number" | "text"; placeholder?: string; min?: string };

/** Gorizontal filtr paneli (gidlar, mehmonxonalar) — qiymatlar URL'da. */
export function SimpleFilters({ fields }: { fields: FilterField[] }) {
  const router = useRouter();
  const pathname = usePathname();
  const params = useSearchParams();
  const [v, setV] = useState<Record<string, string>>(() => Object.fromEntries(fields.map((f) => [f.name, params.get(f.name) ?? ""])));

  function submit(e: React.FormEvent) {
    e.preventDefault();
    const q = new URLSearchParams();
    for (const [k, val] of Object.entries(v)) if (val) q.set(k, val);
    router.push(`${pathname}${q.size ? `?${q}` : ""}`);
  }

  return (
    <form onSubmit={submit} className="card grid gap-3 p-4 sm:grid-cols-2 lg:grid-cols-[repeat(auto-fit,minmax(150px,1fr))] lg:items-end">
      {fields.map((f) => (
        <label key={f.name} className="block">
          <span className="label">{f.label}</span>
          {f.type === "select" ? (
            <select className="input" value={v[f.name]} onChange={(e) => setV({ ...v, [f.name]: e.target.value })}>
              {f.options.map(([val, lab]) => <option key={val} value={val}>{lab}</option>)}
            </select>
          ) : (
            <input
              className="input"
              type={f.type}
              min={f.type === "date" ? f.min : f.type === "number" ? "1" : undefined}
              placeholder={f.placeholder}
              value={v[f.name]}
              onChange={(e) => setV({ ...v, [f.name]: e.target.value })}
            />
          )}
        </label>
      ))}
      <button className="btn-primary h-[42px]">Qidirish</button>
    </form>
  );
}
