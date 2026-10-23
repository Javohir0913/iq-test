import { expect, test, type Response } from "@playwright/test";
import { loginPage, loginToken } from "./auth";

// Test davomida tarmoq javoblarida ball yoki to‘g‘ri javob bo‘lmasligi kerak
const FORBIDDEN = /"(points|correct|is_correct|reason_uz|reason_ru|logic_uz|logic_ru)"\s*:/;

test("kirishsiz /start Telegram login kartasini ko‘rsatadi", async ({ page }) => {
  await page.goto("/start");
  await expect(page.getByRole("heading", { name: "Telegram orqali kiring" })).toBeVisible();
  await expect(page.locator("#full_name")).toHaveCount(0);
  const meta = await (await page.request.get("/api/v1/test/meta")).json();
  expect(meta.auth_required).toBe(true);
  const res = await page.request.post("/api/v1/attempts", { data: { full_name: "Mehmon" } });
  expect(res.status()).toBe(401);
});

test("asosiy oqim: boshlash → 35 savol → natija", async ({ page, request }, testInfo) => {
  await loginPage(page, request);
  const isMobile = testInfo.project.name === "mobile";
  const leaks: string[] = [];
  let testPhase = true;
  page.on("response", async (res: Response) => {
    if (!testPhase || !res.url().includes("/api/v1/")) return;
    try {
      const body = await res.text();
      if (FORBIDDEN.test(body)) leaks.push(res.url());
    } catch {
      /* binary yoki bekor qilingan */
    }
  });

  await page.goto("/");
  await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
  await page.getByRole("link", { name: /Testni boshlash/ }).first().click();

  await expect(page).toHaveURL(/\/start$/);
  // Ism Telegram akkauntidan to‘ldirilgan
  await expect(page.getByLabel("Ism familiya")).toHaveValue("E2E Sinov");
  // Bo‘sh ism bilan yuborish – xato ko‘rsatiladi
  await page.getByLabel("Ism familiya").fill("");
  await page.getByRole("button", { name: /Testni boshlash/ }).click();
  await expect(page.getByText("Ism familiyani kiriting")).toBeVisible();

  await page.getByLabel("Ism familiya").fill("Playwright Sinov");
  await page.getByLabel(/Telefon/).fill("901234567");
  await expect(page.getByLabel(/Telefon/)).toHaveValue("+998 (90) 123-45-67");
  await page.getByRole("button", { name: /Testni boshlash/ }).click();

  await expect(page).toHaveURL(/\/test\/[0-9a-f-]{36}$/);
  await expect(page.getByText("1 / 35", { exact: false }).first()).toBeVisible();

  for (let i = 1; i <= 35; i++) {
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
    const options = page.getByRole("radio");
    await expect(options).toHaveCount(6);
    const target = options.nth(i % 6);
    await target.click();
    await expect(target).toHaveAttribute("aria-checked", "true");

    if (i === 10) {
      // Sahifa yangilansa test shu joydan davom etadi va javob saqlanib qoladi
      await page.waitForTimeout(600);
      await page.reload();
      await expect(page.getByRole("radio").nth(i % 6)).toHaveAttribute("aria-checked", "true");
    }

    if (i < 35) {
      if (isMobile) await page.getByRole("button", { name: /Keyingi/ }).click();
      else await page.keyboard.press("ArrowRight");
    }
  }

  await expect(page.getByText(/Saqlandi/).first()).toBeVisible({ timeout: 15_000 }).catch(() => {});
  await page.getByRole("button", { name: /Testni yakunlash/ }).first().click();
  const dialog = page.getByRole("dialog");
  await expect(dialog).toBeVisible();
  await expect(dialog).toContainText("Barcha savollarga javob berdingiz");
  testPhase = false;
  await dialog.getByRole("button", { name: /Ha, yakunlash/ }).click();

  await expect(page).toHaveURL(/\/result\//, { timeout: 30_000 });
  await expect(page.getByText(/\/ 245/).first()).toBeVisible();
  await expect(page.getByText(/Yo‘nalishlar bo‘yicha tahlil/)).toBeVisible();
  await expect(page.getByRole("link", { name: /Sertifikat/ })).toHaveAttribute("href", /certificate\.pdf/);
  // IQ raqami ko‘rsatilmaydi
  await expect(page.locator("body")).not.toContainText(/IQ\s*=\s*\d+/);

  // Til almashtirish
  await page.getByRole("button", { name: "ru", exact: true }).click();
  await expect(page.getByText("Анализ по направлениям")).toBeVisible();

  // Natija Telegram akkauntiga bog‘langan: "Mening natijalarim" da ko‘rinadi
  const attemptId = page.url().split("/result/")[1];
  await page.goto("/me");
  await expect(page.locator(`a[href="/result/${attemptId}"]`)).toBeVisible();

  // Ism birinchi testdan keyin qulflangan: keyingi safar o‘zgartirib bo‘lmaydi
  await page.goto("/start");
  const nameInput = page.locator("#full_name");
  await expect(nameInput).toHaveValue("Playwright Sinov");
  await expect(nameInput).toHaveAttribute("readonly", "");

  expect(leaks, `ball/to‘g‘ri javob sizdi: ${leaks.join(", ")}`).toEqual([]);
});

test("boshqa qurilmadan: natija Telegram akkaunti orqali ochiladi", async ({ browser, request }) => {
  const token = await loginToken(request, undefined, "Ikki", "Qurilma");
  const auth = { Authorization: `Bearer ${token}` };
  const created = await (await request.post("/api/v1/attempts", { data: { full_name: "Ikki Qurilma" }, headers: auth })).json();
  await request.post(`/api/v1/attempts/${created.attempt_id}/finish`, { headers: { "X-Attempt-Token": created.token } });
  // Yangi kontekst = boshqa qurilma: attempt tokeni yo‘q, faqat Telegram sessiyasi
  const ctx = await browser.newContext();
  await ctx.addInitScript((t) => window.localStorage.setItem("iq.auth", t), token);
  const page = await ctx.newPage();
  await page.goto(`/result/${created.attempt_id}`);
  await expect(page.getByText(/Ikki Qurilma/)).toBeVisible();
  await ctx.close();
});

test("sertifikat PDF yuklanadi", async ({ request }) => {
  const token = await loginToken(request);
  const created = await (
    await request.post("/api/v1/attempts", { data: { full_name: "PDF Sinov" }, headers: { Authorization: `Bearer ${token}` } })
  ).json();
  const headers = { "X-Attempt-Token": created.token };
  await request.put(`/api/v1/attempts/${created.attempt_id}/answers/1`, { data: { letter: "A" }, headers });
  await request.post(`/api/v1/attempts/${created.attempt_id}/finish`, { headers });
  const pdf = await request.get(`/api/v1/attempts/${created.attempt_id}/certificate.pdf?token=${created.token}`);
  expect(pdf.status()).toBe(200);
  expect(pdf.headers()["content-type"]).toContain("application/pdf");
});

test("qorong‘i rejim almashtirgich ishlaydi", async ({ page }) => {
  await page.goto("/");
  const html = page.locator("html");
  const toggle = page.getByRole("button", { name: /Mavzu|Тема/ });
  // system → light → dark
  for (let i = 0; i < 3; i++) {
    if (await html.evaluate((el) => el.classList.contains("dark"))) break;
    await toggle.click();
  }
  await expect(html).toHaveClass(/dark/);
});

test("bosh sahifada til almashtirish (server render)", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { level: 1 })).toContainText("Mantiqiy");
  await page.getByRole("button", { name: "ru", exact: true }).click();
  await expect(page.getByRole("heading", { level: 1 })).toContainText("логическое");
  await page.reload();
  await expect(page.getByRole("heading", { level: 1 })).toContainText("логическое");
  await page.getByRole("button", { name: "uz", exact: true }).click();
  await expect(page.getByRole("heading", { level: 1 })).toContainText("Mantiqiy");
});

test("sertifikat QR tekshiruvi: haqiqiy va soxta kod", async ({ page, request }) => {
  const token = await loginToken(request, undefined, "Tekshiruv", "Sinov");
  const auth = { Authorization: `Bearer ${token}` };
  const created = await (await request.post("/api/v1/attempts", { data: { full_name: "Tekshiruv Sinov" }, headers: auth })).json();
  const result = await (
    await request.post(`/api/v1/attempts/${created.attempt_id}/finish`, { headers: { "X-Attempt-Token": created.token } })
  ).json();
  expect(result.verify_code).toMatch(/^[0-9A-Z]{4}-[0-9A-Z]{4}-[0-9A-Z]{2}$/);

  await page.goto(`/verify/${result.verify_code.replace(/-/g, "")}`);
  await expect(page.getByRole("heading", { name: "Sertifikat haqiqiy" })).toBeVisible();
  await expect(page.getByText("Tekshiruv Sinov")).toBeVisible();
  await expect(page.getByText(result.verify_code)).toBeVisible();

  await page.goto("/verify/ZZZZZZZZZZ");
  await expect(page.getByRole("heading", { name: "Sertifikat topilmadi" })).toBeVisible();
  // Qo‘lda kiritish formasi
  await page.locator("#verify-code").fill(result.verify_code);
  await page.getByRole("button", { name: "Tekshirish" }).click();
  await expect(page.getByRole("heading", { name: "Sertifikat haqiqiy" })).toBeVisible();
});
