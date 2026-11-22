import { authProxy } from "../_shared";

/** Telegram bot yuborgan bir martalik havola kodi → backend tekshiradi → tokenlar cookie'ga. */
export async function POST(req: Request) {
  return authProxy("/auth/telegram/login/", await req.json());
}
