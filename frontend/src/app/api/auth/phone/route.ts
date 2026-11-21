import { authProxy } from "../_shared";

/** Telegram kodni tekshirish → kirish (kod so'rash esa oddiy proxy orqali: /api/proxy/auth/phone/request-code/). */
export async function POST(req: Request) {
  return authProxy("/auth/phone/verify/", await req.json());
}
