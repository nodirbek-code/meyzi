"use client";

/** Brauzerdan backendga: /api/proxy orqali (token cookie'da). Xato bo'lsa — maydon xabarlari bilan. */
export class ClientApiError extends Error {
  constructor(
    public status: number,
    public data: Record<string, unknown>,
  ) {
    super(firstError(data) || `Xato ${status}`);
  }
}

export function firstError(data: unknown): string {
  if (!data || typeof data !== "object") return "";
  for (const v of Object.values(data as Record<string, unknown>)) {
    if (typeof v === "string") return v;
    if (Array.isArray(v) && typeof v[0] === "string") return v[0];
    if (v && typeof v === "object") {
      const inner = firstError(v);
      if (inner) return inner;
    }
  }
  return "";
}

async function request<T>(url: string, init: RequestInit): Promise<T> {
  const res = await fetch(url, init);
  const text = await res.text();
  const data = text ? JSON.parse(text) : {};
  if (!res.ok) {
    if (res.status === 429) throw new ClientApiError(429, { detail: data.detail || "Juda ko'p urinish. Biroz kuting." });
    throw new ClientApiError(res.status, data);
  }
  return data as T;
}

const json = (method: string, body?: unknown): RequestInit => ({
  method,
  headers: { "Content-Type": "application/json" },
  body: body === undefined ? undefined : JSON.stringify(body),
});

export const api = {
  get: <T>(path: string) => request<T>(`/api/proxy${path}`, { method: "GET" }),
  post: <T>(path: string, body?: unknown) => request<T>(`/api/proxy${path}`, json("POST", body ?? {})),
  patch: <T>(path: string, body: unknown) => request<T>(`/api/proxy${path}`, json("PATCH", body)),
  del: <T>(path: string) => request<T>(`/api/proxy${path}`, { method: "DELETE" }),
  /** Kirish/chiqish — tokenlar cookie'ga yoziladi */
  auth: <T>(action: "login" | "register" | "phone" | "google" | "logout", body?: unknown) =>
    request<T>(`/api/auth/${action}`, json("POST", body ?? {})),
};
