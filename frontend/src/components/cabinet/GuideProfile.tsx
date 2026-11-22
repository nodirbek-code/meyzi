"use client";

import { useEffect, useState } from "react";

import { Checks, FilePick, Req } from "@/components/PartnerForms";
import { phoneReady, VerifiedPhoneField, type VerifiedPhone } from "@/components/PhoneField";
import { firstError } from "@/lib/client";
import { LANGUAGE_NAMES, SPECIALIZATIONS } from "@/lib/format";
import type { DestinationShort, Paginated } from "@/lib/types";
import { DOC_ACCEPT, IMAGE_ACCEPT, IMAGE_MAX_MB } from "@/lib/uploads";

import { ErrorText, Loading, ModerationBanner, Panel } from "./Bits";
import { useData } from "./useData";

type Profile = {
  display_name: string;
  photo: string | null;
  bio: string;
  phone: string;
  languages: string[];
  specializations: string[];
  destinations: string[];
  experience_years: number;
  certificate_number: string;
  has_certificate_file: boolean;
  price_half_day_uzs: number;
  price_full_day_uzs: number;
  price_per_day_uzs: number;
  status: string;
  moderation_note: string;
};

const digits = (s: string) => s.replace(/\D/g, "");

/** Gid o'z profilini tahrirlaydi (tillar, shaharlar, narxlar, rasm, sertifikat). Saqlansa — qayta tekshiruvga. */
export function GuideProfileEdit() {
  const profile = useData<Profile>("/guides/me");
  const dests = useData<Paginated<DestinationShort>>("/catalog/destinations?page_size=50");
  const [f, setF] = useState<Profile | null>(null);
  const [phone, setPhone] = useState<VerifiedPhone | null>(null);
  const [photo, setPhoto] = useState<File | null>(null);
  const [cert, setCert] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (profile.data && !f) setF(profile.data);
  }, [profile.data, f]);

  if (!f || !profile.data) return profile.error ? <ErrorText text={profile.error} /> : <Loading />;
  const p = profile.data;
  const ph = phone ?? { phone: p.phone, token: "" };
  const set = <K extends keyof Profile>(k: K, v: Profile[K]) => setF({ ...f, [k]: v });
  const ready = f.display_name.trim() && f.languages.length && f.destinations.length && phoneReady(ph, p.phone);

  async function save(e: React.FormEvent) {
    e.preventDefault();
    if (!f) return;
    setBusy(true);
    setError("");
    setSaved(false);
    const fd = new FormData();
    const fields: Record<string, string | number> = {
      display_name: f.display_name,
      bio: f.bio,
      experience_years: f.experience_years,
      certificate_number: f.certificate_number,
      price_half_day_uzs: f.price_half_day_uzs,
      price_full_day_uzs: f.price_full_day_uzs,
      price_per_day_uzs: f.price_per_day_uzs,
    };
    Object.entries(fields).forEach(([k, v]) => fd.append(k, String(v ?? "")));
    f.languages.forEach((x) => fd.append("languages", x));
    f.specializations.forEach((x) => fd.append("specializations", x));
    f.destinations.forEach((x) => fd.append("destinations", x));
    if (ph.phone !== p.phone) {
      fd.append("phone", ph.phone);
      fd.append("phone_token", ph.token);
    }
    if (photo) fd.append("photo", photo);
    if (cert) fd.append("certificate_file", cert);
    try {
      const res = await fetch("/api/proxy/guides/me", { method: "PATCH", body: fd });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(firstError(data) || "Saqlab bo'lmadi");
      setSaved(true);
      setPhoto(null);
      setCert(null);
      setF(null);
      profile.reload();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  const destOptions = Object.fromEntries((dests.data?.results ?? []).map((d) => [d.slug, d.name]));
  return (
    <form onSubmit={save} className="space-y-6">
      <ModerationBanner state={p.status} note={p.moderation_note} what="Gid profili" />
      {saved && <p className="rounded-xl bg-forest-50 px-4 py-3 text-sm text-forest-700">✅ Saqlandi va tekshiruvga yuborildi. Admin tasdiqlagach saytda yangilanadi.</p>}

      <Panel title="Asosiy ma'lumotlar">
        <div className="space-y-4">
          <div className="flex items-start gap-4">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            {p.photo && !photo && <img src={p.photo} alt="" className="h-16 w-16 shrink-0 rounded-full object-cover" />}
            <div className="flex-1">
              <FilePick
                label="Rasmni almashtirish"
                accept={IMAGE_ACCEPT}
                kind="image"
                hint={`jpg, png yoki webp — ${IMAGE_MAX_MB} MB gacha.`}
                file={photo}
                onChange={setPhoto}
                preview
                optional
              />
            </div>
          </div>
          <label className="block">
            <span className="label">Ism familiya<Req /></span>
            <input className="input" required value={f.display_name} onChange={(e) => set("display_name", e.target.value)} />
          </label>
          <VerifiedPhoneField value={ph} onChange={setPhone} trustedPhone={p.phone} />
          <label className="block">
            <span className="label">O&apos;zingiz haqingizda</span>
            <textarea className="input min-h-24" value={f.bio} onChange={(e) => set("bio", e.target.value)} />
          </label>
        </div>
      </Panel>

      <Panel title="Ish hududi va tillar">
        <div className="space-y-4">
          <div>
            <span className="label">Shaharlar<Req /></span>
            {dests.data ? <Checks options={destOptions} value={f.destinations} onChange={(v) => set("destinations", v)} /> : <Loading />}
          </div>
          <div>
            <span className="label">Tillar<Req /></span>
            <Checks options={LANGUAGE_NAMES} value={f.languages} onChange={(v) => set("languages", v)} />
          </div>
          <div>
            <span className="label">Yo&apos;nalishlar</span>
            <Checks options={SPECIALIZATIONS} value={f.specializations} onChange={(v) => set("specializations", v)} />
          </div>
        </div>
      </Panel>

      <Panel title="Narxlar (so'm)">
        <div className="grid gap-4 sm:grid-cols-3">
          {(
            [
              ["price_half_day_uzs", "Yarim kun (4 soat)"],
              ["price_full_day_uzs", "To'liq kun (8 soat)"],
              ["price_per_day_uzs", "Ko'p kunlik (1 kun)"],
            ] as const
          ).map(([k, label]) => (
            <label key={k}>
              <span className="label">{label}<Req /></span>
              <input className="input" required inputMode="numeric" value={f[k] || ""} onChange={(e) => set(k, Number(digits(e.target.value)) || 0)} />
            </label>
          ))}
        </div>
      </Panel>

      <Panel title="Tajriba va sertifikat">
        <div className="grid gap-4 sm:grid-cols-2">
          <label>
            <span className="label">Tajriba (yil)</span>
            <input className="input" type="number" min={0} value={f.experience_years} onChange={(e) => set("experience_years", Number(e.target.value) || 0)} />
          </label>
          <label>
            <span className="label">Sertifikat raqami</span>
            <input className="input" value={f.certificate_number} onChange={(e) => set("certificate_number", e.target.value)} />
          </label>
        </div>
        <div className="mt-4">
          <FilePick
            label={p.has_certificate_file ? "Sertifikatni almashtirish (yuklangan ✓)" : "Gid sertifikati"}
            accept={DOC_ACCEPT}
            kind="document"
            hint={`pdf, jpg yoki png — ${IMAGE_MAX_MB} MB gacha. Faqat tekshiruvchilarga ko'rinadi.`}
            file={cert}
            onChange={setCert}
            optional
          />
        </div>
      </Panel>

      {error && <p className="rounded-xl bg-clay-50 px-3 py-2 text-sm text-clay-700">{error}</p>}
      <div className="flex flex-wrap items-center gap-3">
        <button className="btn-primary" disabled={busy || !ready}>{busy ? "Saqlanmoqda…" : "Saqlash va tekshiruvga yuborish"}</button>
        <span className="text-xs text-ink-mute">Saqlangach profil admin tasdiqlaguncha saytda ko&apos;rinmaydi.</span>
      </div>
    </form>
  );
}
