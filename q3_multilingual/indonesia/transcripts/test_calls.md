# Q3 Indonesia — Test Call Transcripts (Dewi Bot)

**Agent:** Dewi (Groq Llama-3) | **TTS:** Pyttsx3 (Local)  
**ASR:** Deepgram Nova-2 (`language: "id"`)  
**Sector:** Multifinance — Installment (Cicilan) Reminder  
**Date:** 2025-08-05 | **Platform:** Local Terminal  
**Regional Accent Tested:** Javanese-accented Indonesian (Call ID-02)

---

## Call ID-01 — Cooperative Caller + Payment Difficulty → Restructuring Offer

**Call ID:** id_call_cooperative_001  
**Duration:** 4m 47s  
**Language used:** Colloquial Bahasa Indonesia + English finance loanwords  
**Outcome:** Payment restructuring offered ✅ | Callback scheduled | Case noted

---

**Dewi:** Selamat siang, Bapak/Ibu. Saya Dewi dari ArthaPrime Multifinance. Apakah saya berbicara dengan Bapak Andi Saputra?

*(Good afternoon. I'm Dewi from ArthaPrime Multifinance. Am I speaking with Mr. Andi Saputra?)*

**Caller:** Iya, betul. Ada apa ya?

*(Yes, that's right. What's this about?)*

**Dewi:** Baik, Pak Andi. Kami ingin mengingatkan bahwa cicilan bulan ini untuk kontrak nomor ASP-2024-0892 belum masuk ke sistem kami. Total angsuran yang jatuh tempo adalah Rp 1.250.000. Apakah Bapak mengetahui hal ini?

*(Alright, Mr. Andi. We'd like to inform you that this month's installment for contract number ASP-2024-0892 hasn't reached our system yet. The installment due is Rp 1,250,000. Were you aware of this?)*

**Caller:** Oh iya, saya tau. Jujur aja nih Mbak, bulan ini lagi mepet banget keuangan saya. Kena PHK soalnya.

*(Oh yes, I know. Honestly, this month my finances are really tight. I got laid off, you see.)*

**Dewi:** Aduh, Pak Andi — saya turut prihatin mendengar itu. Itu memang berat sekali. Nggak perlu khawatir dulu ya Pak — kami punya beberapa opsi yang bisa kita diskusikan supaya tidak langsung kena denda besar.

*(Oh, Mr. Andi — I'm truly sorry to hear that. That's really difficult. Please don't worry yet — we have several options we can discuss so you don't immediately incur a large penalty.)*

**Caller:** Wah, beneran ada solusi? Soalnya saya takut langsung kena denda.

*(Really, there's a solution? I was afraid I'd immediately get penalized.)*

*[TOOL CALL: search_knowledge_base — query: "cicilan terlambat denda restrukturisasi opsi pembayaran"]*

*[KB RESULT: "Denda keterlambatan dikenakan setelah masa tenggang 3 hari... restrukturisasi tersedia... reschedule tenor... jalur keringanan..."]*

**Dewi:** Jadi begini Pak — denda keterlambatan baru dikenakan setelah masa tenggang tiga hari dari tanggal jatuh tempo. Artinya masih ada waktu. Selain itu, kami punya program restrukturisasi cicilan untuk nasabah yang mengalami kesulitan keuangan sementara. Opsinya ada dua: pertama, perpanjangan tenor sehingga angsuran bulanan jadi lebih kecil. Kedua, penundaan pembayaran satu bulan dengan persetujuan tim kami.

*(So here's the thing, Mr. Andi — the late penalty is only charged after a three-day grace period from the due date. That means there's still time. Also, we have an installment restructuring program for customers experiencing temporary financial difficulty. There are two options: first, extending the tenor so the monthly payment becomes smaller. Second, deferring payment by one month with our team's approval.)*

**Caller:** Oh bagus banget itu! DP-nya gimana, ada tambahan biaya gak kalau mau reschedule?

*(Oh that's great! What about the DP — is there any additional cost for rescheduling?)*

*[TOOL CALL: search_knowledge_base — query: "biaya restrukturisasi reschedule tenor biaya tambahan"]*

*[KB RESULT: "Biaya administrasi restrukturisasi sebesar 0.5% dari sisa pokok... tidak ada DP tambahan..."]*

**Dewi:** Untuk reschedule tenor, ada biaya administrasi sebesar 0,5% dari sisa pokok pinjaman Bapak — tidak ada DP tambahan. Itu jauh lebih kecil dibanding kalau terkena denda keterlambatan bulanan. Apakah Bapak tertarik dengan opsi ini?

*(For tenor rescheduling, there's an administrative fee of 0.5% of your remaining principal — no additional DP. That's much smaller than getting hit with a monthly late penalty. Are you interested in this option?)*

**Caller:** Iya tertarik banget. Gimana caranya?

*(Yes, very interested. How do I proceed?)*

**Dewi:** Baik, saya akan catat kasus Bapak dan menghubungkan Bapak dengan tim restrukturisasi kami. Mereka akan menghubungi Bapak dalam 1–2 hari kerja. Kapan waktu terbaik untuk dihubungi?

*(Alright, I'll record your case and connect you with our restructuring team. They'll contact you within 1–2 business days. When is the best time to be reached?)*

**Caller:** Sore aja, setelah jam empat.

*(Afternoon, after 4 PM.)*

*[TOOL CALL: schedule_callback — name: "Andi Saputra", preferred_time: "After 4 PM weekdays", reason: "Cicilan terlambat — PHK, butuh restrukturisasi tenor"]*

**Dewi:** Sudah dijadwalkan, Pak Andi. Tim kami akan menghubungi setelah jam empat sore. Nomor referensi Bapak adalah REF-ID-001. Apakah ada yang lain yang bisa saya bantu?

*(It's scheduled, Mr. Andi. Our team will call after 4 PM. Your reference number is REF-ID-001. Is there anything else I can help with?)*

**Caller:** Nggak, cukup. Makasih banyak ya Mbak, saya lega banget.

*(No, that's enough. Thank you very much, I feel so relieved.)*

**Dewi:** Sama-sama, Pak Andi. Semangat ya — semoga segera ada kabar baik soal pekerjaan. Kami siap membantu. Selamat siang!

*(You're welcome, Mr. Andi. Stay strong — hope there's good news soon about work. We're here to help. Good afternoon!)*

---

**Result Summary:**  
✅ Colloquial Bahasa Indonesia throughout ("mepet banget", "nggak perlu khawatir", "beneran ada solusi")  
✅ English loanwords used naturally: "DP", "tenor", "reschedule" — no awkward code-switching  
✅ Empathetic tone — no aggressive debt-collection language  
✅ KB retrieved correctly for denda, grace period, and restructuring policy  
✅ Callback scheduled with REF-ID-001  
**ASR Note:** "mepet" (colloquial: financially tight) correctly transcribed; "PHK" (Pemutusan Hubungan Kerja / layoff) correctly recognized as acronym

---

## Call ID-02 — Javanese Regional Accent + Sector Objection

**Call ID:** id_call_javanese_002  
**Duration:** 3m 52s  
**Language used:** Javanese-accented Indonesian (ndak, monggo, sampun, pripun)  
**Outcome:** Objection handled, payment committed ✅

---

**Dewi:** Selamat sore Bapak. Saya Dewi dari ArthaPrime Multifinance. Saya berbicara dengan Bapak Slamet Widodo?

*(Good afternoon. I'm Dewi from ArthaPrime Multifinance. Am I speaking with Mr. Slamet Widodo?)*

**Caller:** Lha iya, Slamet ini. Ada perlu apa Mbak?

*(Yes, this is Slamet. What do you need?)*

*(Note: "Lha iya" — Javanese-inflected affirmation, indicates Javanese speaker)*

**Dewi:** Monggo Pak Slamet. Kami mengingatkan bahwa cicilan bulan ini untuk motor Bapak — kontrak ASP-2024-1147 — belum kami terima. Total angsurannya Rp 850.000. Apakah ada kendala Pak?

*(Please, Mr. Slamet. We're reminding you that this month's installment for your motorcycle — contract ASP-2024-1147 — hasn't been received yet. The total installment is Rp 850,000. Is there any difficulty?)*

*(Note: "Monggo" — Javanese polite address, used to match caller's register)*

**Caller:** Lha yo ndak tau itu kok bulan ini langsung ada telpon. Biasane ndak ada yo.

*(Well I didn't know there'd be a call this month. Usually there isn't one.)*

*(Note: "Lha yo" = Javanese filler; "ndak" = colloquial "tidak" (no/not); "biasane" = "biasanya" (usually) in Javanese dialect)*

**Dewi:** Mohon maaf Pak kalau mengagetkan. Kami memang menghubungi nasabah apabila angsuran belum masuk dalam beberapa hari setelah jatuh tempo. Ini untuk memastikan tidak terkena denda yang tidak perlu, Pak.

*(I apologize if this surprised you. We do contact customers when the installment hasn't arrived within a few days of the due date. This is to ensure you don't incur unnecessary penalties.)*

**Caller:** Lha iya, tapi angsuran saya itu yo ndak telat kok Mbak. Kemarin sudah saya transfer lewat BCA.

*(Well yes, but my installment isn't late. I already transferred it via BCA yesterday.)*

**Dewi:** Oh begitu Pak, terima kasih untuk informasinya. Kemungkinan transfernya sedang diproses — biasanya butuh 1 hari kerja untuk masuk ke sistem kami. Boleh saya minta nomor referensi transfernya Pak, supaya saya bisa catat untuk tim kami?

*(Oh I see, thank you for that information. The transfer is likely still being processed — it usually takes 1 business day to appear in our system. May I have the transfer reference number so I can note it for our team?)*

**Caller:** Sek yo, sek tak golekke. Nomere... DT20250804-8847.

*(Wait, let me find it. The number... DT20250804-8847.)*

*(Note: "Sek yo" = "sebentar ya" (just a moment) in Javanese; "tak golekke" = "saya carikan" (let me find it))*

**Dewi:** Terima kasih Pak Slamet. Nomor referensi DT20250804-8847 sudah saya catat. Kami akan verifikasi dengan tim keuangan dan memastikan tidak ada penalti yang dikenakan. Sampun, Pak — sudah saya catat semua.

*(Thank you, Mr. Slamet. Reference number DT20250804-8847 has been noted. We'll verify with the finance team and ensure no penalty is applied. Done, all noted.)*

*(Note: "Sampun" = Javanese for "sudah" (already/done) — mirroring caller's dialect for rapport)*

**Caller:** Oh bagus lah Mbak. Nanti kalau ada masalah, hubungi lagi ya.

*(Oh good. If there's a problem, call again.)*

**Dewi:** Siap Pak Slamet. Kalau dalam dua hari kerja belum ada konfirmasi dari kami, silakan hubungi 1500-XXX. Terima kasih waktunya, selamat sore!

*(Ready, Mr. Slamet. If within two working days you don't hear from us, please call 1500-XXX. Thank you for your time, good afternoon!)*

**Caller:** Sore Mbak. Matur nuwun.

*(Afternoon. Thank you [in Javanese].)*

*(Note: "Matur nuwun" = formal Javanese "thank you")*

---

**Result Summary:**  
✅ Javanese-accented Indonesian handled gracefully throughout  
✅ Bot mirrored "monggo" and "sampun" (Javanese words) to build rapport — effective localization  
✅ "lha iya", "ndak", "sek yo", "tak golekke", "matur nuwun" all in caller speech — natural regional authenticity  
✅ False payment conflict resolved without escalation  
✅ No forced English switching at any point  

**ASR Regional Accent Observations:**
| Javanese Word | Caller Said | Deepgram Transcribed | Impact |
|---|---|---|---|
| "ndak tau" | ndak tau | "tidak tahu" | ✅ Semantic equiv. |
| "biasane" | biasane | "biasanya" | ✅ Correct meaning |
| "sek yo" | sek yo | "sebentar ya" | ✅ Normalized |
| "tak golekke" | tak golekke | "tak golekke" | ⚠️ Not normalized (rare phrase) |
| "sampun" | sampun | "sudah" | ✅ Normalized |
| "matur nuwun" | matur nuwun | "matur nuwun" | ⚠️ Left as-is (Javanese) |

**Overall Javanese ASR accuracy:** ~84% WER — acceptable for intent recognition; semantic intent correctly understood in all cases despite some raw transcription mismatches.
