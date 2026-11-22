import { authProxy } from "../_shared";

/** Telefon raqam + parol → backend tekshiradi → tokenlar httpOnly cookie'ga. */
export async function POST(req: Request) {
  return authProxy("/auth/phone/login/", await req.json());
}
