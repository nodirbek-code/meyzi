import { cookies } from "next/headers";
import { NextResponse } from "next/server";

import { API_INTERNAL, API_PUBLIC, ACCESS_COOKIE } from "@/lib/config";

/**
 * Brauzer → /api/proxy/<yo'l> → backend /api/v1/<yo'l>, Authorization cookie'dagi tokendan qo'shiladi.
 * Shu tufayli brauzer JWT'ni hech qachon ko'rmaydi. Faqat /api/v1 ostidagi yo'llar.
 */
async function handle(req: Request, ctx: { params: Promise<{ path: string[] }> }) {
  const { path } = await ctx.params;
  if (path.some((p) => p === ".." || p.includes("\\"))) {
    return NextResponse.json({ detail: "Noto'g'ri yo'l" }, { status: 400 });
  }
  const search = new URL(req.url).search;
  const target = `${API_INTERNAL}/api/v1/${path.map(encodeURIComponent).join("/")}/${search}`;

  const headers: Record<string, string> = { Accept: "application/json" };
  const contentType = req.headers.get("content-type");
  if (contentType) headers["Content-Type"] = contentType; // multipart chegarasi (boundary) saqlanadi
  const token = (await cookies()).get(ACCESS_COOKIE)?.value;
  if (token) headers.Authorization = `Bearer ${token}`;

  const hasBody = !["GET", "HEAD"].includes(req.method);
  const res = await fetch(target, {
    method: req.method,
    headers,
    body: hasBody ? await req.arrayBuffer() : undefined,
    cache: "no-store",
  });
  const text = (await res.text()).split(API_INTERNAL).join(API_PUBLIC);
  return new NextResponse(text || null, {
    status: res.status,
    headers: { "Content-Type": res.headers.get("content-type") || "application/json" },
  });
}

export { handle as GET, handle as POST, handle as PATCH, handle as PUT, handle as DELETE };
