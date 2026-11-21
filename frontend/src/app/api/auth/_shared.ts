import { NextResponse } from "next/server";

import { setAuthCookies } from "@/lib/auth-cookies";
import { backendFetch } from "@/lib/backend";

/** Backend auth endpoint'ini chaqiradi; muvaffaqiyatda tokenlarni cookie'ga yozib, faqat user'ni qaytaradi. */
export async function authProxy(path: string, body: unknown) {
  const r = await backendFetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!r.ok) return NextResponse.json(r.data, { status: r.status });
  const { access, refresh, ...rest } = r.data as { access: string; refresh: string };
  const res = NextResponse.json(rest);
  setAuthCookies(res, { access, refresh });
  return res;
}
