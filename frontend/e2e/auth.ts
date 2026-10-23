// E2E uchun Telegram Login: haqiqiy widget localhost'da ishlamaydi, shuning uchun ma’lumot
// bot tokeni bilan imzolanadi (backenddagi tekshiruv bilan bir xil algoritm).
import { createHash, createHmac } from "node:crypto";
import fs from "node:fs";
import path from "node:path";
import type { APIRequestContext, Page } from "@playwright/test";

export function botToken(): string {
  if (process.env.TELEGRAM_BOT_TOKEN) return process.env.TELEGRAM_BOT_TOKEN;
  try {
    const env = fs.readFileSync(path.resolve(__dirname, "../../.env"), "utf8");
    return /^TELEGRAM_BOT_TOKEN=(.*)$/m.exec(env)?.[1].trim() ?? "";
  } catch {
    return "";
  }
}

export function signWidget(user: Record<string, string | number>, token = botToken()) {
  const fields = Object.fromEntries(Object.entries(user).map(([k, v]) => [k, String(v)]));
  const check = Object.keys(fields)
    .sort()
    .map((k) => `${k}=${fields[k]}`)
    .join("\n");
  const secret = createHash("sha256").update(token).digest();
  return { ...fields, hash: createHmac("sha256", secret).update(check).digest("hex") };
}

export async function loginToken(request: APIRequestContext, id = 700000001, firstName = "E2E", lastName = "Sinov") {
  const data = signWidget({ id, first_name: firstName, last_name: lastName, auth_date: Math.floor(Date.now() / 1000) });
  const res = await request.post("/api/v1/auth/telegram/widget", { data });
  if (!res.ok()) throw new Error(`login ${res.status()}`);
  return (await res.json()).token as string;
}

export async function loginPage(page: Page, request: APIRequestContext, id?: number) {
  const token = await loginToken(request, id);
  await page.addInitScript((t) => window.localStorage.setItem("iq.auth", t), token);
  return token;
}
