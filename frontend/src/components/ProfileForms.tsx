"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { api, ClientApiError } from "@/lib/client";
import type { User } from "@/lib/types";

import { TelegramLogo, useTelegramLogin } from "./TelegramButton";

function useRun() {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [ok, setOk] = useState("");
  async function run(fn: () => Promise<string | void>) {
    setBusy(true);
    setError("");
    setOk("");
    try {
      const msg = await fn();
      if (msg) setOk(msg);
    } catch (e) {
      setError(e instanceof ClientApiError ? e.message : "Xatolik");
    } finally {
      setBusy(false);
    }
  }
  return { busy, error, ok, run };
}

export function ProfileForm({ user }: { user: User }) {
  const router = useRouter();
  const [f, setF] = useState({ first_name: user.first_name, last_name: user.last_name });
  const { busy, error, ok, run } = useRun();
  return (
    <form className="space-y-4" onSubmit={(e) => { e.preventDefault(); run(async () => { await api.patch("/auth/me", f); router.refresh(); return "Saqlandi"; }); }}>
      <div className="grid gap-3 sm:grid-cols-2">
        <label><span className="label">Ism</span><input className="input" value={f.first_name} onChange={(e) => setF({ ...f, first_name: e.target.value })} /></label>
        <label><span className="label">Familiya</span><input className="input" value={f.last_name} onChange={(e) => setF({ ...f, last_name: e.target.value })} /></label>
      </div>
      {error && <p className="text-sm text-clay-700">{error}</p>}
      {ok && <p className="text-sm text-forest-700">{ok}</p>}
      <button className="btn-primary" disabled={busy}>Saqlash</button>
    </form>
  );
}

/** Profilga email ulash: email → 6 xonali kod emailga → kod to'g'ri bo'lsa email tasdiqlangan holda yoziladi. */
export function AttachEmail({ current }: { current?: string | null }) {
  const router = useRouter();
  const [email, setEmail] = useState(current ?? "");
  const [code, setCode] = useState("");
  const [sent, setSent] = useState(false);
  const { busy, error, ok, run } = useRun();

  const sendCode = () =>
    run(async () => {
      await api.post("/auth/me/email/request-code", { email });
      setSent(true);
      setCode("");
      return "Kod emailingizga yuborildi. Pochtangizni (va «Spam» papkasini) tekshiring.";
    });

  return (
    <form
      className="space-y-3"
      onSubmit={(e) => {
        e.preventDefault();
        if (!sent) return sendCode();
        run(async () => {
          await api.post("/auth/me/email/verify", { email, code });
          setSent(false);
          router.refresh();
          return "Email ulandi";
        });
      }}
    >
      <span className="label">{current ? "Emailni tasdiqlash" : "Email qo'shish"}</span>
      <div className="flex flex-wrap gap-2">
        <input
          className="input w-full sm:w-72"
          type="email"
          autoComplete="email"
          placeholder="siz@email.com"
          required
          value={email}
          disabled={sent}
          onChange={(e) => setEmail(e.target.value)}
        />
        {sent && (
          <input
            className="input w-40 text-center font-mono tracking-[0.4em]"
            maxLength={6}
            inputMode="numeric"
            autoComplete="one-time-code"
            placeholder="Kod"
            autoFocus
            value={code}
            onChange={(e) => setCode(e.target.value.replace(/\D/g, ""))}
          />
        )}
        <button className="btn-primary" disabled={busy || !email || (sent && code.length !== 6)}>
          {busy ? "Kuting…" : sent ? "Tasdiqlash" : "Kod yuborish"}
        </button>
      </div>
      {sent && (
        <p className="text-xs text-ink-soft">
          <button type="button" className="font-semibold text-forest-600 hover:underline" onClick={() => { setSent(false); setCode(""); }}>
            Emailni o&apos;zgartirish
          </button>
          {" · "}
          <button type="button" className="font-semibold text-forest-600 hover:underline" disabled={busy} onClick={sendCode}>
            Kodni qayta yuborish
          </button>
        </p>
      )}
      {error && <p className="text-sm text-clay-700">{error}</p>}
      {ok && <p className="text-sm text-forest-700">{ok}</p>}
    </form>
  );
}

/**
 * Telefon raqami yo'q foydalanuvchi (masalan Google orqali kirgan) uchun: botga bir martalik havola bilan
 * olib boradi — bot kimligini havoladan biladi va faqat telefon raqamini so'raydi.
 * Foydalanuvchi saytga qaytganda (oyna fokusga qaytsa) profil avtomatik yangilanadi.
 */
export function AddPhoneViaTelegram() {
  const router = useRouter();
  const telegram = useTelegramLogin();
  const { busy, error, run } = useRun();
  const [opened, setOpened] = useState(false);

  useEffect(() => {
    if (!opened) return;
    const refresh = () => document.visibilityState === "visible" && router.refresh();
    document.addEventListener("visibilitychange", refresh);
    window.addEventListener("focus", refresh);
    return () => {
      document.removeEventListener("visibilitychange", refresh);
      window.removeEventListener("focus", refresh);
    };
  }, [opened, router]);

  const open = () => {
    // Oyna darhol ochiladi (aks holda brauzer so'rovdan keyingi popup'ni bloklaydi), havola keyin beriladi
    const win = window.open("", "_blank");
    run(async () => {
      try {
        const { url } = await api.post<{ url: string }>("/auth/me/phone/telegram-link");
        if (win) win.location.href = url;
        else window.location.href = url;
        setOpened(true);
      } catch (e) {
        win?.close();
        throw e;
      }
    });
  };

  if (!telegram?.enabled) return null; // bot sozlanmagan — tugma ko'rsatilmaydi

  return (
    <div className="space-y-2">
      <button
        type="button"
        onClick={open}
        disabled={busy}
        className="btn bg-[#229ED9] text-white hover:bg-[#1c8cc2] disabled:opacity-60"
      >
        <TelegramLogo />
        {busy ? "Ochilmoqda…" : "Telefon raqam qo'shish"}
      </button>
      {opened && (
        <p className="text-xs text-ink-soft">
          Telegram botda <b>📱 Telefon raqamni yuborish</b> tugmasini bosing. Raqam akkauntingizga yoziladi —
          saytga qaytganingizda shu sahifa o&apos;zi yangilanadi.{" "}
          <button type="button" className="underline" onClick={() => router.refresh()}>
            Yangilash
          </button>
        </p>
      )}
      {error && <p className="text-sm text-clay-700">{error}</p>}
    </div>
  );
}
