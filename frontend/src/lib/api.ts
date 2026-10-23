// Backend API mijozi. Ballar va to‘g‘ri javoblar bu yerga hech qachon kelmaydi.

const API = "/api/v1";

export interface TestMeta {
  question_count: number;
  duration_minutes: number;
  options_per_question: number;
  max_score: number;
  languages: string[];
  telegram_bot?: string;
  auth_required?: boolean;
}

export interface AuthUser {
  telegram_id: number;
  first_name: string;
  last_name: string;
  full_name: string;
  username: string;
  photo_url: string;
  language_code: string;
  /** Sertifikatdagi ism (birinchi testda kiritiladi) */
  real_name: string;
  name_locked: boolean;
}

export interface MyAttempt {
  attempt_id: string;
  token: string;
  status: AttemptStatus;
  full_name: string;
  started_at: string;
  finished_at: string | null;
  total_score: number | null;
  percent: number | null;
  level: { name_uz: string; name_ru: string } | null;
}

// Telegram sessiya tokeni (lib/auth.tsx o‘rnatadi) – har bir so‘rovga qo‘shiladi
let authToken: string | null = null;
export function setAuthToken(token: string | null) {
  authToken = token;
}

export interface PublicOption {
  letter: string;
  value: number | null;
  image: string | null;
}

export interface PublicQuestion {
  number: number;
  type: "number" | "image";
  prompt: { uz: string; ru: string };
  figure: string;
  options: PublicOption[];
}

export type AttemptStatus = "in_progress" | "finished" | "expired";

export interface AttemptQuestions {
  attempt_id: string;
  status: AttemptStatus;
  full_name: string;
  language: string;
  started_at: string;
  expires_at: string;
  server_time: string;
  questions: PublicQuestion[];
  answers: Record<string, string>;
}

export interface CategoryResult {
  key: "numeric" | "pattern" | "spatial";
  name_uz: string;
  name_ru: string;
  score: number;
  max: number;
  percent: number;
}

export interface AttemptResult {
  attempt_id: string;
  status: AttemptStatus;
  full_name: string;
  language: string;
  started_at: string;
  finished_at: string | null;
  duration_seconds: number;
  total_score: number;
  max_score: number;
  percent: number;
  level: {
    name_uz: string;
    name_ru: string;
    description_uz: string;
    description_ru: string;
    min_score: number;
    max_score: number;
  } | null;
  categories: CategoryResult[];
  answered_count: number;
  total_questions: number;
}

export class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    public data: Record<string, unknown> = {},
  ) {
    super(code);
  }
  get isNetwork() {
    return this.status === 0;
  }
}

async function request<T>(path: string, init: RequestInit & { token?: string } = {}): Promise<T> {
  const headers: Record<string, string> = { Accept: "application/json" };
  if (init.body) headers["Content-Type"] = "application/json";
  if (init.token) headers["X-Attempt-Token"] = init.token;
  if (authToken) headers.Authorization = `Bearer ${authToken}`;
  let res: Response;
  try {
    res = await fetch(`${API}${path}`, { ...init, headers: { ...headers, ...(init.headers as object) }, cache: "no-store" });
  } catch {
    throw new ApiError(0, "network");
  }
  let data: Record<string, unknown> = {};
  try {
    data = await res.json();
  } catch {
    /* bo‘sh javob */
  }
  if (!res.ok) {
    const code = (data.error as string) || (data.detail as string) || `http_${res.status}`;
    throw new ApiError(res.status, code, data);
  }
  return data as T;
}

export const authApi = {
  widget: (data: Record<string, unknown>) =>
    request<{ token: string; user: AuthUser }>("/auth/telegram/widget", { method: "POST", body: JSON.stringify(data) }),
  webapp: (initData: string) =>
    request<{ token: string; user: AuthUser }>("/auth/telegram/webapp", {
      method: "POST",
      body: JSON.stringify({ init_data: initData }),
    }),
  me: () => request<{ user: AuthUser }>("/auth/me"),
  myAttempts: () => request<{ max_score: number; attempts: MyAttempt[] }>("/me/attempts"),
};

export const api = {
  meta: () => request<TestMeta>("/test/meta"),
  createAttempt: (body: { full_name: string; phone: string; language: string; telegram_init_data?: string }) =>
    request<{ attempt_id: string; token: string; expires_at: string; server_time: string }>("/attempts", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  questions: (id: string, token: string) => request<AttemptQuestions>(`/attempts/${id}/questions`, { token }),
  answer: (id: string, token: string, number: number, letter: string | null) =>
    request<{ number: number; letter: string | null; answered_count: number }>(`/attempts/${id}/answers/${number}`, {
      method: "PUT",
      token,
      body: JSON.stringify({ letter }),
    }),
  finish: (id: string, token: string) => request<AttemptResult>(`/attempts/${id}/finish`, { method: "POST", token }),
  result: (id: string, token: string) => request<AttemptResult>(`/attempts/${id}/result`, { token }),
  certificateUrl: (id: string, token: string, lang: string) =>
    `${API}/attempts/${id}/certificate.pdf?token=${encodeURIComponent(token)}&lang=${lang}`,
  telegramAuth: (initData: string) =>
    request<{ ok: boolean; user: { id: number; full_name: string; language_code: string } }>("/telegram/auth", {
      method: "POST",
      body: JSON.stringify({ init_data: initData }),
    }),
};
