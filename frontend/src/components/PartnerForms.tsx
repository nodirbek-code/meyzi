"use client";

import { useEffect, useState } from "react";

import { firstError } from "@/lib/client";
import { AMENITIES, LANGUAGE_NAMES, SPECIALIZATIONS } from "@/lib/format";
import type { DestinationShort } from "@/lib/types";
import { DOC_ACCEPT, fileError, IMAGE_ACCEPT, IMAGE_MAX_MB } from "@/lib/uploads";

import { phoneReady, VerifiedPhoneField, type VerifiedPhone } from "./PhoneField";

function Checks({ options, value, onChange }: { options: Record<string, string>; value: string[]; onChange: (v: string[]) => void }) {
  return (
    <div className="flex flex-wrap gap-2">
      {Object.entries(options).map(([k, l]) => {
        const on = value.includes(k);
        return (
          <button
            type="button"
            key={k}
            aria-pressed={on}
            onClick={() => onChange(on ? value.filter((x) => x !== k) : [...value, k])}
            className={`chip border px-3 py-1.5 transition ${on ? "border-forest-600 bg-forest-600 text-white" : "border-sand-300 bg-white text-ink-soft hover:border-forest-400"}`}
          >
            {on && "✓ "}
            {l}
          </button>
        );
      })}
    </div>
  );
}

function Done({ text }: { text: string }) {
  return (
    <div className="card p-10 text-center">
      <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-forest-600 text-2xl text-white">✓</div>
      <h3 className="mt-4 text-xl">Ariza yuborildi</h3>
      <p className="mt-2 text-sm text-ink-soft">{text}</p>
    </div>
  );
}

function Req() {
  return <span className="text-clay-500"> *</span>;
}

/** Fayl tanlash: format va hajm darhol tekshiriladi (xato bo'lsa fayl qabul qilinmaydi). */
function FilePick({
  label,
  accept,
  kind,
  hint,
  file,
  onChange,
  preview,
}: {
  label: string;
  accept: string;
  kind: "image" | "document";
  hint: string;
  file: File | null;
  onChange: (f: File | null) => void;
  preview?: boolean;
}) {
  const [error, setError] = useState("");
  const [url, setUrl] = useState<string | null>(null);
  useEffect(() => {
    if (!preview || !file) return setUrl(null);
    const u = URL.createObjectURL(file);
    setUrl(u);
    return () => URL.revokeObjectURL(u);
  }, [file, preview]);
  return (
    <label className="block">
      <span className="label">
        {label}
        <Req />
      </span>
      <div className="flex items-center gap-3">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        {url && <img src={url} alt="" className="h-14 w-14 shrink-0 rounded-full object-cover" />}
        <input
          className="input py-2"
          type="file"
          accept={accept}
          required={!file}
          onChange={(e) => {
            const f = e.target.files?.[0] ?? null;
            const err = f ? fileError(f, kind) : null;
            setError(err ?? "");
            if (err) e.target.value = "";
            onChange(err ? null : f);
          }}
        />
      </div>
      <span className={`mt-1 block text-xs ${error ? "text-clay-700" : "text-ink-mute"}`}>{error || hint}</span>
    </label>
  );
}

/** multipart (fayl bilan) — ro'yxatlar takroriy kalitlar sifatida */
async function sendForm(url: string, fields: Record<string, string | string[] | File | null>) {
  const fd = new FormData();
  for (const [k, v] of Object.entries(fields)) {
    if (v === null || v === "") continue;
    if (Array.isArray(v)) v.forEach((x) => fd.append(k, x));
    else fd.append(k, v);
  }
  const res = await fetch(url, { method: "POST", body: fd });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(firstError(data) || "Xatolik");
}

const digits = (s: string) => s.replace(/\D/g, "");

export function BecomeGuideForm({ destinations, trustedPhone }: { destinations: DestinationShort[]; trustedPhone?: string | null }) {
  const [f, setF] = useState({
    display_name: "",
    bio: "",
    experience_years: "1",
    certificate_number: "",
    price_half_day_uzs: "",
    price_full_day_uzs: "",
    price_per_day_uzs: "",
  });
  const [phone, setPhone] = useState<VerifiedPhone>({ phone: trustedPhone ?? "", token: "" });
  const [langs, setLangs] = useState<string[]>(["uz"]);
  const [specs, setSpecs] = useState<string[]>([]);
  const [dests, setDests] = useState<string[]>([]);
  const [cert, setCert] = useState<File | null>(null);
  const [photo, setPhoto] = useState<File | null>(null);
  const [error, setError] = useState("");
  const [done, setDone] = useState(false);
  const [busy, setBusy] = useState(false);
  const set = (k: keyof typeof f) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => setF({ ...f, [k]: e.target.value });
  const ready = f.display_name.trim() && langs.length && dests.length && photo && cert && phoneReady(phone, trustedPhone);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await sendForm("/api/proxy/guides/me", {
        photo,
        ...f,
        phone: phone.phone,
        phone_token: phone.token,
        languages: langs,
        specializations: specs,
        destinations: dests,
        certificate_file: cert,
      });
      setDone(true);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }
  if (done)
    return <Done text="Jamoamiz 48 soat ichida profilingizni tekshiradi. Natija emailingizga keladi. Tasdiqlangach, kabinetda uchrashuv joylaringizni qo'shing." />;
  const destOptions = Object.fromEntries(destinations.map((d) => [d.slug, d.name]));
  return (
    <form onSubmit={submit} className="card space-y-6 p-6 sm:p-8">
      <fieldset className="space-y-4">
        <legend className="mb-1 font-sans text-base font-semibold">Asosiy ma&apos;lumotlar</legend>
        <label className="block">
          <span className="label">
            Ism familiya
            <Req />
          </span>
          <input className="input" required value={f.display_name} onChange={set("display_name")} />
        </label>
        <FilePick
          label="O'zingizning rasmingiz"
          accept={IMAGE_ACCEPT}
          kind="image"
          hint={`Yuzingiz aniq ko'rinadigan rasm — jpg, png yoki webp, ${IMAGE_MAX_MB} MB gacha. Sayohatchilar shu rasmni ko'radi.`}
          file={photo}
          onChange={setPhoto}
          preview
        />
        <VerifiedPhoneField value={phone} onChange={setPhone} trustedPhone={trustedPhone} />
        <label className="block">
          <span className="label">O&apos;zingiz haqingizda</span>
          <textarea className="input min-h-24" placeholder="Tajribangiz, qiziqishlaringiz, qaysi joylarni yaxshi bilasiz…" value={f.bio} onChange={set("bio")} />
        </label>
      </fieldset>

      <fieldset className="space-y-4 border-t border-sand-200 pt-6">
        <legend className="mb-1 font-sans text-base font-semibold">Ish hududi va tillar</legend>
        <div>
          <span className="label">
            Shaharlar
            <Req />
          </span>
          <Checks options={destOptions} value={dests} onChange={setDests} />
        </div>
        <div>
          <span className="label">
            Tillar
            <Req />
          </span>
          <Checks options={LANGUAGE_NAMES} value={langs} onChange={setLangs} />
        </div>
        <div>
          <span className="label">Yo&apos;nalishlar</span>
          <Checks options={SPECIALIZATIONS} value={specs} onChange={setSpecs} />
        </div>
      </fieldset>

      <fieldset className="space-y-4 border-t border-sand-200 pt-6">
        <legend className="mb-1 font-sans text-base font-semibold">Narxlar (so&apos;m)</legend>
        <div className="grid gap-4 sm:grid-cols-3">
          <label>
            <span className="label">
              Yarim kun (4 soat)
              <Req />
            </span>
            <input className="input" required inputMode="numeric" value={f.price_half_day_uzs} onChange={(e) => setF({ ...f, price_half_day_uzs: digits(e.target.value) })} />
          </label>
          <label>
            <span className="label">
              To&apos;liq kun (8 soat)
              <Req />
            </span>
            <input className="input" required inputMode="numeric" value={f.price_full_day_uzs} onChange={(e) => setF({ ...f, price_full_day_uzs: digits(e.target.value) })} />
          </label>
          <label>
            <span className="label">
              Ko&apos;p kunlik (1 kun)
              <Req />
            </span>
            <input className="input" required inputMode="numeric" value={f.price_per_day_uzs} onChange={(e) => setF({ ...f, price_per_day_uzs: digits(e.target.value) })} />
          </label>
        </div>
      </fieldset>

      <fieldset className="space-y-4 border-t border-sand-200 pt-6">
        <legend className="mb-1 font-sans text-base font-semibold">Tajriba va sertifikat</legend>
        <div className="grid gap-4 sm:grid-cols-2">
          <label>
            <span className="label">Tajriba (yil)</span>
            <input className="input" type="number" min={0} value={f.experience_years} onChange={set("experience_years")} />
          </label>
          <label>
            <span className="label">Sertifikat raqami</span>
            <input className="input" value={f.certificate_number} onChange={set("certificate_number")} />
          </label>
        </div>
        <FilePick
          label="Gid sertifikati"
          accept={DOC_ACCEPT}
          kind="document"
          hint={`pdf, jpg yoki png — ${IMAGE_MAX_MB} MB gacha.`}
          file={cert}
          onChange={setCert}
        />
        <p className="text-xs text-ink-mute">Sertifikat faqat tekshiruvchilarimizga ko&apos;rinadi.</p>
      </fieldset>

      {error && <p className="rounded-xl bg-clay-50 px-3 py-2 text-sm text-clay-700">{error}</p>}
      <button className="btn-primary w-full py-3.5 text-base" disabled={busy || !ready}>
        {busy ? "Yuborilmoqda…" : "Ariza yuborish"}
      </button>
    </form>
  );
}

export function JoinHotelForm({ destinations, trustedPhone }: { destinations: DestinationShort[]; trustedPhone?: string | null }) {
  const [f, setF] = useState({
    name: "",
    kind: "hotel",
    destination: destinations[0]?.slug ?? "",
    stars: "",
    address: "",
    email: "",
    description: "",
    cancellation_policy: "free",
  });
  const [phone, setPhone] = useState<VerifiedPhone>({ phone: trustedPhone ?? "", token: "" });
  const [amen, setAmen] = useState<string[]>(["wifi"]);
  const [error, setError] = useState("");
  const [done, setDone] = useState(false);
  const [busy, setBusy] = useState(false);
  const set = (k: keyof typeof f) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) =>
    setF({ ...f, [k]: e.target.value });
  const ready = f.name.trim() && f.address.trim() && phoneReady(phone, trustedPhone);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await sendForm("/api/proxy/hotels/me", { ...f, phone: phone.phone, phone_token: phone.token, amenities: amen });
      setDone(true);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }
  if (done) return <Done text="Mehmonxonangiz tekshiruvdan o'tgach, kabinetda xona turlari va rasmlarni qo'shasiz." />;
  return (
    <form onSubmit={submit} className="card space-y-6 p-6 sm:p-8">
      <fieldset className="space-y-4">
        <legend className="mb-1 font-sans text-base font-semibold">Joy haqida</legend>
        <div className="grid gap-4 sm:grid-cols-2">
          <label>
            <span className="label">
              Nomi
              <Req />
            </span>
            <input className="input" required value={f.name} onChange={set("name")} />
          </label>
          <label>
            <span className="label">Turi</span>
            <select className="input" value={f.kind} onChange={set("kind")}>
              <option value="hotel">Mehmonxona</option>
              <option value="hostel">Hostel</option>
              <option value="guesthouse">Mehmon uyi</option>
              <option value="resort">Dam olish maskani</option>
            </select>
          </label>
          <label>
            <span className="label">
              Shahar
              <Req />
            </span>
            <select className="input" value={f.destination} onChange={set("destination")}>
              {destinations.map((d) => (
                <option key={d.slug} value={d.slug}>
                  {d.name}
                </option>
              ))}
            </select>
          </label>
          <label>
            <span className="label">Yulduz</span>
            <select className="input" value={f.stars} onChange={set("stars")}>
              <option value="">—</option>
              {[1, 2, 3, 4, 5].map((n) => (
                <option key={n} value={n}>
                  {"★".repeat(n)}
                </option>
              ))}
            </select>
          </label>
        </div>
        <label className="block">
          <span className="label">
            Manzil
            <Req />
          </span>
          <input className="input" required value={f.address} onChange={set("address")} />
        </label>
        <label className="block">
          <span className="label">Tavsif</span>
          <textarea className="input min-h-24" value={f.description} onChange={set("description")} />
        </label>
      </fieldset>

      <fieldset className="space-y-4 border-t border-sand-200 pt-6">
        <legend className="mb-1 font-sans text-base font-semibold">Aloqa</legend>
        <VerifiedPhoneField value={phone} onChange={setPhone} trustedPhone={trustedPhone} />
        <label className="block">
          <span className="label">Email</span>
          <input className="input" type="email" value={f.email} onChange={set("email")} />
        </label>
      </fieldset>

      <fieldset className="space-y-4 border-t border-sand-200 pt-6">
        <legend className="mb-1 font-sans text-base font-semibold">Qulayliklar va shartlar</legend>
        <Checks options={AMENITIES} value={amen} onChange={setAmen} />
        <label className="block">
          <span className="label">Bekor qilish siyosati</span>
          <select className="input" value={f.cancellation_policy} onChange={set("cancellation_policy")}>
            <option value="free">Bepul (kirishdan 24 soat oldingacha)</option>
            <option value="partial">Qisman (48 soatdan oldin — 50%)</option>
            <option value="non_refundable">Qaytarilmaydi</option>
          </select>
        </label>
      </fieldset>

      {error && <p className="rounded-xl bg-clay-50 px-3 py-2 text-sm text-clay-700">{error}</p>}
      <button className="btn-primary w-full py-3.5 text-base" disabled={busy || !ready}>
        {busy ? "Yuborilmoqda…" : "Ariza yuborish"}
      </button>
    </form>
  );
}
