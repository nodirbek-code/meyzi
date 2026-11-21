import { API_INTERNAL, API_PUBLIC } from "./config";

/** Route handler'lar uchun: backendga so'rov va javobni (manzillarni almashtirib) qaytarish. */
export async function backendFetch(path: string, init: RequestInit = {}) {
  const res = await fetch(`${API_INTERNAL}/api/v1${path}`, { ...init, cache: "no-store" });
  const text = (await res.text()).split(API_INTERNAL).join(API_PUBLIC);
  let data: unknown = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = { detail: "Serverdan noto'g'ri javob keldi." };
  }
  return { status: res.status, ok: res.ok, data };
}
