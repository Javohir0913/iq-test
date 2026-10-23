# Mantiqiy test (IQ test) platformasi

35 ta mantiqiy savoldan iborat test: veb-sayt + Telegram Mini App. Natija **ball / 245, foiz va daraja** ko‘rinishida beriladi. Test normalashtirilmagani uchun sayt "IQ = N" raqamini ko‘rsatmaydi.

| Qatlam | Texnologiya |
|---|---|
| Backend | Python 3.12, Django 5.1, Django REST Framework, Gunicorn, django-unfold (admin) |
| Frontend | Next.js 15 (App Router, TypeScript), Tailwind CSS, Framer Motion |
| Baza | PostgreSQL 16 |
| Proxy | Nginx (`/` → frontend; `/api`, `/admin`, `/static`, `/media` → backend) |

## Tez boshlash

Talab: Docker Desktop (yoki Docker Engine + compose plagini).

```bash
cp .env.example .env        # parollar va maxfiy kalitni o‘zgartiring
docker compose -f docker-compose.yml up -d --build
```

Sayt: **http://localhost** · Admin: **http://localhost/admin/** · API hujjati: **http://localhost/api/docs**

Birinchi ishga tushishda `backend/entrypoint.sh` avtomatik bajaradi:
1. migratsiyalar (shu jumladan standart `ScoreLevel` darajalari);
2. `import_questions` — `namunalar/questions.json` dan 35 savol va rasmlar (bazada savol bo‘lmasa);
3. `.env` dagi `DJANGO_SUPERUSER_*` bo‘yicha superuser;
4. `collectstatic`.

### Dev rejimi (hot reload)

`docker-compose.override.yml` dev sozlamalarini qo‘shadi: Django `runserver` va `next dev`, kod volume orqali ulanadi. Compose bu faylni avtomatik qo‘shadi:

```bash
docker compose up -d --build        # dev (override bilan)
docker compose -f docker-compose.yml up -d --build   # prod (faqat asosiy fayl)
```

## Server (iq.coffee-nap.uz)

Kod serverda `~/iq-test` papkasida (GitHub: `Javohir0913/iq-test`). Stack faqat `127.0.0.1:5183` da tinglaydi, tashqariga host nginx (`/etc/nginx/sites-available/iq.coffee-nap.uz`) HTTPS bilan chiqaradi. Serverdagi `.env` da `COMPOSE_FILE=docker-compose.yml`, shuning uchun u yerda oddiy `docker compose …` prod rejimida ishlaydi.

```bash
ssh azureuser@20.84.45.45
cd ~/iq-test && ./deploy/update.sh          # git pull + qayta qurish
docker compose logs -f backend bot           # loglar
grep DJANGO_SUPERUSER_PASSWORD .env          # admin paroli
```

Eslatma: bitta bot tokeni bilan bot faqat bitta joyda ishlashi kerak – lokal sinovda `bot` servisini ishga tushirmang (yoki boshqa test bot tokenidan foydalaning).

## Admin panel

`http://localhost/admin/` ga `.env` dagi `DJANGO_SUPERUSER_USERNAME` / `DJANGO_SUPERUSER_PASSWORD` bilan kiring.

- **Boshqaruv paneli / Statistika** — jami urinishlar, o‘rtacha ball, darajalar taqsimoti, so‘nggi 14 kun, eng qiyin savollar, har bir savolda qaysi variant necha marta tanlangani.
- **Savollar** — ro‘yxat, tartib, faol/nofaol, rasmni almashtirish, variant ballari. Tekshiruv: 6 ta variant, ball 3–7, aniq bitta 7 (formada va baza cheklovlarida).
- **Urinishlar** — filtrlar (holat, daraja, til, sana), qidiruv, har bir javob va uning bali; **CSV / Excel eksport** (yuqoridagi tugmalar yoki tanlanganlar uchun amal).
- **Ishtirokchilar**, **Darajalar** (chegaralarni tahrirlash), **Sozlamalar** (test vaqti).

## Savollarni yangilash

Savollar va ballarning yagona manbai — `namunalar/questions.json` (+ `namunalar/assets/`).

```bash
docker compose exec backend python manage.py import_questions /app/namunalar/questions.json
```

Buyruq idempotent: savollar `number`, variantlar (savol, harf) bo‘yicha yangilanadi, dublikat yaratilmaydi. Import oldidan butun fayl tekshiriladi; xato bo‘lsa hech narsa yozilmaydi. Eslatma: prod obrazida `namunalar/` obraz ichiga ko‘chiriladi, shuning uchun fayl o‘zgarsa obrazni qayta quring (`--build`).

## Ballash

- Har savolda 6 variant: bittasi 7 ball (to‘g‘ri), qolganlari 6/5/4/3. Javobsiz savol = 0.
- Umumiy ball = yig‘indi, maksimum 245. Foiz = (ball − 105) / 140 × 100 (0 dan past bo‘lsa 0).
- Ballar va to‘g‘ri javob **hech qachon frontendga yuborilmaydi**; hisob faqat serverda (`backend/quiz/services.py`).
- Taymer server tomonida tekshiriladi (`TEST_DURATION_MINUTES` yoki admin → Sozlamalar). Muddat o‘tgan urinish avtomatik yakunlanadi.

## Telegram bot va Mini App

Bot `bot/` papkasida (aiogram 3) va `bot` servisi sifatida avtomatik ishga tushadi.

1. @BotFather dan olingan tokenni `.env` dagi `TELEGRAM_BOT_TOKEN` ga yozing.
2. Mini App faqat **HTTPS** bilan ochiladi:
   - **Domen bo‘lmasa** (sinov): `.env` da `COMPOSE_PROFILES=tunnel` qoldiring. `tunnel` servisi (Cloudflare quick tunnel) bepul `https://….trycloudflare.com` manzil beradi; bot va backend uni avtomatik topadi, bot menyu tugmasini ham o‘zi yangilaydi. Manzil tunnel qayta ishga tushganda o‘zgaradi.
   - **Domen bo‘lsa** (prod): `PUBLIC_URL=https://sizning-domen.uz` yozing va `COMPOSE_PROFILES` qatorini o‘chiring (HTTPS sertifikatini domen oldidagi proxy/Cloudflare beradi).
3. `docker compose -f docker-compose.yml up -d --build` — bot `docker compose logs bot` da `Mini App manzili: https://…` deb yozadi.

Bot imkoniyatlari:
- `/start` — salomlashish va **«Testni boshlash»** (Mini App) tugmasi; chat menyusida ham «Test» tugmasi bor.
- `/test`, `/natija` (so‘nggi natijalar, natijani ochish yoki tugallanmagan testni davom ettirish), `/yordam`.
- Uz/ru — foydalanuvchining Telegram tiliga qarab. Buyruqlar va bot tavsifi ham ikki tilda.
- Test yakunlanganda natija (ball, foiz, daraja) va «Natijani ochish» tugmasi bot chatiga avtomatik yuboriladi (`TELEGRAM_NOTIFY_RESULTS`).

Mini App ichida: `ready()`, `expand()`, Telegram mavzusi (yorug‘/qorong‘i) va til, BackButton, haptic, test vaqtida yopishdan oldin tasdiq, pastga surganda yopilib ketmaslik, sertifikat `downloadFile` orqali yuklanadi. `initData` serverda bot tokeni bilan tekshiriladi va `telegram_id` saqlanadi. Bot uchun ichki API (`/api/v1/bot/…`) faqat Docker ichki tarmog‘ida ochiq, tashqaridan yopilgan.

## Testlar

```bash
# Backend (pytest): ballash, darajalar, muddat, ruxsatlar, import, "ball sizmasligi", admin, Telegram
docker compose exec backend pytest

# Bot (pytest)
docker compose run --rm --no-deps bot python -m pytest -q tests

# Frontend E2E (Playwright): boshlash → 35 savol → natija, tarmoqda ball yo‘qligi, PDF, til, qorong‘i rejim
cd frontend
npm ci
npx playwright install chromium
npm run e2e                     # BASE_URL=http://localhost standart

# Dizayn skrinshotlari (desktop/mobil, yorug‘/qorong‘i, uz/ru)
node e2e/screenshots.mjs ./screenshots
```

## Tuzilma

```
backend/            Django loyiha (config/) va quiz ilovasi
  quiz/models.py      Question, Option, Participant, Attempt, Answer, ScoreLevel, TestSettings
  quiz/services.py    ballash va urinish holati
  quiz/api/           DRF API (/api/v1/)
  quiz/certificate.py sertifikat PDF (ReportLab, Inter)
  quiz/admin.py       admin, eksport, statistika
  tests/              pytest
bot/                Telegram bot (aiogram 3): iqbot/, i18n/, tests/
frontend/           Next.js ilova
  src/app/            sahifalar: /, /start, /test/[id], /result/[id]
  src/components/     dizayn tizimi komponentlari
  src/i18n/           uz.json, ru.json
  e2e/                Playwright testlari
nginx/nginx.conf
namunalar/          savollar, rasmlar, PDF namunalar (o‘zgartirilmaydi)
```

## API (`/api/v1/`)

| Metod | Yo‘l | Vazifa |
|---|---|---|
| GET | `/test/meta` | savollar soni, vaqt, tillar |
| POST | `/attempts` | urinish yaratish → `attempt_id`, `token`, `expires_at` |
| GET | `/attempts/{id}/questions` | savollar (ballarsiz) + tanlangan javoblar |
| PUT | `/attempts/{id}/answers/{n}` | javobni saqlash (`{"letter": "A"}`, `null` – bekor qilish) |
| POST | `/attempts/{id}/finish` | yakunlash va hisoblash |
| GET | `/attempts/{id}/result` | natija |
| GET | `/attempts/{id}/certificate.pdf?token=…&lang=uz` | sertifikat |
| POST | `/telegram/auth` | Telegram `initData` tekshiruvi |

Urinish so‘rovlari `X-Attempt-Token` sarlavhasi bilan himoyalangan. Rate limiting — DRF throttling (`THROTTLE_*` o‘zgaruvchilari).
