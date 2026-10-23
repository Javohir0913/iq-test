# Loyiha qoidalari (Claude Code uchun)

- Loyiha: "Mantiqiy test" (IQ test) veb-platformasi. To‘liq talablar – `TZ.md`.
- Savollar, ballar va to‘g‘ri javoblar uchun yagona manba – `namunalar/questions.json`. Ularni o‘zgartirma.
- Ballar va to‘g‘ri javob frontendga hech qachon yuborilmaydi; hisoblash faqat backendda.
- Variant ballari 3–7, har savolda aniq bitta 7. Javobsiz savol – 0 ball. Maksimum 245.
- Natija "IQ = N" son sifatida ko‘rsatilmaydi.
- UI matnlari o‘zbek (lotin) va rus tilida, faqat i18n fayllarida.
- Stek: Django 5 + DRF + PostgreSQL 16, Next.js (TypeScript) + Tailwind + Framer Motion, Nginx, docker compose.
- Barcha sozlamalar `.env` orqali; maxfiy ma’lumotlarni kodga yozma.
- Har bosqichdan keyin `docker compose up` va testlar bilan tekshir.
- Dizayn: `TZ.md` 6-band tokenlari, Inter shrifti, `namunalar/test_uz.pdf` uslubi asosida, premium darajada.
- Noaniq joy bo‘lsa, taxmin qilma – so‘ra.
