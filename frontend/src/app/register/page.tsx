import type { Metadata } from "next";
import Link from "next/link";

import { AuthCard } from "@/components/AuthCard";
import { RegisterForm } from "@/components/RegisterForm";

export const metadata: Metadata = { title: "Ro'yxatdan o'tish" };

export default function RegisterPage() {
  return (
    <AuthCard title="Hisob yaratish" subtitle="Email orqali ro'yxatdan o'tsangiz, emailingizga tasdiqlash kodi yuboriladi.">
      <RegisterForm />
      <div className="mt-6 space-y-2 text-center text-sm text-ink-soft">
        <p>
          Telefon orqali qulayroqmi?{" "}
          <Link href="/login" className="font-semibold text-forest-600 hover:underline">
            Telegram kodi bilan kiring
          </Link>
        </p>
        <p>
          Hisobingiz bormi?{" "}
          <Link href="/login" className="font-semibold text-forest-600 hover:underline">
            Kirish
          </Link>
        </p>
      </div>
    </AuthCard>
  );
}
