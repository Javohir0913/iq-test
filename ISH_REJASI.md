# Ish rejasi va holati

Belgilar: `[x]` bajarildi · `[ ]` qilinmagan

## 0. Tayyorgarlik
- [x] TZ.md, CLAUDE.md, PROMPT.md o‘qildi; questions.json tahlil qilindi (35 savol: 7 number, 28 image; numeric 7 / pattern 17 / spatial 11; har savolda aniq bitta 7)
- [x] test_uz.pdf va qollanma.pdf ko‘rib chiqildi (dizayn namunasi)

## 1. Docker skeleti
- [x] db (postgres:16-alpine, volume, healthcheck)
- [x] backend (Gunicorn, entrypoint: migrate → import → superuser → collectstatic, healthcheck)
- [x] frontend (Next.js standalone, healthcheck)
- [x] nginx (80-port: `/` → frontend, `/api` `/admin` `/static` `/media` → backend, gzip, kesh)
- [x] docker-compose.override.yml (dev: runserver + next dev, hot reload) — tekshirildi
- [x] .env.example, .gitignore, .dockerignore

## 2. Backend modellari
- [x] Question, Option, Participant, Attempt (UUID + token), Answer, ScoreLevel, TestSettings
- [x] DB cheklovlari: points 3–7, (savol, harf) unique, harf A–F, savolda ko‘pi bilan bitta 7 (partial unique) + clean()/import/admin formada aniq bitta 7
- [x] ScoreLevel standart qiymatlari migratsiya orqali (uz/ru nom va tavsif)
- [x] `import_questions` (rasmlar bilan, idempotent, oldindan to‘liq validatsiya, `--if-empty`)
- [x] Django admin (unfold): inline variantlar, rasm ko‘rinishi, urinish tafsiloti

## 3. API + pytest
- [x] test/meta, attempts, questions, answers, finish, result, certificate.pdf, telegram/auth
- [x] Token himoyasi, muddat tekshiruvi (server), throttling, CORS, `/api/docs` (drf-spectacular)
- [x] 60 ta pytest: ballash (245/min/aralash/javobsiz), darajalar, muddat, ruxsatlar, import, ball sizmasligi, admin, eksport, Telegram

## 4. Frontend dizayn tizimi
- [x] Tokenlar (TZ 6-band) yorug‘/qorong‘i, Inter (lotin+kirill subset, 66 KB), Tailwind
- [x] Button, Card, OptionCard, ProgressBar, Timer, QuestionMap, Modal, Skeleton, StateView
- [x] i18n (uz.json, ru.json, ruscha ko‘plik shakllari), til va mavzu almashtirish

## 5. Sahifalar
- [x] Bosh sahifa (server render, CSS animatsiyali geometrik shakllar, 3×3 jumboq, "Qanday ishlaydi")
- [x] /start (ism, +998 niqobi, qoidalar, tugallanmagan testni davom ettirish)
- [x] /test/[id] (autosave + oflayn navbat, davom ettirish, server taymeri, klaviatura, xarita, yakunlash va vaqt tugashi oynalari)

## 6. Natija
- [x] /result/[id]: ball halqasi va sanab chiqish, foiz, daraja, kategoriya chiziqlari + radar diagramma
- [x] Sertifikat PDF (ReportLab, Inter, uz/ru)
- [x] Ulashish kartochkasi PNG (canvas) + Telegram / native share / havola / yuklab olish

## 7. Admin
- [x] Statistika dashboard (jami, o‘rtacha, darajalar, 14 kun, eng qiyin savollar, variantlar taqsimoti)
- [x] Eksport CSV / XLSX (hammasi filtr bo‘yicha yoki tanlanganlar)
- [x] Darajalar va test sozlamalari (vaqt) tahriri

## 8. Telegram bot va Mini App
- [x] WebApp ready/expand, mavzu ranglari, BackButton, haptic, ismni avtomatik to‘ldirish
- [x] initData server tekshiruvi (HMAC, muddat), telegram_id saqlanadi
- [x] Bot servisi (aiogram 3): /start, /test, /natija, /yordam, uz/ru, menyu tugmasi (Mini App), bot tavsifi
- [x] Natija bot chatiga avtomatik yuboriladi («Natijani ochish» tugmasi bilan)
- [x] Bot orqali natijani ochish / tugallanmagan testni davom ettirish (token `?t=` orqali, manzildan darhol o‘chiriladi)
- [x] HTTPS: Cloudflare quick tunnel (domen bo‘lmaganda), manzil avtomatik aniqlanadi
- [x] Mini App: Telegram tili, yopishdan oldin tasdiq, vertikal surishda yopilmaslik, sertifikat `downloadFile` orqali
- [x] @iq_uzrobot bilan jonli tekshiruv: bot ishga tushdi, menyu tugmasi Mini App ga ulangan; imzolangan initData bilan to‘liq oqim (tunnel orqali) o‘tdi
- [ ] Doimiy domen + HTTPS (prod): PUBLIC_URL=https://domen, tunnel o‘chiriladi
- [ ] Haqiqiy telefonda Telegram ichida qo‘lda sinov (siz tomondan)

## 9. Yakuniy
- [x] Testlar: backend pytest 65/65, bot pytest 4/4
- [x] Playwright E2E: 8/8 (desktop + mobil): boshlash → 35 savol → natija, yangilashdan keyin davom etish, tarmoqda ball yo‘qligi, PDF, til, qorong‘i rejim
- [x] Skrinshotlar bilan dizayn tekshiruvi (360px va 1440px, yorug‘/qorong‘i, uz/ru) va tuzatishlar
- [x] Lighthouse: bosh sahifa mobil 91/100/100, desktop 100/100/100; /start mobil 92/100/100, desktop 100/100/100
- [x] README.md

## 9.1 Telegram orqali kirish (web)
- [x] Veb: Telegram Login Widget → imzo serverda tekshiriladi → sessiya tokeni (Bearer, 30 kun)
- [x] Mini App: initData orqali avtomatik kirish
- [x] Test boshlash faqat kirgan foydalanuvchiga (`REQUIRE_TELEGRAM_AUTH`), natijalar Telegram akkauntiga bog‘langan
- [x] "Mening natijalarim" sahifasi, boshqa qurilmadan natija/testni ochish
- [x] Admin: Telegram foydalanuvchilar ro‘yxati
- [x] Testlar: backend 74, E2E 12
- [x] @BotFather → /setdomain → iq.coffee-nap.uz

## 9.1.1 Ism va sertifikat ishonchliligi
- [x] Ism birinchi testda kiritiladi va Telegram akkauntga qulflanadi; faqat admin o‘zgartiradi (eski natijalar ham yangilanadi)
- [x] Sertifikatda QR kod va tekshiruv kodi (K7M2-QX9P-4T): skaner → `/verify/KOD` – ma’lumot serverdan, PDF tahrirlansa soxtaligi bilinadi
- [x] `/verify` – kodni qo‘lda kiritish; tekshiruv kodi natijaga kirish huquqini bermaydi

## 9.2 Server (iq.coffee-nap.uz)
- [x] Deploy fayllari: `deploy/nginx-iq.coffee-nap.uz.conf`, `deploy/update.sh`, deploy kalit
- [x] GitHub (Javohir0913/iq-test) → serverda `~/iq-test` (deploy key `github.com-iq`)
- [x] Server `.env` (alohida maxfiy kalitlar), stack `127.0.0.1:5183` da, tunnel o‘chiq
- [x] Host nginx: `/etc/nginx/sites-available/iq.coffee-nap.uz`, Let's Encrypt SSL (certbot, avtomatik yangilanadi), http → https
- [x] https://iq.coffee-nap.uz ishlayapti; bot serverda, menyu tugmasi domenga ulangan; lokal bot to‘xtatilgan
- [x] Boshqa saytlar (hostel, profit, test) tekshirildi – ta’sir yo‘q

## 10. Mobil ilova (keyingi bosqich)
- [ ] **Android (APK / AAB)** — birinchi navbatda
  - **Kirish – Telegram orqali** (web bilan bir xil akkaunt va natijalar): ilova Telegram Login sahifasini tizim brauzerida ochadi → `https://iq.coffee-nap.uz/auth/app?…` → deep link (`iqtest://auth?token=…`) bilan ilovaga qaytadi; backend’dagi `/api/v1/auth/telegram/widget` va Bearer token o‘zgarishsiz ishlatiladi
  - Yondashuv: mavjud Next.js frontendni **Capacitor** bilan o‘rash (bitta kod bazasi; API va dizayn o‘zgarmaydi)
  - Native: splash screen, ikonka, status bar ranglari, orqaga tugmasi, sertifikatni yuklab olish va ulashish (Share API)
  - Push-bildirishnomalar (ixtiyoriy, Firebase)
  - Imzolangan release APK + Google Play uchun AAB, versiyalash
- [ ] **iPhone (iOS)** — Android'dan keyin: o‘sha Capacitor loyihasi, Xcode, App Store (Apple Developer akkaunti kerak)

## Eslatmalar
- questions.json da `logic_ru` maydoni yo‘q — bazada bo‘sh, admin panelda to‘ldirish mumkin.
- 7-savolda eng past ball 4 (3 emas), shuning uchun barcha eng past variantlar yig‘indisi 106. Formula TZ bo‘yicha (105 asos) o‘zgarmagan.
