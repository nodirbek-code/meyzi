import { cookies } from "next/headers";
import { NextResponse } from "next/server";

import { clearAuthCookies } from "@/lib/auth-cookies";
import { backendFetch } from "@/lib/backend";
import { ACCESS_COOKIE, REFRESH_COOKIE } from "@/lib/config";

export async function POST() {
  const jar = await cookies();
  const access = jar.get(ACCESS_COOKIE)?.value;
  const refresh = jar.get(REFRESH_COOKIE)?.value;
  if (access && refresh) {
    // refresh tokenni serverda ham bekor qilamiz (xato bo'lsa ham cookie'lar o'chiriladi)
    await backendFetch("/auth/logout/", {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${access}` },
      body: JSON.stringify({ refresh }),
    }).catch(() => null);
  }
  const res = NextResponse.json({ ok: true });
  clearAuthCookies(res);
  return res;
}
