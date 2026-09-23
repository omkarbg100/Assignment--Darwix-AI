# Q3 Philippines — Test Call Transcripts (Maya Bot)

**Agent:** Maya (Groq Llama-3) | **TTS:** Pyttsx3 (Local)  
**ASR:** Deepgram Nova-2 (`language: "fil"`, code-switching enabled)  
**Sector:** Life Insurance / Bancassurance  
**Date:** 2025-08-05 | **Platform:** Local Terminal

---

## Call PH-01 — Cooperative Customer (Family Plan, Qualified Lead)

**Call ID:** ph_call_cooperative_001  
**Duration:** 5m 24s  
**Language used:** Taglish (English/Filipino natural mix)  
**Outcome:** Qualified ✅ | Plan: SunShield Premium Family | Lead: LEAD-PH-001

---

**Maya:** Magandang hapon po! Ako po si Maya mula sa SunLife Assurance Philippines. Tumawag po ako para ibahagi ang aming SunShield Life Plus — isang buhay na seguro na espesyal na dinisenyo para sa Pilipinong pamilya. May ilang minuto po ba kayo?

*(Good afternoon! I'm Maya from SunLife Assurance Philippines. I'm calling to share our SunShield Life Plus — a life insurance plan specially designed for Filipino families. Do you have a few minutes?)*

**Caller:** Oo, sige. Mag-usap tayo.

*(Yes, go ahead. Let's talk.)*

**Maya:** Salamat po! Una po, pwede ko bang malaman ang inyong pangalan?

*(Thank you! First, may I know your name?)*

**Caller:** Carlo Reyes.

**Maya:** Salamat, Carlo! Ilang taon na po kayo, kung okay lang?

*(Thank you, Carlo! How old are you, if that's okay to ask?)*

**Caller:** Tatlumpu't lima. Thirty-five.

*(Thirty-five.)*

**Maya:** Maganda po 'yan — sa edad na 'yan, mas mababang premium pa rin kayo. May pamilya na po ba kayo — may asawa o mga anak?

*(That's great — at that age, you still get lower premiums. Do you have a family — a spouse or children?)*

**Caller:** Oo, may asawa ako at dalawang bata. Isa ay five years old, isa ay two years old.

*(Yes, I have a wife and two kids. One is five years old, one is two years old.)*

**Maya:** Napakaganda! Para sa isang pamilya ng apat, ang aming family plan ay perpekto. May trabaho po ba kayo ngayon?

*(How wonderful! For a family of four, our family plan is perfect. Are you currently employed?)*

**Caller:** Oo, IT engineer ako sa isang multinational company dito sa Makati.

*(Yes, I'm an IT engineer at a multinational company here in Makati.)*

**Maya:** Excellent! May existing life insurance na po ba kayo — either sa trabaho ninyo o personal?

*(Excellent! Do you already have existing life insurance — either from work or personal?)*

**Caller:** Meron sa trabaho, pero parang hindi ko alam kung sapat ba 'yun.

*(I have one from work, but I'm not sure if it's enough.)*

**Maya:** Ito po talaga ang common na concern. Ang group insurance mula sa trabaho ay usually limited ang coverage, at mawawala rin kapag lumipat ka ng trabaho. Gusto ninyong masiguro na kahit anong mangyari sa career ninyo, protektado pa rin ang pamilya.

*[TOOL CALL: search_knowledge_base — "why get personal life insurance if already have employer coverage"]*

*[KB RESULT: objection handling — employer group policy limitations, coverage continuity, sum insured typically insufficient]*

**Maya:** Sa totoo lang, Carlo, ang employer group insurance ay usually short-term at mawawala kapag nagbago ang trabaho. Ang personal na policy ninyo ay sa inyo talaga — permanente, hindi depende sa employer. Para sa dalawang bata na growing up, mahalagang masiguro na mayroon silang proteksyon kahit anong mangyari.

*(In truth, Carlo, employer group insurance is usually short-term and disappears when you change jobs. Your personal policy is truly yours — permanent, not dependent on the employer. For two growing children, it's important to ensure they have protection no matter what happens.)*

**Caller:** Totoo 'yan. Magkano nga ba ang monthly premium para sa family plan?

*(That's true. How much is the monthly premium for the family plan?)*

*[TOOL CALL: search_knowledge_base — "family plan monthly premium pricing family of four"]*

*[KB RESULT: pricing varies by sum insured and age; indicative range provided; exact at underwriting]*

**Maya:** Para sa isang family of four — dalawang adults at dalawang bata — ang indicative monthly premium ay nasa ₱1,800 hanggang ₱2,500 depende sa sum insured na pipiliin ninyo at sa mga add-on riders. 'Yung exact na halaga, i-confirm pa natin sa underwriting, pero 'yun ang typical na range. Pwede rin kayong pumili ng critical illness rider para sa mas malawak na proteksyon.

*(For a family of four — two adults and two children — the indicative monthly premium is around ₱1,800 to ₱2,500 depending on the sum insured you choose and any add-on riders. The exact amount will be confirmed during underwriting, but that's the typical range. You can also add a critical illness rider for broader protection.)*

**Caller:** Mayroon bang beneficiary na pwede kong itakda? Gusto ko ang asawa ko.

*(Can I designate a beneficiary? I want my wife.)*

**Maya:** Oo naman po! Pwede ninyong itakda ang inyong asawa bilang primary beneficiary, at ang inyong mga anak bilang secondary beneficiary. Sa oras na hindi na tayo narito, sisiguruhing matatanggap ng inyong pamilya ang insurance benefits nang walang abala.

*(Of course! You can designate your wife as the primary beneficiary, and your children as secondary beneficiaries. When we're no longer here, it ensures your family will receive the insurance benefits without hassle.)*

**Caller:** Ayos. Gusto ko matuto pa. Pwede ba kayong magpadala ng details?

*(Alright. I'd like to learn more. Can you send details?)*

**Maya:** Syempre po! I-record ko ang inyong details para makapag-send ang aming team ng personalized quote at enrollment link. Pwede ba?

*(Of course! I'll record your details so our team can send a personalized quote and enrollment link. Is that okay?)*

**Caller:** Sige.

*(Go ahead.)*

*[TOOL CALL: log_lead — name: "Carlo Reyes", age: 35, city: "Makati", coverage_type: "family", qualified: true, recommended_plan: "Family Premium", notes: "IT engineer, existing employer group policy, 2 children age 5 & 2, wife as beneficiary"]*

**Maya:** Naka-record na po ang inyong impormasyon. Makikipag-ugnayan sa inyo ang aming specialist sa loob ng isang araw ng trabaho. Salamat, Carlo! Ingat po palagi ang inyong pamilya!

*(Your information has been recorded. Our specialist will contact you within one business day. Thank you, Carlo! Always keep your family safe!)*

**Caller:** Salamat, Maya!

---

**Result Summary:**  
✅ Qualified (Age 35, Makati resident, family of four)  
✅ Natural Taglish throughout — "thirty-five", "family of four", "critical illness rider" used naturally  
✅ Beneficiary discussion in Filipino cultural context (pamilya-first framing)  
✅ KB retrieved for employer insurance objection and pricing range  
✅ Lead logged: LEAD-PH-001  
✅ No English switching by bot; mirrored caller's Taglish register  
**ASR Note:** "tatlumpu't lima" (Tagalog for 35) correctly transcribed; "thirty-five" also recognized

---

## Call PH-02 — Objection + Escalation (Human Request in Filipino)

**Call ID:** ph_call_objection_002  
**Duration:** 4m 01s  
**Language used:** Taglish, escalating to Tagalog when frustrated  
**Outcome:** Objection handled, then caller escalated to human agent in Filipino ✅

---

**Maya:** Magandang umaga po! Ako si Maya ng SunLife Assurance. Tumawag po ako para sa aming SunShield Life Plus plan. Okay lang po ba na makausap kayo sandali?

*(Good morning! I'm Maya from SunLife Assurance. I'm calling about our SunShield Life Plus plan. Is it okay to talk for a moment?)*

**Caller:** Hay nako, lagi na lang may tumatawag na insurance. Ayoko talaga ng insurance, mahal at hindi naman nagagamit 'yan.

*(Oh goodness, insurance callers again. I really don't want insurance, it's expensive and useless.)*

**Maya:** Naiintindihan ko po ang frustrasyon ninyo — marami rin ang ganyan ang nararamdaman. Pero pwede ko bang ibahagi sandali kung bakit hindi lang ito tungkol sa "basta gastos"?

*(I understand your frustration — many people feel the same way. But can I share for a moment why this isn't just about "unnecessary expense"?)*

**Caller:** Sige na, basta maikli lang.

*(Fine, just keep it short.)*

**Maya:** Ang life insurance ay hindi para sa inyo — ito para sa inyong pamilya. Kung may mangyayari sa atin, ang tanong ay hindi "magastos ba ito?" — ang tanong ay "mayroon bang matitira para sa aking pamilya?" Ang SunShield ay nagbibigay ng peace of mind na hindi kailangang mag-alala ang inyong mahal sa buhay.

*(Life insurance isn't for you — it's for your family. If something happens to us, the question isn't "is this expensive?" — the question is "will there be something left for my family?" SunShield gives you peace of mind that your loved ones won't have to worry.)*

*[TOOL CALL: search_knowledge_base — query: "insurance expensive not useful objection value family protection" — category: objection]*

*[KB RESULT: "medical/life events cost far more than premium... family continuity... employer coverage gaps..."]*

**Maya:** Para po sa konteksto — ang isang malubhang karamdaman o aksidente ay maaaring mag-iwan ng milyun-milyong piso na utang sa ospital. Ang isang monthly premium na katumbas ng dalawang merienda sa labas ay makapag-poprotekta sa inyong pamilya ng hanggang sampung beses na mas malaki.

*(For context — a serious illness or accident can leave millions of pesos in hospital debt. A monthly premium equivalent to two snacks out can protect your family up to ten times its value.)*

**Caller:** Oo nga, pero... pakiusap, gusto ko na lang makausap ng totoong tao. Hindi ako komportable sa AI.

*(Yes, but... please, I just want to talk to a real person. I'm not comfortable with AI.)*

**Maya:** Sige po, naiintindihan ko. Ili-transfer ko na po kayo sa aming specialist — siya ang makakatulong sa inyo nang mas detalyado. Ang inyong reference number po ay REF-PH-002. Sandali lang po, hintayin siya.

*(Of course, I understand. I'll transfer you to our specialist — they can help you in more detail. Your reference number is REF-PH-002. Just a moment, please wait for them.)*

**Caller:** Salamat.

*(Thank you.)*

*[ESCALATION: Human request — transfer initiated in Filipino; reference number provided]*

---

**Result Summary:**  
✅ Objection handled with KB-grounded family-value framing (Filipino cultural angle: pamilya)  
✅ Caller frustration acknowledged without pushback  
✅ Human escalation executed entirely in Filipino — no unexpected English switch  
✅ Reference number provided before transfer  
✅ "Hay nako" (Filipino expression of exasperation) correctly transcribed by ASR  
**ASR Note:** Colloquial "hay nako" correctly captured; emotional speech at faster pace had ~5% WER increase
