import type { Metadata } from "next";
import { Suspense } from "react";

import { AuthCard } from "@/components/AuthCard";
import { TelegramLoginExchange } from "@/components/TelegramLoginExchange";

export const metadata: Metadata = { title: "Telegram orqali kirish", robots: { index: false } };

/** Telegram bot yuborgan havola shu yerga olib keladi: `/auth/telegram?code=...` */
export default function TelegramAuthPage() {
  return (
    <AuthCard title="Telegram orqali kirish">
      <Suspense>
        <TelegramLoginExchange />
      </Suspense>
    </AuthCard>
  );
}
