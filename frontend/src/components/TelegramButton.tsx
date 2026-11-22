"use client";

import { useEffect, useState } from "react";

import { api } from "@/lib/client";

type TelegramLogin = { enabled: boolean; bot_username: string | null; url: string | null };

export function TelegramLogo() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" aria-hidden>
      <circle cx="12" cy="12" r="12" fill="#229ED9" />
      <path
        fill="#fff"
        d="M5.4 11.8 16.9 7.4c.5-.2 1 .1.8 1l-2 9.3c-.1.6-.5.8-1.1.5l-3-2.2-1.4 1.4c-.2.2-.3.3-.6.3l.2-3.1 5.6-5.1c.2-.2 0-.3-.4-.1L8 13.7l-3-.9c-.6-.2-.6-.6.4-1Z"
      />
    </svg>
  );
}

/**
 * "Telegram orqali ro'yxatdan o'tish": botga olib boradi. Bot telefon raqam, ism-familiya va parolni
 * so'raydi, so'ng darhol kirish havolasini yuboradi (`/auth/telegram?code=...`). Keyingi safar user
 * saytga telefon + parol bilan kiradi. Sozlanmagan bo'lsa — o'chiq tugma ("tez kunda").
 */
/** `/features` → telegram_login (bot sozlanmagan bo'lsa `enabled: false`). */
export function useTelegramLogin() {
  const [info, setInfo] = useState<TelegramLogin | null>(null);
  useEffect(() => {
    let alive = true;
    api
      .get<{ telegram_login?: TelegramLogin }>("/features")
      .then((f) => alive && setInfo(f.telegram_login ?? { enabled: false, bot_username: null, url: null }))
      .catch(() => alive && setInfo({ enabled: false, bot_username: null, url: null }));
    return () => {
      alive = false;
    };
  }, []);
  return info;
}

/** Bot havolasi boshqa `start` parametri bilan (masalan, `parol` — parolni tiklash). */
export function botUrl(info: TelegramLogin | null, start: string) {
  return info?.bot_username ? `https://t.me/${info.bot_username}?start=${start}` : null;
}

export function TelegramButton({ label = "Telegram orqali ro'yxatdan o'tish" }: { label?: string }) {
  const info = useTelegramLogin();
  const [opened, setOpened] = useState(false);

  if (!info?.enabled || !info.url) {
    return (
      <button
        type="button"
        disabled
        className="btn-ghost w-full py-3"
        title={info ? "Telegram orqali ro'yxatdan o'tish tez kunda ishga tushadi" : undefined}
      >
        <TelegramLogo />
        {label}
        {info && <span className="text-xs font-normal text-ink-mute">· tez kunda</span>}
      </button>
    );
  }

  return (
    <div>
      <a
        href={info.url}
        target="_blank"
        rel="noopener noreferrer"
        onClick={() => setOpened(true)}
        className="btn w-full bg-[#229ED9] py-3 text-white hover:bg-[#1c8cc2]"
      >
        <TelegramLogo />
        {label}
      </a>
      {opened && (
        <p className="mt-2 text-center text-xs text-ink-soft">
          Telegram&apos;da <b>@{info.bot_username}</b> botiga telefon raqamingizni yuboring, ism-familiya va parol
          o&apos;rnating. Keyin saytga telefon raqam va parol bilan kirasiz.
        </p>
      )}
    </div>
  );
}
