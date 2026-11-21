import { authProxy } from "../_shared";

/** Google Identity Services `credential` (ID token) → backend tekshiradi → tokenlar cookie'ga. */
export async function POST(req: Request) {
  return authProxy("/auth/google/", await req.json());
}
