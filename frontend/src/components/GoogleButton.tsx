"use client";

import { useEffect, useRef, useState } from "react";

import { api, ClientApiError } from "@/lib/client";

type GoogleId = {
  accounts: {
    id: {
      initialize: (o: { client_id: string; callback: (r: { credential: string }) => void; ux_mode?: string }) => void;
      renderButton: (el: HTMLElement, o: Record<string, unknown>) => void;
    };
  };
};
declare global {
  interface Window {
    google?: GoogleId;
  }
}

const SCRIPT = "https://accounts.google.com/gsi/client";

function loadScript(): Promise<void> {
  return new Promise((resolve, reject) => {
    if (window.google?.accounts) return resolve();
    const existing = document.querySelector<HTMLScriptElement>(`script[src="${SCRIPT}"]`);
    const s = existing ?? document.createElement("script");
    s.addEventListener("load", () => resolve());
    s.addEventListener("error", () => reject(new Error("Google skripti yuklanmadi")));
    if (!existing) {
      s.src = SCRIPT;
      s.async = true;
      document.head.appendChild(s);
    }
  });
}

/**
 * "Google orqali kirish". Client ID backenddan (`/features/` → google_login) olinadi.
 * Sozlanmagan bo'lsa — o'chiq tugma ("tez kunda").
 */
export function GoogleButton({ onDone, label = "signin_with" }: { onDone: () => void; label?: "signin_with" | "signup_with" }) {
  const box = useRef<HTMLDivElement>(null);
  const [state, setState] = useState<"loading" | "ready" | "off">("loading");
  const [error, setError] = useState("");

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const f = await api.get<{ google_login?: { enabled: boolean; client_id: string | null } }>("/features");
        const cid = f.google_login?.enabled ? f.google_login.client_id : null;
        if (!cid) return alive && setState("off");
        await loadScript();
        if (!alive || !box.current || !window.google) return;
        window.google.accounts.id.initialize({
          client_id: cid,
          callback: async ({ credential }) => {
            setError("");
            try {
              await api.auth("google", { credential });
              onDone();
            } catch (e) {
              setError(e instanceof ClientApiError ? e.message : "Google orqali kirib bo'lmadi");
            }
          },
        });
        window.google.accounts.id.renderButton(box.current, {
          theme: "outline",
          size: "large",
          shape: "rectangular",
          text: label,
          width: box.current.offsetWidth || 360,
          locale: "uz",
        });
        setState("ready");
      } catch {
        if (alive) setState("off");
      }
    })();
    return () => {
      alive = false;
    };
  }, [label, onDone]);

  return (
    <div>
      <div ref={box} className={state === "ready" ? "flex justify-center" : "hidden"} />
      {state !== "ready" && (
        <button type="button" disabled className="btn-ghost w-full py-3" title={state === "off" ? "Google orqali kirish tez kunda ishga tushadi" : undefined}>
          <svg width="18" height="18" viewBox="0 0 48 48" aria-hidden>
            <path fill="#FFC107" d="M43.6 20.5H42V20H24v8h11.3C33.7 32.7 29.2 36 24 36c-6.6 0-12-5.4-12-12s5.4-12 12-12c3 0 5.8 1.1 7.9 3l5.7-5.7C34 6.1 29.3 4 24 4 12.9 4 4 12.9 4 24s8.9 20 20 20 20-8.9 20-20c0-1.3-.1-2.4-.4-3.5Z" />
            <path fill="#FF3D00" d="m6.3 14.7 6.6 4.8C14.7 15.1 19 12 24 12c3 0 5.8 1.1 7.9 3l5.7-5.7C34 6.1 29.3 4 24 4 16.3 4 9.7 8.3 6.3 14.7Z" />
            <path fill="#4CAF50" d="M24 44c5.2 0 9.9-2 13.4-5.2l-6.2-5.2C29.2 35.1 26.7 36 24 36c-5.2 0-9.6-3.3-11.3-8l-6.5 5C9.5 39.6 16.2 44 24 44Z" />
            <path fill="#1976D2" d="M43.6 20.5H42V20H24v8h11.3a12 12 0 0 1-4.1 5.6l6.2 5.2C36.9 39.2 44 34 44 24c0-1.3-.1-2.4-.4-3.5Z" />
          </svg>
          Google orqali kirish
          {state === "off" && <span className="text-xs font-normal text-ink-mute">· tez kunda</span>}
        </button>
      )}
      {error && <p className="mt-2 text-center text-xs text-clay-700">{error}</p>}
    </div>
  );
}
