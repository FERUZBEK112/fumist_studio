# FUMIST Studio — ishga tushirish

GitHub: https://github.com/FERUZBEK112/fumist_studio

Railway: https://railway.com/project/9197fa2c-ab04-44e7-9f6f-47affedad5be/service/addf5fe5-2905-4f29-817d-4ae7953292ee?environmentId=7c7f37d6-1b67-48e5-a90d-63faf0329c71

Sayt uchun ajratilgan manzil: https://fumist-studio-production.up.railway.app

## 1. Botlar

@BotFather orqali ikkita alohida bot yarating:

1. FUMIST Studio — foydalanuvchilar uchun.
2. FUMIST Admin — to‘lovlarni ko‘rib chiqish uchun.

Tokenlarni faqat Railway → fumist-studio → Variables bo‘limiga kiriting. GitHub kodiga yoki postga joylamang.

| Variable | Qiymati |
| --- | --- |
| `BOT_TOKEN` | Foydalanuvchi botining tokeni |
| `BOT_USERNAME` | Foydalanuvchi botining username’i, @ belgisiz |
| `ADMIN_BOT_TOKEN` | Ikkinchi, admin botning tokeni |
| `ADMIN_IDS` | Sizning raqamli Telegram ID’ingiz; bir necha admin bo‘lsa vergul bilan |
| `CARD_NUMBER` | To‘lov qabul qiluvchi karta raqami |
| `CARD_HOLDER` | Kartada ko‘rsatiladigan egasining ism-sharifi |

Telegram ID’ni bilish uchun bot tokeni sozlangach o‘z botingizga `/id` yuboring. Bot faqat xabar yuborgan odamning o‘z ID’sini qaytaradi. Keyin shu sonni `ADMIN_IDS`ga yozing.

Ikkala botga ham o‘z Telegram akkauntingizdan `/start` bosing. Admin bot siz uni birinchi marta ochmaguningizcha sizga chek yuborolmaydi.

## 2. Mini App

@BotFather → foydalanuvchi boti → Bot Settings → Menu Button / Main Mini App sozlamalarida saytning HTTPS manzilini kiriting.

Sayt va Mini App uchun O‘zbekcha / Русский / English, Qorong‘i / Yorug‘ / Tizimga mos mavjud. Oddiy Telegram chatining rangini Telegram boshqaradi; botdagi mavzu Mini App ko‘rinishiga ta’sir qiladi.

## 3. Tariflar

- Free — bepul.
- Plus — 15 000 so‘m / 1 kalendar oy.
- Pro — 40 000 so‘m / 1 kalendar oy.

Narxlar oldindan `PLUS_PRICE_UZS=15000`, `PRO_PRICE_UZS=40000` qilib belgilangan.

**Chek yuborilishi obunani ochmaydi.** To‘lovni bank tarixingizdan tekshirib, admin botdagi `✅ Tasdiqlash`ni bosganingizdan keyingina ochiladi. Muddat aynan shu vaqtdan boshlanadi. Masalan: 17-noyabr 20:30 → 17-dekabr 20:30. Oyda bunday kun bo‘lmasa keyingi oyning oxirgi kuni olinadi. `❌ Rad etish` obunani ochmaydi.

Obuna qayta sotib olinsa, yangi tasdiqlash vaqtidan bir oylik muddat boshlanadi. Eski muddat ustiga avtomatik qo‘shilmaydi.

Mustaqil sayt orqali karta va chek ishlatiladi. Telegram ichida raqamli obuna faqat Stars bilan sotiladi; `PLUS_PRICE_STARS` va `PRO_PRICE_STARS` qiymatlari belgilanmaguncha bu xarid yopiq. Stars to‘lovi ham avval tasdiq kutadi. Stars to‘lovini rad etishning o‘zi pulni qaytarmaydi: admin botda `/refund ORDER_ID` ishlatiladi.

Hamma sozlamalar kiritilib, tekshirilgandan keyin `BILLING_ENABLED=true` qiling.

## 4. AI subtitr

`ENABLE_AI_TRANSCRIPTION=true` bo‘lsa, nutqni matnga aylantirish yoqiladi. `WHISPER_MODEL=base` boshlang‘ich variant. Model birinchi ishlatishda yuklanadi; CPU ishlovi vaqt oladi. Kamida 2 GB RAM tavsiya qilinadi. O‘zbekcha matnni albatta tekshiring.

Pauzalarni aniqlash, SRT import/eksport, oddiy montaj va MP4 eksport uchun AI model kerak emas.

## 5. Ishga tushirish tekshiruvi

1. Akkaunt oching va kichik video yuklang.
2. Qisqartiring, matn va musiqa qo‘shing, MP4 eksport qiling.
3. Til va mavzuni o‘zgartirib, qayta kirishda saqlanganini tekshiring.
4. Kartaga haqiqiy to‘lovingizni tekshirgandan keyin Plus/Pro uchun chek yuboring: sayt hali Free bo‘lib qolishi kerak.
5. Admin botda tasdiqlang: sayt yangilanganda obuna ochilishi kerak.
6. Ikkinchi marta tasdiqlash obuna muddatini uzaytirmasligi kerak.

`/stats` — statistika. `/pending` — tasdiq kutayotgan to‘lovlar. `/block USER_ID` — bloklash. `/unblock USER_ID` — ochish.

Media va eksportlar odatda 30 kun saqlanadi. Muhim fayllarni yuklab oling. Birinchi versiyada parolni tiklash yordam orqali amalga oshiriladi.
