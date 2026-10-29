"use client";

import { useEffect, useState } from "react";
import { api, type TestMeta } from "./api";

// Server javobi kelguncha TZ dagi standart qiymatlar ko‘rsatiladi
const FALLBACK: TestMeta = {
  question_count: 20,
  duration_minutes: 25,
  options_per_question: 6,
  max_score: 140,
  languages: ["uz", "ru", "en"],
};

let cache: TestMeta | null = null;

export function useMeta() {
  const [meta, setMeta] = useState<TestMeta>(cache ?? FALLBACK);
  useEffect(() => {
    if (cache) return;
    let alive = true;
    api
      .meta()
      .then((m) => {
        cache = m;
        if (alive) setMeta(m);
      })
      .catch(() => {});
    return () => {
      alive = false;
    };
  }, []);
  return meta;
}
