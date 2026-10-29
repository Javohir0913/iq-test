# Loyiha qoidalari (Claude Code uchun)

- Loyiha: "Mantiqiy test" (IQ test) veb-platformasi. To‘liq talablar – `TZ.md`.
- Savollar, ballar va to‘g‘ri javoblar uchun yagona manba – `namunalar/questions.json`. Ularni o‘zgartirma.
- Ballar va to‘g‘ri javob frontendga hech qachon yuborilmaydi; hisoblash faqat backendda.
- Variant ballari 3–7, har savolda aniq bitta 7. Javobsiz savol – 0 ball. Maksimum = urinishdagi savollar soni × 7.
- Test 3 bosqichli (`Stage`): savollar bankdan qiyinlik bo‘yicha tasodifiy tanlanadi, urinishga `question_ids` sifatida yoziladi. Darajalar (`ScoreLevel`) foizda.
- Bosqich ochilishi: majburiy kanallar (`RequiredChannel`, admin panelda yoqiladi) va taklif qilingan do‘stlar (`quiz/progress.py`).
- Natija "IQ = N" son sifatida ko‘rsatilmaydi.
- UI matnlari o‘zbek (lotin), rus va ingliz tilida, faqat i18n fayllarida (frontend, backend, bot – uchala til kalitlari bir xil).
- Stek: Django 5 + DRF + PostgreSQL 16, Next.js (TypeScript) + Tailwind + Framer Motion, Nginx, docker compose.
- Barcha sozlamalar `.env` orqali; maxfiy ma’lumotlarni kodga yozma.
- Har bosqichdan keyin `docker compose up` va testlar bilan tekshir. Testlarni hech qachon production bazasiga ulangan konteynerda ishga tushirma (entrypoint migratsiya qiladi).
- Dizayn: `TZ.md` 6-band tokenlari, Inter shrifti, `namunalar/test_uz.pdf` uslubi asosida, premium darajada.
- Noaniq joy bo‘lsa, taxmin qilma – so‘ra.
