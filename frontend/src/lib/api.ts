import "server-only";

import { cookies } from "next/headers";

import { ACCESS_COOKIE, API_INTERNAL, API_PUBLIC } from "./config";

export class ApiError extends Error {
  constructor(
    public status: number,
    public data: unknown,
  ) {
    super(`API ${status}`);
  }
}

type Options = { auth?: boolean; revalidate?: number | false; query?: Record<string, string | number | undefined> };

/**
 * Server tomonda backenddan o'qish (Server Component'lar uchun).
 * Javobdagi ichki manzil (web:8000) brauzer ko'radigan manzilga almashtiriladi — rasm URL'lari ishlashi uchun.
 */
export async function apiGet<T>(path: string, opts: Options = {}): Promise<T> {
  const url = new URL(`${API_INTERNAL}/api/v1${path}`);
  for (const [k, v] of Object.entries(opts.query || {})) {
    if (v !== undefined && v !== "") url.searchParams.set(k, String(v));
  }
  const headers: Record<string, string> = { Accept: "application/json" };
  if (opts.auth) {
    const token = (await cookies()).get(ACCESS_COOKIE)?.value;
    if (token) headers.Authorization = `Bearer ${token}`;
  }
  const res = await fetch(url, {
    headers,
    ...(opts.auth || opts.revalidate === false ? { cache: "no-store" } : { next: { revalidate: opts.revalidate ?? 60 } }),
  });
  const text = (await res.text()).split(API_INTERNAL).join(API_PUBLIC);
  const data = text ? JSON.parse(text) : null;
  if (!res.ok) throw new ApiError(res.status, data);
  return data as T;
}

/** 404 bo'lsa null (sahifada notFound() chaqirish uchun). */
export async function apiGetOrNull<T>(path: string, opts: Options = {}): Promise<T | null> {
  try {
    return await apiGet<T>(path, opts);
  } catch (e) {
    if (e instanceof ApiError && e.status === 404) return null;
    throw e;
  }
}
