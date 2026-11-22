import "server-only";

import { notFound, redirect } from "next/navigation";

import { apiGet } from "./api";
import type { User } from "./types";
import { getUser } from "./session";

/** /control sahifalari: kirmagan — admin login'ga; oddiy foydalanuvchi — 404 (panel borligi ham ko'rinmaydi). */
export async function requireStaff(): Promise<User> {
  const user = await getUser();
  if (!user) redirect("/control/login");
  if (!user.is_staff) notFound();
  return user;
}

export function controlGet<T>(path: string, query?: Record<string, string | number | undefined>) {
  return apiGet<T>(`/control${path}`, { auth: true, revalidate: false, query });
}
