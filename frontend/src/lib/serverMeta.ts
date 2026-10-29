import type { TestMeta } from "./api";

const FALLBACK: TestMeta = {
  question_count: 20,
  duration_minutes: 25,
  options_per_question: 6,
  max_score: 140,
  languages: ["uz", "ru", "en"],
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
