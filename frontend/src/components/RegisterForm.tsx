"use client";

import { useRouter } from "next/navigation";
import { useCallback, useState } from "react";

import { api, ClientApiError } from "@/lib/client";

import { Divider, FormError, TermsNote } from "./AuthCard";
import { GoogleButton } from "./GoogleButton";

export function RegisterForm() {
  const router = useRouter();
  const [f, setF] = useState({ first_name: "", last_name: "", email: "", password: "" });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const set = (k: keyof typeof f) => (e: React.ChangeEvent<HTMLInputElement>) => setF({ ...f, [k]: e.target.value });

  const welcome = useCallback(() => {
    router.push("/account/profile?welcome=1");
    router.refresh();
  }, [router]);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    setErrors({});
    try {
      await api.auth("register", f);
      welcome();
    } catch (err) {
      if (err instanceof ClientApiError) {
        const fieldErrors: Record<string, string> = {};
        for (const [k, v] of Object.entries(err.data)) fieldErrors[k] = Array.isArray(v) ? String(v[0]) : String(v);
        setErrors(fieldErrors);
        setError(fieldErrors.detail || fieldErrors.non_field_errors || "");
      } else setError("Xatolik yuz berdi");
      setBusy(false);
    }
  }

  const field = (k: keyof typeof f, label: string, type = "text", auto = "", placeholder = "") => (
    <label className="block">
      <span className="label">{label}</span>
      <input
        className="input"
        type={type}
        autoComplete={auto}
        placeholder={placeholder}
        required={k !== "last_name"}
        value={f[k]}
        onChange={set(k)}
      />
      {errors[k] && <span className="mt-1 block text-xs text-clay-700">{errors[k]}</span>}
    </label>
  );

  return (
    <div className="space-y-5">
      <GoogleButton onDone={welcome} label="signup_with" />
      <Divider text="yoki email bilan" />
      <form onSubmit={submit} className="space-y-4">
        <div className="grid grid-cols-2 gap-3">
          {field("first_name", "Ism", "text", "given-name")}
          {field("last_name", "Familiya", "text", "family-name")}
        </div>
        {field("email", "Email", "email", "email", "siz@email.com")}
        <div>
          {field("password", "Parol", "password", "new-password")}
          <p className="mt-1 text-xs text-ink-mute">Kamida 8 belgi, faqat raqamlardan iborat bo&apos;lmasin.</p>
        </div>
        <FormError message={error} />
        <button className="btn-primary w-full py-3" disabled={busy}>
          {busy ? "Yaratilmoqda…" : "Ro'yxatdan o'tish"}
        </button>
      </form>
      <TermsNote />
    </div>
  );
}
