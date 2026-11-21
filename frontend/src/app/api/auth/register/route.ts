import { authProxy } from "../_shared";

export async function POST(req: Request) {
  return authProxy("/auth/register/", await req.json());
}
