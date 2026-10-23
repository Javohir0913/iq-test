// Server komponentlari uchun backend so‘rovlari (ichki tarmoq orqali)
import { cookies } from "next/headers";
import { LANG_COOKIE, type Lang } from "@/i18n/core";

const BASE = process.env.BACKEND_INTERNAL_URL || "http://backend:8000";

export async function serverLang(): Promise<Lang> {
  return (await cookies()).get(LANG_COOKIE)?.value === "ru" ? "ru" : "uz";
}

export interface VerifyResult {
  valid: boolean;
  code: string;
  full_name: string;
  finished_at: string | null;
  total_score: number;
  max_score: number;
  percent: number;
  level: { name_uz: string; name_ru: string } | null;
  telegram_verified: boolean;
}

/** null – topilmadi; "error" – backend javob bermadi */
export async function verifyCertificate(code: string): Promise<VerifyResult | null | "error"> {
  try {
    const res = await fetch(`${BASE}/api/v1/verify/${encodeURIComponent(code)}`, {
      cache: "no-store",
      signal: AbortSignal.timeout(4000),
      headers: { Accept: "application/json" },
    });
    if (res.status === 404) return null;
    if (!res.ok) return "error";
    return (await res.json()) as VerifyResult;
  } catch {
    return "error";
  }
}
