/** Server va brauzer uchun umumiy telefon yordamchilari (komponent emas). */

/** Akkauntdagi tasdiqlangan raqam (bo'lmasa null) — bunday raqamga formalarda kod so'ralmaydi */
export function accountPhone(user: { phone: string | null; phone_verified: boolean } | null) {
  return user?.phone && user.phone_verified ? user.phone : null;
}
