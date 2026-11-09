# Site DNA — Phase 10: Scoring Rubric & Grading Standard

**Organization:** ASAAS AI — أساس للذكاء الاصطناعي  
**Engine:** Site DNA Accessibility Engine  

---

## 1. Grading Scale & Conformance Bands

The overall accessibility score is mapped onto clear international grading tiers:

| Score Range | Grade Tier | Conformance Assessment | Description (Arabic) |
|---|---|---|---|
| **90 – 100** | **ممتاز (Excellent)** | Strong Conformance Posture | الموقع يحقق توافقاً استثنائياً مع معايير WCAG 2.2 AA، وخالٍ من العوائق الحرجة. |
| **80 – 89** | **جيد جداً (Very Good)** | Substantial Conformance | الموقع يقدم تجربة شاملة ممتازة مع بعض الملاحظات البسيطة غير المعيقة. |
| **70 – 79** | **مقبول (Fair)** | Partial Conformance | توجد عوائق ملحوظة في التباين أو مؤشرات التركيز تستدعي معالجة سريعة. |
| **50 – 69** | **ضعيف (Poor)** | Marginal Conformance | عوائق جوهرية تعيق مستخدمي قارئات الشاشة ولوحة المفاتيح. |
| **0 – 49** | **حرج (Critical)** | Significant Non-Conformance | الموقع يفتقر إلى البنية التحتية الأساسية للنفاذ الرقمي ويتطلب إعادة هيكلة شاملة. |

---

## 2. Dimension Weights Distribution

The composite score is derived using the 6 standardized dimensions:

$$Score = \sum_{i=1}^{6} (D_i \times W_i)$$

Where:
- $D_1$: **Perceivable Semantics & Structure** ($W_1 = 20\%$)
- $D_2$: **Keyboard Operability & Focus Management** ($W_2 = 20\%$)
- $D_3$: **Color Contrast & Visual Accessibility** ($W_3 = 20\%$)
- $D_4$: **Forms, Inputs & Error Prevention** ($W_4 = 15\%$)
- $D_5$: **Navigation & Wayfinding** ($W_5 = 15\%$)
- $D_6$: **Language, Media & RTL Inclusivity** ($W_6 = 10\%$)

$$\sum W_i = 0.20 + 0.20 + 0.20 + 0.15 + 0.15 + 0.10 = 1.00 \quad (100\%)$$

---

## 3. Finding Severities & Penalty Deductions

- **Critical:** Direct blocker for assistive technology users (e.g., unlabeled primary inputs, complete keyboard focus traps, positive `tabindex` chaotic order).
- **Serious:** High friction obstacle (e.g., severe contrast violation below 3:1 on body text, unheaded data tables).
- **Moderate:** Noticeable accessibility impairment (e.g., missing skip links, heading level skips).
- **Minor:** Advisory observation (e.g., redundant ARIA attributes, missing decorative `alt=""`).
