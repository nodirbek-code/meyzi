"use client";

import { useEffect, useRef, useState } from "react";

import { api, ClientApiError } from "@/lib/client";

import { TelegramLogo, useTelegramLogin } from "./TelegramButton";

type Me = { phone: string | null; phone_verified: boolean };

/**
 * "Telefon raqam qo'shish" — botga bir martalik havola bilan olib boradi. Bot foydalanuvchini havoladan taniydi
 * va faqat telefon raqamini so'raydi (Telegram kontakti). Raqam akkauntga yozilgach `onLinked(phone)` chaqiriladi:
 * sahifa akkauntni har 3 soniyada (va oynaga qaytganda) tekshirib turadi.
 */
export function TelegramPhoneButton({ onLinked, label = "Telefon raqam qo'shish" }: { onLinked: (phone: string) => void; label?: string }) {
  const telegram = useTelegramLogin();
  const [busy, setBusy] = useState(false);
  const [opened, setOpened] = useState(false);
  const [error, setError] = useState("");
  const linked = useRef(onLinked);
  linked.current = onLinked;

  useEffect(() => {
    if (!opened) return;
    let stopped = false;
    const started = Date.now();
    const check = async () => {
      try {
        const me = await api.get<Me>("/auth/me");
        if (!stopped && me.phone && me.phone_verified) {
          stopped = true;
          linked.current(me.phone);
        }
      } catch {
        /* tarmoq xatosi — keyingi safar */
      }
    };
    const timer = window.setInterval(() => {
      if (Date.now() - started > 10 * 60_000) window.clearInterval(timer);
      else void check();
    }, 3000);
    const onFocus = () => document.visibilityState === "visible" && void check();
    window.addEventListener("focus", onFocus);
    document.addEventListener("visibilitychange", onFocus);
    return () => {
      stopped = true;
      window.clearInterval(timer);
      window.removeEventListener("focus", onFocus);
      document.removeEventListener("visibilitychange", onFocus);
    };
  }, [opened]);

  if (telegram && !telegram.enabled) {
    return <p className="text-xs text-clay-700">Telegram bot hozircha sozlanmagan — telefon raqam qo&apos;shib bo&apos;lmaydi.</p>;
  }

  async function open() {
    // Oyna darhol ochiladi (aks holda brauzer so'rovdan keyingi popup'ni bloklaydi), havola keyin beriladi
    const win = window.open("", "_blank");
    setBusy(true);
    setError("");
    try {
      const { url } = await api.post<{ url: string }>("/auth/me/phone/telegram-link");
      if (win) win.location.href = url;
      else window.location.href = url;
      setOpened(true);
    } catch (e) {
      win?.close();
      setError(e instanceof ClientApiError ? e.message : "Xatolik yuz berdi");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-2">
      <button type="button" onClick={open} disabled={busy || !telegram} className="btn bg-[#229ED9] text-white hover:bg-[#1c8cc2] disabled:opacity-60">
        <TelegramLogo />
        {busy ? "Ochilmoqda…" : label}
      </button>
      {opened && (
        <p className="text-xs text-ink-soft">
          Telegram botda <b>📱 Telefon raqamni yuborish</b> tugmasini bosing. Raqam akkauntingizga yoziladi va shu yerda
          o&apos;zi paydo bo&apos;ladi.
        </p>
      )}
      {error && <p className="text-xs text-clay-700">{error}</p>}
    </div>
  );
}
