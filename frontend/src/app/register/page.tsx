import type { Metadata } from "next";
import Link from "next/link";
import { Suspense } from "react";

import { AuthCard } from "@/components/AuthCard";
import { LoginForm } from "@/components/LoginForm";

export const metadata: Metadata = { title: "Ro'yxatdan o'tish" };

export default function RegisterPage() {
  return (
    <AuthCard title="Hisob yaratish" subtitle="Telegram bot (telefon, ism va parol) yoki Google orqali — bir daqiqada.">
      <Suspense>
        <LoginForm mode="register" />
      </Suspense>
      <p className="mt-6 text-center text-sm text-ink-soft">
        Hisobingiz bormi?{" "}
        <Link href="/login" className="font-semibold text-forest-600 hover:underline">
          Kirish
        </Link>
      </p>
    </AuthCard>
  );
}
