import type { TestMeta } from "./api";

const FALLBACK: TestMeta = {
  question_count: 35,
  duration_minutes: 40,
  options_per_question: 6,
  max_score: 245,
  languages: ["uz", "ru"],
};

// Server tomonida backenddan test ma’lumotini olish (xato bo‘lsa standart qiymatlar)
export async function getServerMeta(): Promise<TestMeta> {
  const base = process.env.BACKEND_INTERNAL_URL || "http://backend:8000";
  try {
    const res = await fetch(`${base}/api/v1/test/meta`, {
      cache: "no-store",
      signal: AbortSignal.timeout(1500),
      headers: { Accept: "application/json" },
    });
    if (!res.ok) return FALLBACK;
    return (await res.json()) as TestMeta;
  } catch {
    return FALLBACK;
  }
}
