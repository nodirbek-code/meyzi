import "server-only";

import { notFound, redirect } from "next/navigation";

import { apiGet, ApiError } from "./api";
import type { User } from "./types";
import { getUser } from "./session";

/** /control sahifalari: kirmagan — admin login'ga; oddiy foydalanuvchi — 404 (panel borligi ham ko'rinmaydi). */
export async function requireStaff(): Promise<User> {
  const user = await getUser();
  if (!user) redirect("/control/login");
  if (!user.is_staff) notFound();
  return user;
}

/** Backend'dan o'qish; ishchiga tegishli bo'lmagan bo'lim (403/404) — 404 sahifasi. */
export async function controlGet<T>(path: string, query?: Record<string, string | number | undefined>): Promise<T> {
  try {
    return await apiGet<T>(`/control${path}`, { auth: true, revalidate: false, query });
  } catch (e) {
    if (e instanceof ApiError && (e.status === 403 || e.status === 404)) notFound();
    throw e;
  }
}
