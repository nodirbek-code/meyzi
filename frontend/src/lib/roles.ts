import "server-only";

import { redirect } from "next/navigation";

import { apiGetOrNull, ApiError } from "./api";
import { requireUser } from "./session";

export type Roles = {
  agency: { name: string; slug: string; status: string; is_verified: boolean } | null;
  guide: { display_name: string; slug: string; status: string; moderation_note: string } | null;
  hotel: { name: string; slug: string; status: string; moderation_note: string } | null;
};

async function safe<T>(path: string): Promise<T | null> {
  try {
    return await apiGetOrNull<T>(path, { auth: true });
  } catch (e) {
    if (e instanceof ApiError && (e.status === 403 || e.status === 401)) return null;
    throw e;
  }
}

/** Foydalanuvchi qaysi kabinetlarga kira oladi (agentlik / gid / mehmonxona). */
export async function getRoles(): Promise<Roles> {
  const [agency, guide, hotel] = await Promise.all([
    safe<Roles["agency"]>("/cabinet/agency/"),
    safe<Roles["guide"]>("/guides/me/"),
    safe<Roles["hotel"]>("/hotels/me/"),
  ]);
  return { agency, guide, hotel };
}

export const isPartner = (r: Roles) => !!(r.agency || r.guide || r.hotel);

/**
 * Kabinet sahifasi uchun: kirmagan — login'ga; shu rol yo'q — /cabinet ga (u yerdan o'z kabinetiga),
 * umuman hamkor bo'lmasa — /account ga. Oddiy foydalanuvchi kabinetga kira olmaydi.
 */
export async function requireRole(role: keyof Roles, path: string): Promise<Roles> {
  await requireUser(path);
  const roles = await getRoles();
  if (!roles[role]) redirect(isPartner(roles) ? "/cabinet" : "/account");
  return roles;
}
