/** Brauzer ko'radigan backend manzili. */
export const API_PUBLIC = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/\/$/, "");
/** Next server (SSR, route handler'lar) ishlatadigan ichki manzil. */
export const API_INTERNAL = (process.env.API_INTERNAL_URL || API_PUBLIC).replace(/\/$/, "");

export const ACCESS_COOKIE = "lz_access";
export const REFRESH_COOKIE = "lz_refresh";
