import type { NextResponse } from "next/server";

import { ACCESS_COOKIE, REFRESH_COOKIE } from "./config";

const secure = process.env.NODE_ENV === "production";

/** JWT'lar faqat httpOnly cookie'da — brauzer JavaScript'i ularni o'qiy olmaydi (XSS'dan himoya). */
export function setAuthCookies(res: NextResponse, tokens: { access: string; refresh?: string }) {
  res.cookies.set(ACCESS_COOKIE, tokens.access, {
    httpOnly: true,
    secure,
    sameSite: "lax",
    path: "/",
    maxAge: 60 * 60 * 24, // haqiqiy muddat JWT ichida; middleware yangilaydi
  });
  if (tokens.refresh) {
    res.cookies.set(REFRESH_COOKIE, tokens.refresh, {
      httpOnly: true,
      secure,
      sameSite: "lax",
      path: "/",
      maxAge: 60 * 60 * 24 * 30,
    });
  }
}

export function clearAuthCookies(res: NextResponse) {
  res.cookies.delete(ACCESS_COOKIE);
  res.cookies.delete(REFRESH_COOKIE);
}

/** JWT exp (soniya) — imzoni tekshirmaydi, faqat yangilash vaqtini bilish uchun. */
export function jwtExp(token: string): number {
  try {
    const payload = JSON.parse(atob(token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/")));
    return Number(payload.exp) || 0;
  } catch {
    return 0;
  }
}
