import { NextResponse, type NextRequest } from "next/server";

import { ACCESS_COOKIE, API_INTERNAL, REFRESH_COOKIE } from "@/lib/config";
import { jwtExp, setAuthCookies, clearAuthCookies } from "@/lib/auth-cookies";

/**
 * Access token muddati tugayotgan bo'lsa (yoki yo'q bo'lsa, lekin refresh bor) — jimgina yangilaydi.
 * Yangi token so'rovning o'ziga ham qo'yiladi, shunda shu sahifaning Server Component'lari uni ko'radi.
 */
export async function middleware(req: NextRequest) {
  const access = req.cookies.get(ACCESS_COOKIE)?.value;
  const refresh = req.cookies.get(REFRESH_COOKIE)?.value;
  const now = Math.floor(Date.now() / 1000);
  if (!refresh || (access && jwtExp(access) - now > 60)) return NextResponse.next();

  try {
    const r = await fetch(`${API_INTERNAL}/api/v1/auth/token/refresh/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh }),
      cache: "no-store",
    });
    if (!r.ok) {
      const res = NextResponse.next();
      clearAuthCookies(res);
      return res;
    }
    const tokens = (await r.json()) as { access: string; refresh?: string };
    req.cookies.set(ACCESS_COOKIE, tokens.access);
    const res = NextResponse.next({ request: { headers: req.headers } });
    setAuthCookies(res, tokens);
    return res;
  } catch {
    return NextResponse.next(); // backend vaqtincha ishlamasa — sahifa baribir ochilsin
  }
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|webp)$).*)"],
};
