import type { Metadata } from "next";
import Link from "next/link";
import { Suspense } from "react";

import { AuthCard } from "@/components/AuthCard";
import { LoginForm } from "@/components/LoginForm";

export const metadata: Metadata = { title: "Kirish" };

export default function LoginPage() {
  return (
    <AuthCard title="Hisobingizga kiring" subtitle="Telefon raqamingiz (Telegram kodi), Google yoki email orqali.">
      <Suspense>
        <LoginForm />
      </Suspense>
      <p className="mt-6 text-center text-sm text-ink-soft">
        Hisobingiz yo&apos;qmi?{" "}
        <Link href="/register" className="font-semibold text-forest-600 hover:underline">
          Ro&apos;yxatdan o&apos;ting
        </Link>
      </p>
    </AuthCard>
  );
}
