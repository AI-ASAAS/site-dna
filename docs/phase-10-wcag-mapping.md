# Site DNA — Phase 10: WCAG 2.2 Success Criteria Mapping Table

**Organization:** ASAAS AI — أساس للذكاء الاصطناعي  
**Engine:** Site DNA Accessibility Intelligence Engine  
**Guideline Baseline:** W3C WCAG 2.2 (Levels A and AA)  

---

| Criterion ID | Criterion Name | Name (Arabic) | Level | Test Method | Primary Engine Trigger / Heuristic |
|---|---|---|---|---|---|
| **1.1.1** | Non-text Content | المحتوى غير النصي | A | Automated | `missing_alt_count > 0` or functional icon buttons without names |
| **1.3.1** | Info and Relationships | المعلومات والعلاقات الدلالية | A | Semi-Automated | Missing `<main>`, unheaded `<table>`, or unlabeled inputs |
| **1.3.2** | Meaningful Sequence | التسلسل ذو المعنى | A | Automated | DOM flow predictability against `tabindex > 0` |
| **1.4.3** | Contrast (Minimum) | التباين البصري الأدنى | AA | Automated | Luminance ratio < 4.5:1 (normal text) or < 3.0:1 (large text) |
| **1.4.4** | Resize Text | تكبير حجم النصوص (200%) | AA | Automated | Viewport `user-scalable=no` or `maximum-scale < 2.0` |
| **1.4.10** | Reflow | إعادة التدفق والتجاوب (320px) | AA | Semi-Automated | Horizontal overflow / scrolling triggered at 320px width |
| **1.4.11** | Non-text Contrast | تباين العناصر غير النصية | AA | Semi-Automated | Focus rings & UI control borders vs adjacent background (< 3:1) |
| **2.1.1** | Keyboard | الوصول عبر لوحة المفاتيح | A | Semi-Automated | Non-semantic clickable elements (`<div onclick>`) without key listeners |
| **2.1.2** | No Keyboard Trap | منع فخاخ لوحة المفاتيح | A | Manual Required | Tab focus trapping within dynamic interactive widgets/modals |
| **2.4.1** | Bypass Blocks | تجاوز الكتل والتنقل السريع | A | Automated | Presence of functional skip navigation links (`href="#main"`) |
| **2.4.2** | Page Titled | عناوين الصفحات الإيضاحية | A | Automated | Presence of non-empty descriptive `<title>` tag |
| **2.4.3** | Focus Order | ترتيب التركيز المتسلسل | A | Automated | Absence of positive `tabindex` causing arbitrary jump sequences |
| **2.4.4** | Link Purpose (In Context) | وضوح غرض الرابط في سياقه | A | Automated | Vague anchor copy ("click here", "اضغط هنا", "اقرأ المزيد") |
| **2.4.6** | Headings and Labels | وضوح العناوين والتسميات | AA | Semi-Automated | Heading level skipping (`h1` directly to `h3`), missing primary `h1` |
| **2.4.7** | Focus Visible | وضوح مؤشر التركيز | AA | Automated | Global CSS `outline: none` without active focus styling replacement |
| **2.4.11** | Focus Not Obscured (Min) | عدم حجب مؤشر التركيز | AA | Semi-Automated | Sticky/fixed navigation obscuring active focused controls (WCAG 2.2) |
| **2.5.8** | Target Size (Minimum) | الحجم الأدنى للأهداف (24px) | AA | Automated | Interactive elements < 24×24 CSS px without spacing exemption (WCAG 2.2) |
| **3.1.1** | Language of Page | لغة الصفحة | A | Automated | Document `<html lang="...">` declaration present and valid |
| **3.1.2** | Language of Parts | لغة الأجزاء والمحتوى المتعدد | AA | Semi-Automated | Mixed Arabic/English spans isolated with appropriate language tags |
| **3.2.1** | On Focus | استقرار السياق عند التركيز | A | Manual Required | Shift of context or unexpected submission upon focus event |
| **3.3.2** | Labels or Instructions | تسميات الحقول والإرشادات | A | Automated | Form input fields missing explicit programmatic labels |
| **3.3.8** | Accessible Authentication | المصادقة الميسرة | AA | Semi-Automated | Password managers / copy-paste support without cognitive puzzles (WCAG 2.2) |
| **4.1.2** | Name, Role, Value | الاسم، الدور، والقيمة (ARIA) | A | Automated | ARIA role validity, intact ID references, and valid `aria-hidden` |
