"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useEffect, useRef, useState } from "react";

import { api, ClientApiError } from "@/lib/client";

import { FormError } from "./AuthCard";

const USED_KEY = "lz_tg_code";

function go(path: string) {
  // To'liq o'tish: yangi cookie'lar bilan sahifa qaytadan yuklanadi va bu sahifa qayta ishlamaydi
  window.location.replace(path);
}

/** Havoladagi bir martalik kodni JWT'ga almashtiradi (tokenlar httpOnly cookie'ga yoziladi). */
export function TelegramLoginExchange() {
  const code = useSearchParams().get("code") ?? "";
  const [error, setError] = useState(code ? "" : "Havolada kod yo'q. Botga /start yozib, yangi havola oling.");
  const started = useRef(false); // kod bir marta ishlaydi — React StrictMode ikkinchi so'rov yubormasin

  useEffect(() => {
    if (!code || started.current) return;
    started.current = true;
    (async () => {
      let usedBefore = false;
      try {
        usedBefore = sessionStorage.getItem(USED_KEY) === code;
      } catch {}
      if (!usedBefore) {
        try {
          const r = await api.auth<{ is_new?: boolean }>("telegram", { code });
          try {
            sessionStorage.setItem(USED_KEY, code);
          } catch {}
          return go(r.is_new ? "/account/profile?welcome=1" : "/account");
        } catch (e) {
          // pastda: balki allaqachon kirilgan
          if (!(e instanceof ClientApiError) || e.status !== 400) {
            return setError("Kirib bo'lmadi. Qayta urinib ko'ring.");
          }
          setError(e.message);
        }
      }
      // Havola avval ishlatilgan (sahifa qayta ochilgan) — foydalanuvchi allaqachon kirgan bo'lsa, kabinetga
      try {
        await api.get("/auth/me");
        return go("/account");
      } catch {
        setError((prev) => prev || "Havola yaroqsiz yoki muddati o'tgan. Botga /start yozib, yangi havola oling.");
      }
    })();
  }, [code]);

  if (error) {
    return (
      <div className="space-y-4">
        <FormError message={error} />
        <Link href="/login" className="btn-primary w-full py-3">
          Kirish sahifasiga qaytish
        </Link>
      </div>
    );
  }
  return <p className="text-sm text-ink-soft">Hisobingizga kirilmoqda…</p>;
}
