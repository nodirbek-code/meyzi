import "server-only";

import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { cache } from "react";

import { apiGet } from "./api";
import { ACCESS_COOKIE } from "./config";
import type { User } from "./types";

/** Joriy foydalanuvchi (yo'q bo'lsa null). Token muddati middleware'da yangilanadi. */
// cache: bitta so'rov ichida (layout + sahifa) /auth/me/ bir marta chaqiriladi
export const getUser = cache(async (): Promise<User | null> => {
  if (!(await cookies()).get(ACCESS_COOKIE)) return null;
  try {
    return await apiGet<User>("/auth/me/", { auth: true });
  } catch {
    return null;
  }
});

/** Himoyalangan sahifa: layout va sahifa parallel render bo'ladi — shuning uchun sahifaning o'zi ham chaqirsin. */
export async function requireUser(next: string): Promise<User> {
  const user = await getUser();
  if (!user) redirect(`/login?next=${encodeURIComponent(next)}`);
  return user;
}
