# Claude Code uchun prompt

Quyidagi matnni to‘liq nusxalab Claude Code'ga yuboring. Loyiha papkasi (`TZ.md`, `CLAUDE.md`, `namunalar/` turgan joy) ochiq bo‘lsin.

---

```
Сделай самую красивую вещь, на которую ты способен.

Sen tajribali full-stack dasturchi va kuchli UI/UX dizaynersan. Bu papkada "Mantiqiy test" (IQ test) veb-platformasini noldan qurasan.

1. MANBALAR
   - TZ.md – texnik topshiriq. Har bir bandiga qat'iy amal qil.
   - CLAUDE.md – loyiha qoidalari.
   - namunalar/questions.json – 35 ta savol, 6 tadan variant, ballar, to'g'ri javob. Bu yagona haqiqat manbai: savollarni, ballarni va matnlarni o'zgartirma.
   - namunalar/assets/ – har bir savol rasmi va variant rasmlari (SVG + PNG).
   - namunalar/test_uz.pdf, test_ru.pdf – savollar dizayni namunasi. Saytdagi savol ekrani shu uslubda, lekin yanada chiroyli bo'lsin.
   - namunalar/qollanma.pdf – har bir savol mantiqi va ballar izohi.
   Ishni boshlashdan oldin hammasini o'qib chiq va PDF larni ko'rib chiq.

2. STEK
   Backend: Django 5 + DRF + PostgreSQL 16. Frontend: Next.js (App Router, TypeScript) + Tailwind CSS + Framer Motion. Nginx. Hammasi docker compose da. Batafsil – TZ.md, 4 va 12-bandlar.

3. ENG MUHIM QOIDALAR
   - Ballar va to'g'ri javob hech qachon frontendga yuborilmaydi. Hisoblash faqat serverda.
   - Javob berilmagan savol = 0 ball. Variant ballari 3–7, har savolda aniq bitta 7.
   - Natija "IQ = N" son sifatida ko'rsatilmaydi: faqat ball / 245, foiz va daraja.
   - Barcha matnlar o'zbek (lotin) va rus tilida, i18n fayllarida.

4. DIZAYN
   Bu oddiy test sayti bo'lmasin. Premium mahsulot darajasida, sen qila oladigan eng chiroyli ishni qil:
   - TZ.md 6-banddagi ranglar va Inter shriftidan foydalan; PDF namunadagi uslubni rivojlantir.
   - Bosh sahifada test uslubidagi geometrik shakllar (yulduz, uchburchak, panjara, aylanuvchi strelka) bilan jonli, ammo bezovta qilmaydigan animatsiyalar.
   - Savollar orasida silliq o'tishlar, variant tanlanganda nozik animatsiya, natija sonining sanab chiqishi, natija sahifasida chiroyli diagrammalar.
   - Telefon (360 px) va kompyuterda mukammal; yorug' va qorong'i rejim; prefers-reduced-motion hurmat qilinsin.
   - Har bir holat chiroyli: yuklanish (skeleton), xato, bo'sh holat, vaqt tugashi, tasdiqlash oynasi.
   - Tayyor bo'lgach, Playwright bilan sahifalar skrinshotini olib, o'zing tekshir va dizaynni ko'rinishi mukammal bo'lguncha yaxshila.

5. ISH TARTIBI
   Avval menga qisqa reja ko'rsat (papka tuzilmasi va bosqichlar), keyin bosqichma-bosqich bajar. Har bosqich oxirida ishlashini tekshir:
   1) Docker skeleti: db, backend, frontend, nginx; docker compose up ishlaydi.
   2) Backend modellari, migratsiyalar, import_questions buyrug'i (namunalar/questions.json va rasmlar), admin.
   3) API (TZ.md 9-band) + pytest testlari, ayniqsa ballash va "ball frontendga chiqmasligi" testi.
   4) Frontend dizayn tizimi: tokenlar, shrift, komponentlar (Button, Card, OptionCard, ProgressBar, Timer, QuestionMap, Modal).
   5) Bosh sahifa, boshlash sahifasi, test oqimi (autosave, davom ettirish, taymer, klaviatura).
   6) Natija sahifasi, sertifikat PDF, ulashish kartochkasi.
   7) Admin: statistika, eksport (CSV/XLSX), darajalar sozlamasi.
   8) Telegram Mini App integratsiyasi.
   9) Playwright E2E testi, skrinshotlar bilan dizayn tekshiruvi, README.md.

6. YAKUNIDA
   TZ.md 14-banddagi qabul qilish mezonlarining har birini tekshir va qaysi biri bajarilganini ro'yxat qilib ko'rsat. Bitta buyruq bilan ishga tushirish: docker compose up -d --build.

Agar TZ da biror narsa noaniq bo'lsa, taxmin qilma, mendan so'ra.
```
