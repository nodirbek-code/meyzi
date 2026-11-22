/**
 * Yuklash qoidalari (backend `apps/core/files.py` bilan bir xil). Hamma joyda:
 * rasm — jpg/png/webp, 6 MB gacha; video — mp4/mov/webm, 20 MB gacha; hujjat — pdf/jpg/png, 6 MB gacha.
 * Tur va mehmonxona galereyasi: ko'pi bilan 20 ta rasm va 4 ta video.
 * Brauzerdagi tekshiruv — faqat qulaylik uchun; haqiqiy format (fayl ichi) serverda tekshiriladi.
 */

export const IMAGE_MAX_MB = 6;
export const VIDEO_MAX_MB = 20;
export const MAX_IMAGES = 20;
export const MAX_VIDEOS = 4;

const MB = 1024 * 1024;
const IMAGE_EXTS = ["jpg", "jpeg", "png", "webp"];
const VIDEO_EXTS = ["mp4", "mov", "webm"];
const DOC_EXTS = ["pdf", "jpg", "jpeg", "png"];

export const IMAGE_ACCEPT = ".jpg,.jpeg,.png,.webp,image/jpeg,image/png,image/webp";
export const MEDIA_ACCEPT = `${IMAGE_ACCEPT},.mp4,.mov,.webm,video/mp4,video/quicktime,video/webm`;
export const DOC_ACCEPT = ".pdf,.jpg,.jpeg,.png,application/pdf,image/jpeg,image/png";

export const MEDIA_HINT = `Rasm — jpg/png/webp, ${IMAGE_MAX_MB} MB gacha (ko'pi bilan ${MAX_IMAGES} ta). Video — mp4/mov/webm, ${VIDEO_MAX_MB} MB gacha (ko'pi bilan ${MAX_VIDEOS} ta).`;

const ext = (name: string) => (name.includes(".") ? name.split(".").pop()!.toLowerCase() : "");

export type MediaKind = "image" | "video";

export function mediaKind(file: File): MediaKind | null {
  const e = ext(file.name);
  return IMAGE_EXTS.includes(e) ? "image" : VIDEO_EXTS.includes(e) ? "video" : null;
}

/** Bitta fayl: xato matni yoki null. `kind`: "image" | "video" | "media" (rasm yoki video) | "document". */
export function fileError(file: File, kind: MediaKind | "media" | "document"): string | null {
  const e = ext(file.name);
  const name = `«${file.name}»`;
  if (kind === "document") {
    if (!DOC_EXTS.includes(e)) return `${name}: faqat pdf, jpg yoki png fayl.`;
    if (file.size > IMAGE_MAX_MB * MB) return `${name}: hajmi ${IMAGE_MAX_MB} MB dan oshmasin.`;
    return null;
  }
  const k = mediaKind(file);
  if (!k || (kind !== "media" && k !== kind)) {
    return kind === "image" ? `${name}: faqat jpg, png yoki webp rasm.` : `${name}: faqat rasm (jpg/png/webp) yoki video (mp4/mov/webm).`;
  }
  const max = k === "video" ? VIDEO_MAX_MB : IMAGE_MAX_MB;
  if (file.size > max * MB) return `${name}: ${k === "video" ? "video" : "rasm"} hajmi ${max} MB dan oshmasin.`;
  return null;
}

/** Galereyaga qo'shiladigan fayllar: format, hajm va 20 rasm / 4 video chegarasi. Xato bo'lsa — matn. */
export function galleryError(files: File[], existing: { kind: string }[]): string | null {
  let images = existing.filter((m) => m.kind !== "video").length;
  let videos = existing.filter((m) => m.kind === "video").length;
  for (const f of files) {
    const err = fileError(f, "media");
    if (err) return err;
    if (mediaKind(f) === "video") videos += 1;
    else images += 1;
  }
  if (images > MAX_IMAGES) return `Ko'pi bilan ${MAX_IMAGES} ta rasm yuklash mumkin (hozir ${existing.filter((m) => m.kind !== "video").length} ta bor).`;
  if (videos > MAX_VIDEOS) return `Ko'pi bilan ${MAX_VIDEOS} ta video yuklash mumkin (hozir ${existing.filter((m) => m.kind === "video").length} ta bor).`;
  return null;
}
