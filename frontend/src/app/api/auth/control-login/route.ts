import { authProxy } from "../_shared";

/** Admin kirishi (/control): Django admin email + paroli → backend faqat adminni qabul qiladi → tokenlar cookie'ga. */
export async function POST(req: Request) {
  return authProxy("/control/login/", await req.json());
}
