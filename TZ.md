# TEXNIK TOPSHIRIQ (TZ)
## "Mantiqiy test" veb-platformasi (IQ test)

| | |
|---|---|
| Versiya | 1.0 |
| Til | O‘zbek (lotin) va rus |
| Turi | Veb-sayt + Telegram Mini App |
| Infratuzilma | Docker / docker compose |
| Ma’lumotlar bazasi | PostgreSQL |

---

## 1. Loyiha maqsadi

Foydalanuvchi brauzerda yoki Telegram ichida 35 ta mantiqiy savoldan iborat testni yechadi va oxirida o‘z natijasini (ball va daraja) ko‘radi. Administrator savollarni boshqaradi, natijalarni ko‘radi va eksport qiladi.

Sayt **juda chiroyli, zamonaviy va silliq** bo‘lishi kerak: premium mahsulot darajasidagi dizayn, yengil animatsiyalar, telefonda ham mukammal ko‘rinish.

---

## 2. Tayyor materiallar (`namunalar/` papkasi)

| Fayl | Tavsif |
|---|---|
| `questions.json` | **Asosiy manba.** 35 ta savol: matn (uz/ru), rasm yo‘li, 6 ta variant, har bir variant bali, to‘g‘ri javob, mantiq izohi, kategoriya |
| `assets/qNN/figure.svg` (+ `.png`) | Savolning asosiy rasmi (vektor, shaffof fon) |
| `assets/qNN/option_A.svg` … `option_F.svg` (+ `.png`) | Rasmli variantlar (rasmli savollar uchun) |
| `test_uz.pdf`, `test_ru.pdf` | Savollarning tayyor ko‘rinishi. **Dizayn uchun namuna** |
| `qollanma.pdf` | Har bir savol mantiqi va har bir variant nega shu ballni olgani |
| `javoblar.json` | Qisqa javob kaliti (to‘g‘ri harf va A–F ballari) |

**Savol turlari:**
- `type: "number"` – variantlar son (`value` maydoni). Rasm yo‘q, son katta shriftda chiziladi.
- `type: "image"` – har bir variant SVG rasm (`image` maydoni).

**Kategoriyalar** (natija sahifasidagi tahlil uchun): `numeric` (7 ta), `pattern` (17 ta), `spatial` (11 ta).

> Savollar va ballar **o‘zgartirilmaydi**. Ular `questions.json` dan bazaga import qilinadi.

---

## 3. Ballash qoidalari (MUHIM)

1. Har savolda 6 ta variant (A–F) bor.
2. Har bir variantning bali bor: **bitta variant 7 ball** (to‘g‘ri javob), qolganlari mantiqqa yaqinligiga qarab **6, 5, 4 yoki 3 ball**. 0 ballik variant yo‘q.
3. **Javob berilmagan savol = 0 ball.**
4. Umumiy ball = barcha javoblar ballari yig‘indisi. Maksimum 35 × 7 = **245**.
5. **Ballar va to‘g‘ri javob hech qachon frontendga yuborilmaydi.** Hisoblash faqat serverda bajariladi. Test vaqtida foydalanuvchi ballarni ko‘rmaydi (PDF dagi "N ball" yozuvlari faqat dasturchi uchun).
6. Ma’lumotlar bazasi darajasida tekshirish: har bir savolda aniq 6 ta variant, ball 3–7 oralig‘ida, aniq bitta variant 7 ball.

### Daraja (natija)

Foiz = (ball − 105) / 140 × 100, ya’ni 0–100% oralig‘ida (105 = 35 × 3, ya’ni barcha savolga javob berilgandagi eng past ball). Agar ball 105 dan kam bo‘lsa (javobsiz savollar sababli), foiz 0 deb olinadi.

| Ball | Daraja (uz) | Daraja (ru) |
|---|---|---|
| 0–139 | Boshlang‘ich | Начальный |
| 140–174 | O‘rta | Средний |
| 175–209 | Yuqori | Высокий |
| 210–234 | Juda yuqori | Очень высокий |
| 235–245 | A’lo | Превосходный |

Chegaralar admin panelda o‘zgartiriladigan bo‘lsin (`ScoreLevel` jadvali).

> **Diqqat:** sayt natijani "IQ = 112" kabi son sifatida **ko‘rsatmaydi**. Test normalashtirilmagan, shuning uchun bunday raqam ilmiy jihatdan noto‘g‘ri bo‘ladi. Faqat ball, foiz va daraja ko‘rsatiladi.

---

## 4. Texnologiyalar

| Qatlam | Texnologiya |
|---|---|
| Backend | Python 3.12, **Django 5 + Django REST Framework**, Gunicorn |
| Frontend | **Next.js (App Router) + TypeScript**, Tailwind CSS, Framer Motion |
| Baza | **PostgreSQL 16** |
| Proxy | Nginx (frontend, `/api`, `/admin`, `/media`, `/static` ni bitta domenda birlashtiradi) |
| Infratuzilma | Docker, docker compose (`db`, `backend`, `frontend`, `nginx`) |
| Shrift | Inter (PDF namunadagidek) |

Barcha versiyalar aniq ko‘rsatilsin (`requirements.txt`, `package-lock.json`). Barcha sozlamalar `.env` orqali; `.env.example` bo‘lishi shart.

---

## 5. Foydalanuvchi qismi (frontend)

### 5.1 Bosh sahifa (`/`)
- Hero bo‘lim: sarlavha, qisqa tavsif, **"Testni boshlash"** tugmasi.
- "Qanday ishlaydi": 3 qadam (savollar soni 35, vaqt, natija).
- Til tanlash: **UZ / RU** (header'da, tanlov saqlanadi).
- Fon va bezaklarda test uslubidagi geometrik shakllar (yulduz, uchburchak, panjara) yengil animatsiya bilan.

### 5.2 Boshlash (`/start`)
- Maydonlar: **Ism familiya** (majburiy), **Telefon** (ixtiyoriy, `+998` formatida niqob).
- Qoidalar: savollar soni, vaqt chegarasi, har savolda 6 ta variant, bitta javob tanlanadi.
- Telegram Mini App ichida ochilsa, ism Telegram ma’lumotlaridan avtomatik to‘ldiriladi.

### 5.3 Test (`/test/{attempt_id}`)
- **Bir ekranda bitta savol.** Yuqorida: savol raqami ("12 / 35"), progress bar, taymer.
- Savol rasmi (`figure.svg`) katta, markazda, `test_uz.pdf` dagi kabi panel ichida.
- 6 ta variant: kompyuterda **3 × 2**, telefonda **2 × 3** to‘r. Variant kartochkasida harf (A–F) va rasm yoki son.
- Variantni bosish uni tanlaydi (aniq "selected" holati: rang, soya, belgi). Javob darhol serverga saqlanadi (autosave).
- Tugmalar: **"Oldingi"**, **"Keyingi"**. Savollar xaritasi (1–35 kichik doirachalar: javob berilgan / berilmagan / joriy) orqali istalgan savolga o‘tish mumkin.
- Klaviatura: `1–6` yoki `A–F` variant tanlaydi, `←/→` savollar orasida yuradi.
- Sahifa yangilansa yoki internet uzilib qaytsa, test o‘sha joydan davom etadi.
- **Taymer**: standart 40 daqiqa (`.env` da `TEST_DURATION_MINUTES`). Vaqt server tomonida ham tekshiriladi. Vaqt tugasa, test avtomatik yakunlanadi.
- **"Testni yakunlash"**: javobsiz savollar soni ko‘rsatilgan tasdiqlash oynasi chiqadi.
- Ballar ham, to‘g‘ri javob ham test davomida ko‘rsatilmaydi.

### 5.4 Natija (`/result/{attempt_id}`)
- Katta animatsiyali ko‘rsatkich: **ball / 245**, foiz, daraja nomi.
- Kategoriyalar bo‘yicha tahlil (3 ta progress bar): Sonli mantiq, Naqsh va ketma-ketlik, Fazoviy tasavvur. Har biri kategoriyadagi maksimal ballga nisbatan foizda.
- Sarflangan vaqt, javob berilgan savollar soni.
- **"Natijani ulashish"**: chiroyli natija kartochkasi (PNG) yaratiladi va Telegram/havola orqali ulashiladi.
- **"Sertifikat (PDF)"**: ism, sana, ball, daraja yozilgan sertifikatni yuklab olish.
- To‘g‘ri javoblar ko‘rsatilmaydi (test qayta ishlatilishi uchun).

### 5.5 Umumiy talablar
- To‘liq moslashuvchan (360 px dan katta ekranlar).
- Yorug‘ va qorong‘i rejim (tizim sozlamasiga qarab + qo‘lda almashtirish).
- Lighthouse: Performance, Accessibility, Best Practices ≥ 90.
- Barcha matnlar i18n fayllarida (`uz.json`, `ru.json`), kodda qattiq yozilgan matn bo‘lmasin.
- Yuklanish holatlari (skeleton), xato holatlari va bo‘sh holatlar chiroyli ishlangan bo‘lsin.

---

## 6. Dizayn tizimi

Asos sifatida `namunalar/test_uz.pdf` uslubi olinadi. Saytda u yanada boyitiladi.

| Token | Rang | Qo‘llanilishi |
|---|---|---|
| `--ink` | `#1B2A41` | Asosiy matn, shakllar |
| `--accent` | `#E4572E` | "?" katagi, asosiy tugmalar, faol holat |
| `--teal` | `#2A7F8F` | Ikkilamchi urg‘u |
| `--soft` | `#9AB3C2` | Yumshoq to‘ldirish |
| `--panel` | `#F4F1EA` | Savol paneli foni |
| `--page` | `#FBFAF7` | Sahifa foni |
| `--line` | `#D6D0C4` | Chegaralar |
| `--muted` | `#7A8291` | Ikkilamchi matn |

- Shrift: **Inter** (400/500/600/700). Sonlar uchun `tabular-nums`.
- Burchak radiuslari: kartochka 14 px, panel 18 px, tugma 12 px.
- Animatsiyalar: savollar orasida silliq o‘tish (slide + fade), variant tanlanganda yengil "pop", natija sonining sanab chiqishi. `prefers-reduced-motion` hurmat qilinadi.
- Qorong‘i rejim uchun ranglar alohida tokenlar bilan beriladi. Savol SVG lari qorong‘i fonda ham o‘qilishi uchun oq/och panel ustida turadi.

---

## 7. Admin panel (`/admin`)

Django admin (zamonaviy tema bilan, masalan `django-unfold`) yoki alohida admin sahifalar.

- **Savollar**: ro‘yxat, tartib, faol/nofaol, rasmni almashtirish, variantlar ballarini tahrirlash (3–7, aniq bitta 7 tekshiruvi bilan), mantiq izohi (uz/ru).
- **Ishtirokchilar va urinishlar**: ism, telefon, til, boshlangan/tugagan vaqt, ball, daraja. Filtr (sana, daraja, til), qidiruv.
- **Urinish tafsiloti**: har bir savolga qaysi variant tanlangani va olgan bali.
- **Eksport**: CSV va Excel (`.xlsx`).
- **Statistika** (dashboard): jami urinishlar, o‘rtacha ball, darajalar taqsimoti; har bir savol bo‘yicha qaysi variant necha marta tanlangani (savolning qiyinligini ko‘rish uchun).
- **Darajalar** (`ScoreLevel`) va test sozlamalarini (vaqt) tahrirlash.

---

## 8. Ma’lumotlar modeli (PostgreSQL)

| Jadval | Asosiy maydonlar |
|---|---|
| `Question` | id, number, type (`number`/`image`), category, prompt_uz, prompt_ru, figure (fayl), logic_uz, logic_ru, order, is_active |
| `Option` | id, question (FK), letter (A–F), value (son, nullable), image (fayl, nullable), points (3–7), reason_uz |
| `Participant` | id, full_name, phone, telegram_id (nullable), language, created_at |
| `Attempt` | id (UUID), participant (FK), status (`in_progress`/`finished`/`expired`), started_at, expires_at, finished_at, total_score, percent, level, category_scores (JSON) |
| `Answer` | id, attempt (FK), question (FK), option (FK), answered_at; unique (attempt, question) |
| `ScoreLevel` | min_score, max_score, name_uz, name_ru, description_uz, description_ru |

Cheklovlar: `Option(question, letter)` unique; `points` 3–7 oralig‘ida; savolda aniq bitta 7 ballik variant (model `clean()` + import paytida tekshiruv).

---

## 9. API (DRF, `/api/v1/`)

| Metod | Yo‘l | Vazifa |
|---|---|---|
| GET | `/test/meta` | Savollar soni, vaqt, tillar |
| POST | `/attempts` | Urinish yaratish (`full_name`, `phone`, `language`) → `attempt_id`, `token`, `expires_at` |
| GET | `/attempts/{id}/questions` | Savollar ro‘yxati (**ballar va to‘g‘ri javobsiz**) + avval tanlangan javoblar |
| PUT | `/attempts/{id}/answers/{question_number}` | Javobni saqlash (`letter`) |
| POST | `/attempts/{id}/finish` | Yakunlash va ballni hisoblash |
| GET | `/attempts/{id}/result` | Natija |
| GET | `/attempts/{id}/certificate.pdf` | Sertifikat |
| POST | `/telegram/auth` | Telegram `initData` ni bot token bilan tekshirish |

- Urinish `token` orqali himoyalanadi (boshqa odam birovning urinishini ocholmaydi).
- Muddati o‘tgan yoki yakunlangan urinishga javob yozib bo‘lmaydi.
- Rate limiting (DRF throttling), CORS faqat o‘z domeni uchun.
- OpenAPI hujjati (`/api/docs`, drf-spectacular).

---

## 10. Import (seed)

- `python manage.py import_questions /app/namunalar/questions.json` – savollar, variantlar va rasmlarni bazaga yuklaydi. Qayta ishga tushirilsa, dublikat yaratmaydi (update).
- `ScoreLevel` standart qiymatlari migration orqali yaratiladi.
- `docker compose up` dan keyin birinchi ishga tushishda migratsiya va import avtomatik bajariladi (entrypoint skripti), superuser `.env` dagi ma’lumotlar bilan yaratiladi.

---

## 11. Telegram Mini App

- Sayt Telegram WebApp sifatida ochilganda: `Telegram.WebApp.ready()`, `expand()`, Telegram mavzu ranglariga moslashish, "BackButton" bilan orqaga qaytish.
- `initData` server tomonida `TELEGRAM_BOT_TOKEN` bilan tekshiriladi, `telegram_id` saqlanadi.
- Oddiy brauzerda ham to‘liq ishlaydi.

---

## 12. Docker

```
docker compose up -d --build
```
- Servislar: `db` (postgres:16, volume bilan), `backend`, `frontend`, `nginx` (80-port).
- `healthcheck` lar, `depends_on: condition: service_healthy`.
- Media va static fayllar volume'da saqlanadi.
- `docker-compose.override.yml` (dev, hot reload) va asosiy fayl (prod) alohida.
- `.env.example`: `POSTGRES_*`, `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS`, `DJANGO_SUPERUSER_*`, `TEST_DURATION_MINUTES`, `TELEGRAM_BOT_TOKEN`, `PUBLIC_URL`.

---

## 13. Sifat va testlar

- Backend: ballash, daraja, muddati o‘tish, ruxsatlar va import uchun pytest testlari.
- API javoblarida ball/to‘g‘ri javob yo‘qligini tekshiradigan alohida test.
- Frontend: asosiy oqim uchun Playwright E2E testi (boshlash → 35 savol → natija).
- `README.md`: o‘rnatish, ishga tushirish, admin ga kirish, savollarni yangilash.

---

## 14. Qabul qilish mezonlari

- [ ] `docker compose up -d --build` bitta buyruq bilan hammasini ishga tushiradi, `http://localhost` da sayt ochiladi.
- [ ] 35 ta savol `questions.json` dan avtomatik import qilingan, rasmlar to‘g‘ri ko‘rinadi.
- [ ] Har savolda 6 ta variant, ballar `questions.json` bilan bir xil.
- [ ] Test davomida brauzer tarmoq so‘rovlarida ball yoki to‘g‘ri javob ko‘rinmaydi.
- [ ] Sahifa yangilanganda test davom etadi, taymer to‘g‘ri ishlaydi.
- [ ] Natija: ball, foiz, daraja, kategoriyalar tahlili, sertifikat PDF, ulashish kartochkasi.
- [ ] UZ va RU tillari to‘liq ishlaydi.
- [ ] Admin: savollar, urinishlar, eksport, statistika ishlaydi.
- [ ] Telefon (360 px) va kompyuterda dizayn mukammal ko‘rinadi, qorong‘i rejim ishlaydi.
- [ ] Testlar o‘tadi.
