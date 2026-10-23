// Dizayn tekshiruvi uchun skrinshotlar: node e2e/screenshots.mjs [chiqish papkasi]
// BASE_URL (standart http://localhost) da ishlayotgan stack kerak.
import { chromium } from "@playwright/test";
import fs from "node:fs";
import path from "node:path";
import { createHash, createHmac } from "node:crypto";

// Telegram Login (imzolangan widget ma’lumoti) – bot tokeni ../.env dan
const BOT = /^TELEGRAM_BOT_TOKEN=(.*)$/m.exec(fs.readFileSync(new URL("../../.env", import.meta.url), "utf8"))?.[1].trim() ?? "";
async function login() {
  const f = { id: "700000009", first_name: "Aziza", last_name: "Karimova", auth_date: String(Math.floor(Date.now() / 1000)) };
  const check = Object.keys(f).sort().map((k) => `${k}=${f[k]}`).join(String.fromCharCode(10));
  const hash = createHmac("sha256", createHash("sha256").update(BOT).digest()).update(check).digest("hex");
  const res = await fetch(`${BASE}/api/v1/auth/telegram/widget`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ ...f, hash }) });
  return (await res.json()).token;
}
const AUTH = BOT ? await login() : "";

const BASE = process.env.BASE_URL || "http://localhost";
const OUT = process.argv[2] || "screenshots";
fs.mkdirSync(OUT, { recursive: true });

const VIEWPORTS = {
  desktop: { width: 1440, height: 900 },
  mobile: { width: 360, height: 780 },
};

async function createAttempt(lang) {
  const res = await fetch(`${BASE}/api/v1/attempts`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...(AUTH ? { Authorization: `Bearer ${AUTH}` } : {}) },
    body: JSON.stringify({ full_name: lang === "ru" ? "Азиза Каримова" : "Aziza Karimova", language: lang }),
  });
  if (!res.ok) throw new Error(`attempt ${res.status}`);
  return res.json();
}

async function answerAll(id, token, count, letters = "ABCDEF") {
  const qs = await (await fetch(`${BASE}/api/v1/attempts/${id}/questions`, { headers: { "X-Attempt-Token": token } })).json();
  for (const [i, q] of qs.questions.slice(0, count).entries()) {
    await fetch(`${BASE}/api/v1/attempts/${id}/answers/${q.number}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json", "X-Attempt-Token": token },
      body: JSON.stringify({ letter: letters[(i * 7 + 2) % letters.length] }),
    });
  }
}

const browser = await chromium.launch();
const only = process.env.ONLY;

for (const [vpName, viewport] of Object.entries(VIEWPORTS)) {
  for (const scheme of ["light", "dark"]) {
    for (const lang of ["uz", "ru"]) {
      if (lang === "ru" && scheme === "dark") continue;
      const tag = `${vpName}-${scheme}-${lang}`;
      if (only && !tag.includes(only)) continue;
      const ctx = await browser.newContext({ viewport, colorScheme: scheme, deviceScaleFactor: vpName === "mobile" ? 2 : 1 });
      await ctx.addCookies([{ name: "lang", value: lang, url: BASE }]);
      if (AUTH) await ctx.addInitScript((t) => window.localStorage.setItem("iq.auth", t), AUTH);
      const page = await ctx.newPage();
      const shot = async (name, full = false) => {
        if (full) {
          // whileInView animatsiyalari ishga tushishi uchun sahifani aylantirib chiqamiz
          await page.evaluate(async () => {
            for (let y = 0; y < document.body.scrollHeight; y += 400) {
              window.scrollTo(0, y);
              await new Promise((r) => setTimeout(r, 120));
            }
            window.scrollTo(0, 0);
          });
        }
        await page.waitForTimeout(1600);
        await page.screenshot({ path: path.join(OUT, `${tag}-${name}.png`), fullPage: full });
      };

      await page.goto(`${BASE}/`);
      await shot("home", true);
      await page.goto(`${BASE}/start`);
      await shot("start");

      const a = await createAttempt(lang);
      await page.evaluate(({ id, token }) => {
        localStorage.setItem("iq.attempts", JSON.stringify({ [id]: { id, token, createdAt: Date.now() } }));
        localStorage.setItem("iq.current", JSON.stringify(id));
      }, { id: a.attempt_id, token: a.token });
      await page.goto(`${BASE}/test/${a.attempt_id}`);
      await shot("test-q1");
      await page.keyboard.press("3");
      await shot("test-q1-selected");
      await page.keyboard.press("ArrowRight");
      await page.keyboard.press("ArrowRight");
      await page.keyboard.press("e");
      await shot("test-q3-image");
      if (vpName === "mobile") {
        await page.getByRole("button", { name: /xarita|карт/i }).click();
        await shot("test-map");
        await page.keyboard.press("Escape");
      }
      await page.evaluate(() => window.scrollTo(0, 0));
      await page.getByRole("button", { name: /yakunlash|завершить/i }).first().click();
      await shot("test-finish-modal");
      await page.keyboard.press("Escape");

      const b = await createAttempt(lang);
      await answerAll(b.attempt_id, b.token, 33);
      await fetch(`${BASE}/api/v1/attempts/${b.attempt_id}/finish`, { method: "POST", headers: { "X-Attempt-Token": b.token } });
      await page.evaluate(({ id, token }) => {
        localStorage.setItem("iq.attempts", JSON.stringify({ [id]: { id, token, createdAt: Date.now() } }));
      }, { id: b.attempt_id, token: b.token });
      await page.goto(`${BASE}/result/${b.attempt_id}`);
      await page.waitForTimeout(1500);
      await shot("result", true);
      await page.getByRole("button", { name: /ulashish|поделиться/i }).first().click();
      await shot("share");
      await ctx.close();
    }
  }
}

await browser.close();
console.log("done", OUT);
